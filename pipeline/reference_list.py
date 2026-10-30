"""Parse the curated Canadian Tech Internships list (negarprh/Canadian-Tech-Internships-2027).

The list has no license (ADR 0007), so it is read at run time for seeding and
evaluation only. Raw copies stay in the gitignored data/reference/raw/; only
aggregate counts and our own board-token lists are committed.

Each README holds one table with the columns Company, Role, Location, Apply,
Date Posted. The table is Markdown today; HTML tables are handled too in case
the curator switches format.

- A Company cell of "↳" means "same company as the row above".
- A closed role shows "Closed🔒" instead of an Apply link.
- The work term, when the curator knows it, is in parentheses after the role:
  "Data Engineer Intern (Summer 2027)". This is the curator's annotation, not
  text from the posting, so it is never used as a gold label.
- Dates are "Oct 27, 2026", or "Jan 14" with no year in older rows. A date
  without a year is kept as text and not parsed: the year is not guessed.

`classify_url` names the job-board platform behind an Apply link from its host
and URL patterns, and the board token where the URL shows one.
"""

from __future__ import annotations

import datetime as dt
import html
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

REPO = "negarprh/Canadian-Tech-Internships-2027"
FILES = {2027: "README.md", 2026: "README-2026.md"}
COLUMNS = ["company", "role", "location", "apply", "date posted"]
SAME_AS_ABOVE = "↳"

TERM_IN_PARENS = re.compile(
    r"\((?P<term>(?:winter|spring|summer|fall|autumn)(?:\s*(?:/|&|and|or|,)\s*(?:winter|spring|summer|fall|autumn))*"
    r"\s+20\d\d)\)",
    re.IGNORECASE,
)
URL = re.compile(r"https?://[^\s)\"'<>\]]+")
DATE_FORMATS = ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d")


def raw_url(season: int) -> str:
    return f"https://raw.githubusercontent.com/{REPO}/main/{FILES[season]}"


@dataclass(frozen=True)
class ReferenceRow:
    season: int  # which README the row came from: 2026 or 2027
    company: str
    role: str
    term: str | None  # the curator's parenthetical, e.g. "Summer 2027"
    location: str
    apply_url: str | None  # None when the role is closed
    closed: bool
    date_posted_raw: str
    date_posted: dt.date | None  # None when the cell has no year


# --- Table reading ----------------------------------------------------------------


def _split_markdown_row(line: str) -> list[str]:
    """Cells of a Markdown table row. "\\|" inside a cell is a literal pipe."""
    body = line.strip()
    body = body[1:] if body.startswith("|") else body
    body = body[:-1] if body.endswith("|") and not body.endswith("\\|") else body
    return [c.replace("\\|", "|").strip() for c in re.split(r"(?<!\\)\|", body)]


def _is_divider(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in cells if c) and any(cells)


def markdown_tables(text: str) -> list[list[list[str]]]:
    """Every Markdown table in the text, as rows of cells (header row included)."""
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            cells = _split_markdown_row(line)
            if not _is_divider(cells):
                current.append(cells)
        elif current:
            tables.append(current)
            current = []
    if current:
        tables.append(current)
    return tables


class _HTMLTables(HTMLParser):
    """Collects <table> rows as cell HTML, so links inside cells survive."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.tables: list[list[list[str]]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self.tables.append([])
        elif tag == "tr" and self.tables:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
        elif self._cell is not None:
            self._cell.append(self.get_starttag_text() or "")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._row is not None and self._cell is not None:
            self._row.append("".join(self._cell).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None:
            self.tables[-1].append(self._row)
            self._row = None
        elif self._cell is not None:
            self._cell.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_entityref(self, name: str) -> None:
        self.handle_data(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.handle_data(f"&#{name};")


def html_tables(text: str) -> list[list[list[str]]]:
    parser = _HTMLTables()
    parser.feed(text)
    return [t for t in parser.tables if t]


def _plain(cell: str) -> str:
    """Cell text without tags or Markdown link syntax."""
    cell = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", cell)
    cell = re.sub(r"<[^>]+>", "", cell)
    cell = re.sub(r"\*\*|__", "", cell)
    return " ".join(html.unescape(cell).split())


def _apply_url(cell: str) -> str | None:
    """The Apply link in a cell: the last URL that is not a badge image."""
    urls = [u for u in URL.findall(html.unescape(cell)) if "img.shields.io" not in u]
    return urls[-1] if urls else None


def _parse_date(text: str) -> dt.date | None:
    for fmt in DATE_FORMATS:
        try:
            return dt.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _listing_table(tables: list[list[list[str]]]) -> list[list[str]]:
    for table in tables:
        header = [_plain(c).lower() for c in table[0]]
        if header[: len(COLUMNS)] == COLUMNS:
            return table
    return []


def parse_readme(text: str, season: int) -> list[ReferenceRow]:
    """Every listing row in one README, with "↳" rows resolved to the company above."""
    table = _listing_table(markdown_tables(text)) or _listing_table(html_tables(text))
    rows: list[ReferenceRow] = []
    company = ""
    for cells in table[1:]:
        if len(cells) < len(COLUMNS):
            continue
        company_cell, role_cell, location_cell, apply_cell, date_cell = cells[: len(COLUMNS)]
        name = _plain(company_cell)
        if name and name != SAME_AS_ABOVE:
            company = name
        if not company:
            continue  # a "↳" with nothing above it: nothing to attach it to
        role = _plain(role_cell)
        term = TERM_IN_PARENS.search(role)
        closed = "closed" in _plain(apply_cell).lower() or "🔒" in apply_cell
        date_raw = _plain(date_cell)
        rows.append(
            ReferenceRow(
                season=season,
                company=company,
                role=role,
                term=" ".join(term["term"].split()) if term else None,
                location=_plain(location_cell),
                apply_url=None if closed else _apply_url(apply_cell),
                closed=closed,
                date_posted_raw=date_raw,
                date_posted=_parse_date(date_raw),
            )
        )
    return rows


# --- Platform classification ------------------------------------------------------

TOKEN_PLATFORMS = ("greenhouse", "lever", "ashby")


@dataclass(frozen=True)
class Platform:
    platform: str  # greenhouse, lever, ashby, workday, ..., other, none
    token: str | None  # board token when the URL shows it
    host: str
    job_id: str | None  # the platform's job id when the URL shows it


def _first_segment(path: str) -> str | None:
    parts = [p for p in path.split("/") if p]
    return parts[0].lower() if parts else None


def _segment_after(path: str, index: int) -> str | None:
    parts = [p for p in path.split("/") if p]
    return parts[index] if len(parts) > index else None


def classify_url(url: str | None) -> Platform:
    if not url:
        return Platform("none", None, "", None)
    parts = urlsplit(url)
    host = parts.netloc.lower().removeprefix("www.")
    path = parts.path
    query = {k.lower(): v for k, v in parse_qs(parts.query).items()}

    def param(name: str) -> str | None:
        return query[name][0] if query.get(name) else None

    if host in ("job-boards.greenhouse.io", "boards.greenhouse.io", "job-boards.eu.greenhouse.io"):
        token = _first_segment(path)
        if token == "embed":  # boards.greenhouse.io/embed/job_app?for=<token>&token=<job id>
            token, job = param("for"), param("token")
        else:
            job = _segment_after(path, 2) if _segment_after(path, 1) == "jobs" else None
        return Platform("greenhouse", token, host, job or param("gh_jid"))
    if "gh_jid" in query:  # Greenhouse behind the employer's own careers page: token unknown
        return Platform("greenhouse", None, host, param("gh_jid"))
    if host == "jobs.lever.co":
        return Platform("lever", _first_segment(path), host, _segment_after(path, 1))
    if host == "jobs.ashbyhq.com":
        return Platform("ashby", _first_segment(path), host, _segment_after(path, 1))
    if host.endswith("myworkdayjobs.com") or host.endswith("myworkdaysite.com"):
        return Platform("workday", None, host, None)
    if host.endswith("oraclecloud.com"):
        return Platform("oracle", None, host, None)
    if host.endswith("icims.com") or query.get("icims") == ["1"]:
        return Platform("icims", None, host, None)
    if host.endswith("eightfold.ai"):
        return Platform("eightfold", None, host, None)
    if [v.lower() for v in query.get("ats", [])] == ["successfactors"]:
        return Platform("successfactors", None, host, None)
    if host == "ats.rippling.com":
        return Platform("rippling", None, host, None)
    if host == "apply.workable.com":
        return Platform("workable", None, host, None)
    if host.endswith("bamboohr.com"):
        return Platform("bamboohr", None, host, None)
    if host.endswith("applytojob.com"):
        return Platform("jazzhr", None, host, None)
    if host.endswith("avature.net"):
        return Platform("avature", None, host, None)
    return Platform("other", None, host, None)
