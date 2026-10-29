"""Program watch: fingerprint student-program pages and record the day each one changes.

For each page in config/programs.yaml:

1. Fetch it and keep only the main text: drop scripts, styles, navigation,
   headers, footers, forms, and anything whose id or class looks like a cookie
   or consent banner, a carousel, or an alert bar.
2. Normalize away content that changes without the program changing: dates,
   times, "last updated" lines, copyright years, and long numbers (view counts,
   cache busters).
3. Hash what is left. A new hash on a successful fetch is a change; a failed
   fetch is never a change.

The raw main text is stored on the `data` branch so changes can be shown as a
short excerpt of the lines that were added.
"""

from __future__ import annotations

import datetime as dt
import difflib
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from pipeline.models import ChangeKind, ProgramChange, ProgramWatch
from pipeline.sources.http import FetchError, PoliteClient
from pipeline.text import content_hash

SKIP_TAGS = {
    "script", "style", "noscript", "template", "svg", "iframe", "nav", "header", "footer", "form", "aside",
    "button", "select", "dialog",
}  # fmt: skip
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
BLOCK_TAGS = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "section", "article", "main", "br", "td"}
NOISY_ATTR = re.compile(
    r"cookie|consent|gdpr|onetrust|banner|carousel|slider|alert-bar|breadcrumb|skip-link|"
    r"share|social|newsletter|modal|popup|feedback|date-modified|wb-dtmd",
    re.IGNORECASE,
)

MONTH = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sep(?:t(?:ember)?)?|"
    r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
)
VOLATILE = [
    re.compile(r"^\s*(?:last\s+|date\s+)?(?:updated|modified|reviewed)\b.*", re.IGNORECASE),
    re.compile(r"(?:©|&copy;|copyright)\s*\d{4}(?:\s*[-–]\s*\d{4})?", re.IGNORECASE),
    re.compile(r"\b\d{4}-\d{2}-\d{2}(?:[t ]\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:z|[+-]\d{2}:?\d{2})?)?\b", re.IGNORECASE),
    re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)?\b", re.IGNORECASE),
    re.compile(rf"\b{MONTH}\.?\s+\d{{1,2}},?\s+\d{{4}}\b", re.IGNORECASE),
    re.compile(r"\b\d{6,}\b"),
]


class _MainText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, bool]] = []  # (tag, skipped)
        self.parts: list[str] = []

    def _skipping(self) -> bool:
        return any(skipped for _, skipped in self.stack)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in VOID_TAGS:
            if tag == "br":
                self.parts.append("\n")
            return
        attr_text = " ".join(v or "" for k, v in attrs if k in ("id", "class", "role", "aria-label"))
        hidden = any(k == "hidden" or (k == "aria-hidden" and v == "true") for k, v in attrs)
        role_skip = any(k == "role" and v in ("navigation", "banner", "contentinfo", "dialog") for k, v in attrs)
        skip = tag in SKIP_TAGS or hidden or role_skip or bool(NOISY_ATTR.search(attr_text))
        self.stack.append((tag, skip))
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        # Pop back to the matching open tag; tolerate unclosed tags in messy HTML.
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skipping():
            self.parts.append(data)


def main_text(html: str) -> str:
    """Visible main text of a page, one block per line, with volatile content removed."""
    parser = _MainText()
    parser.feed(html)
    parser.close()
    lines = []
    for line in "".join(parser.parts).splitlines():
        for pattern in VOLATILE:
            line = pattern.sub(" ", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line and re.search(r"\w", line):
            lines.append(line)
    return "\n".join(lines)


def change_excerpt(old: str, new: str, limit: int = 300) -> str:
    """The lines added in `new`, joined and cut to `limit` characters."""
    added = [
        line[1:].strip()
        for line in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0)
        if line.startswith("+") and not line.startswith("+++")
    ]
    text = " … ".join(a for a in added if a) or "(text removed)"
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def load_programs(path: Path) -> list[dict[str, Any]]:
    """Programs to watch. Entries without a `verified` date are skipped until someone checks the URL."""
    with path.open(encoding="utf-8") as f:
        programs: list[dict[str, Any]] = yaml.safe_load(f).get("programs") or []
    return [p for p in programs if p.get("verified")]


def fetch_program(client: PoliteClient, program: dict[str, Any], now: dt.datetime) -> dict[str, Any]:
    """One raw program-watch record for the data branch. Never raises for page problems."""
    record: dict[str, Any] = {"program_id": program["id"], "url": program["url"], "fetched_at": now.isoformat()}
    if not client.allowed_by_robots(program["url"]):
        return record | {"ok": False, "error": "disallowed by robots.txt", "text": None, "hash": None}
    try:
        text = main_text(client.get(program["url"]).text)
    except FetchError as e:
        return record | {"ok": False, "error": str(e), "text": None, "hash": None}
    if not text:
        return record | {"ok": False, "error": "no main text found", "text": None, "hash": None}
    return record | {"ok": True, "error": None, "text": text, "hash": content_hash(text)}


def build_program_watch(
    programs: list[dict[str, Any]], days: list[tuple[dt.date, list[dict[str, Any]]]]
) -> tuple[list[ProgramWatch], list[ProgramChange]]:
    """Replay every day's records, oldest first, into current status and a change history."""
    state: dict[str, dict[str, Any]] = {
        p["id"]: {"hash": None, "text": None, "checked": None, "ok": False, "changed": None, "excerpt": None}
        for p in programs
    }
    changes: list[ProgramChange] = []
    for day, records in sorted(days, key=lambda d: d[0]):
        for r in records:
            s = state.get(r["program_id"])
            if s is None:  # program removed from the config
                continue
            s["checked"], s["ok"] = day, bool(r["ok"])
            if not r["ok"]:
                continue
            if s["hash"] is not None and r["hash"] != s["hash"]:
                excerpt = change_excerpt(s["text"] or "", r["text"])
                changes.append(
                    ProgramChange(
                        program_id=r["program_id"], changed_on=day, change_excerpt=excerpt,
                        kind=ChangeKind.content_change,
                    )
                )  # fmt: skip
                s["changed"], s["excerpt"] = day, excerpt
            s["hash"], s["text"] = r["hash"], r["text"]

    for p in programs:
        if p.get("note"):
            changes.append(
                ProgramChange(
                    program_id=p["id"], changed_on=p["note_date"], change_excerpt=p["note"], kind=ChangeKind.manual_note
                )
            )

    watch = [
        ProgramWatch(
            program_id=p["id"],
            employer_id=p["employer_id"],
            name=p["name"],
            url=p["url"],
            last_hash=state[p["id"]]["hash"],
            last_checked=state[p["id"]]["checked"],
            last_fetch_ok=state[p["id"]]["ok"],
            last_changed=state[p["id"]]["changed"],
            change_excerpt=state[p["id"]]["excerpt"],
            expected_open=p.get("expected_open"),
            expected_open_src=p.get("expected_open_src"),
        )
        for p in programs
    ]
    changes.sort(key=lambda c: (c.changed_on, c.program_id, c.kind))
    return watch, changes


def write_program_watch(watch: list[ProgramWatch], changes: list[ProgramChange], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    watch_schema = pa.schema(
        [
            ("program_id", pa.string()),
            ("employer_id", pa.string()),
            ("name", pa.string()),
            ("url", pa.string()),
            ("last_hash", pa.string()),
            ("last_checked", pa.date32()),
            ("last_fetch_ok", pa.bool_()),
            ("last_changed", pa.date32()),
            ("change_excerpt", pa.string()),
            ("expected_open", pa.date32()),
            ("expected_open_src", pa.string()),
        ]
    )
    change_schema = pa.schema(
        [
            ("program_id", pa.string()),
            ("changed_on", pa.date32()),
            ("change_excerpt", pa.string()),
            ("kind", pa.string()),
        ]
    )
    rows = [w.model_dump() for w in watch]
    pq.write_table(pa.Table.from_pylist(rows, schema=watch_schema), out_dir / "program_watch.parquet")
    change_rows = [c.model_dump() | {"kind": str(c.kind)} for c in changes]
    pq.write_table(pa.Table.from_pylist(change_rows, schema=change_schema), out_dir / "program_changes.parquet")
