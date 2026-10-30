"""Recall of our pipeline against the curated reference list (ADR 0007).

    python -m pipeline.cli reference-recall

Which open 2027 listings in the curated list do our processed postings contain?

1. **The reference set** is the open rows of the 2027 README whose Apply link
   is on Greenhouse, Lever or Ashby and whose employer is in
   config/employers.yaml: matched by (platform, board token), or by employer
   name when a Greenhouse link (gh_jid) hides the token.
2. **Matching** is by job id parsed from the link (the same key the pipeline
   uses), falling back to a normalized URL.
3. **Recall** is found / reference set, with a 95% Wilson interval.
4. **Each miss gets a likely reason.** Our raw snapshots keep only postings
   that pass the loose Canada filter, so a miss is checked against the live
   board once (with --offline it is not): gone from the board, on the board but
   outside the Canada filter, or on the board but not in our snapshots (posted
   after our latest snapshot, or its employer was added after it). A match
   that we hold but do not count as an open Canadian student posting gets the
   reason our extractors gave.

The curator's parenthetical terms are compared with our term extractor as a
cross-check report only (agree, disagree, we said "not stated"). They are the
curator's annotation, not text from the posting, so they are never gold labels
and never go into data/labels/.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit

from pipeline.evaluate import Ratio
from pipeline.geo import passes_loose_filter
from pipeline.models import Posting, Source, posting_id
from pipeline.reference_list import TOKEN_PLATFORMS, ReferenceRow, classify_url
from pipeline.sources import PLATFORMS
from pipeline.sources.http import FetchError, PoliteClient
from pipeline.text import html_to_text

FOUND = "found"
REASONS = {
    "closed": "in our data, but marked closed",
    "not_canadian": "in our data, but its location was not read as Canadian",
    "not_student": "in our data, but missed by role detection",
    "gone": "no longer on the board (closed before or after our snapshots)",
    "filtered": "on the board, but filtered out as non-Canadian at fetch",
    "new_employer": "on the board; its employer was added after our latest snapshot",
    "not_in_snapshot": "on the board, but not in our snapshots (posted after the latest one)",
    "board_failed": "board fetch failed during this check",
    "not_checked": "not in our data (live board not checked: --offline)",
}


TRACKING_PARAMS = {"gh_src", "lever-source", "lever-origin", "source", "src", "ref", "embed", "utm_source"}
APPLY_SUFFIXES = ("/apply", "/application")


def normalize_url(url: str) -> str:
    """Host, path and meaningful query of a job link, so the same job compares equal.

    The scheme, "www.", a trailing slash, an "/apply" or "/application" page and
    tracking parameters are dropped. Other query parameters are kept, because
    some careers pages carry the job id there ("?gh_jid=123").
    """
    parts = urlsplit(url.strip())
    path = parts.path.rstrip("/").lower()
    for suffix in APPLY_SUFFIXES:
        path = path.removesuffix(suffix)
    query = sorted(
        (k.lower(), v)
        for k, v in parse_qsl(parts.query)
        if k.lower() not in TRACKING_PARAMS and not k.lower().startswith("utm_")
    )
    return f"{parts.netloc.lower().removeprefix('www.')}{path}" + (f"?{urlencode(query)}" if query else "")


@dataclass
class Candidate:
    row: ReferenceRow
    source: Source
    board_token: str
    employer_id: str
    job_id: str | None


@dataclass
class Outcome:
    candidate: Candidate
    reason: str  # FOUND or a key of REASONS
    posting: Posting | None = None


@dataclass
class TermCheck:
    agree: int = 0
    disagree: int = 0
    we_not_stated: int = 0
    we_ambiguous: int = 0
    examples: list[tuple[str, str]] = field(default_factory=list)  # (curator term, our terms) on disagreement


def reference_set(rows: list[ReferenceRow], employers: list[dict[str, Any]]) -> list[Candidate]:
    """Open 2027 rows on Greenhouse, Lever or Ashby whose employer we track."""
    by_board = {(e["board_type"], str(e["board_token"]).lower()): e for e in employers}
    by_name: dict[tuple[str, str], dict[str, Any]] = {}
    for e in employers:
        by_name.setdefault((e["board_type"], e["name"].casefold()), e)
    out = []
    for r in rows:
        if r.season != 2027 or r.closed:
            continue
        p = classify_url(r.apply_url)
        if p.platform not in TOKEN_PLATFORMS:
            continue
        employer = by_board.get((p.platform, p.token or "")) or by_name.get((p.platform, r.company.casefold()))
        if employer is None:
            continue
        out.append(Candidate(r, Source(p.platform), str(employer["board_token"]), employer["id"], p.job_id))
    return out


def match(candidates: list[Candidate], postings: list[Posting]) -> list[Outcome]:
    by_id = {p.id: p for p in postings}
    by_url = {normalize_url(p.url): p for p in postings if p.url}
    outcomes = []
    for c in candidates:
        found = by_id.get(posting_id(c.source, c.board_token, c.job_id)) if c.job_id else None
        found = found or by_url.get(normalize_url(c.row.apply_url or ""))
        if found is None:
            outcomes.append(Outcome(c, "not_checked"))
        elif found.status != "open":
            outcomes.append(Outcome(c, "closed", found))
        elif not found.in_canada:
            outcomes.append(Outcome(c, "not_canadian", found))
        elif not found.is_student_role:
            outcomes.append(Outcome(c, "not_student", found))
        else:
            outcomes.append(Outcome(c, FOUND, found))
    return outcomes


def explain_misses(outcomes: list[Outcome], client: PoliteClient, boards_in_snapshots: set[tuple[Source, str]]) -> None:
    """Fill in the reason for misses we do not hold at all, from one live fetch per board."""
    boards: dict[tuple[Source, str], dict[str, Any] | None] = {}
    for o in outcomes:
        if o.reason != "not_checked":
            continue
        c = o.candidate
        key = (c.source, c.board_token)
        if key not in boards:
            board_url, parse = PLATFORMS[c.source]
            try:
                jobs = parse(client.get_json(board_url(c.board_token)), c.employer_id, c.board_token)
                boards[key] = {j.source_job_id: j for j in jobs} | {normalize_url(j.url): j for j in jobs}
            except (FetchError, ValueError, KeyError, TypeError):
                boards[key] = None
        jobs_by_key = boards[key]
        if jobs_by_key is None:
            o.reason = "board_failed"
            continue
        job = jobs_by_key.get(c.job_id or "") or jobs_by_key.get(normalize_url(c.row.apply_url or ""))
        if job is None:
            o.reason = "gone"
        elif not passes_loose_filter(job.location_raw, job.title, html_to_text(job.description_html)):
            o.reason = "filtered"
        elif (c.source, c.board_token) not in boards_in_snapshots:
            o.reason = "new_employer"
        else:
            o.reason = "not_in_snapshot"


def recall(outcomes: list[Outcome]) -> Ratio:
    return Ratio(sum(o.reason == FOUND for o in outcomes), len(outcomes))


def term_cross_check(outcomes: list[Outcome]) -> TermCheck:
    """Curator's parenthetical term vs our extractor, on matched postings that have one."""
    check = TermCheck()
    for o in outcomes:
        if o.posting is None or not o.candidate.row.term:
            continue
        curator, ours = o.candidate.row.term, o.posting.terms
        if curator in ours:
            check.agree += 1
        elif not ours and o.posting.term_status == "ambiguous":
            check.we_ambiguous += 1
        elif not ours:
            check.we_not_stated += 1
        else:
            check.disagree += 1
            check.examples.append((curator, ", ".join(ours)))
    return check


def on_snapshot_boards(outcomes: list[Outcome], boards_in_snapshots: set[tuple[Source, str]]) -> list[Outcome]:
    """Only the listings whose board our latest snapshot fetched: the pipeline's own recall,
    without employers that were added to the config after that snapshot."""
    return [o for o in outcomes if (o.candidate.source, o.candidate.board_token) in boards_in_snapshots]


def report(outcomes: list[Outcome], check: TermCheck, boards_in_snapshots: set[tuple[Source, str]]) -> str:
    lines = [
        "Pipeline recall against the curated reference list (open 2027 rows, tracked employers,",
        "Greenhouse/Lever/Ashby links):",
        "",
        f"  Recall, boards in our latest snapshot: {recall(on_snapshot_boards(outcomes, boards_in_snapshots))}",
        f"  Recall, every tracked employer:        {recall(outcomes)}",
        "",
        "Misses by likely reason:",
    ]
    reasons = Counter(o.reason for o in outcomes if o.reason != FOUND)
    for key, n in reasons.most_common():
        lines.append(f"  {n:4d}  {REASONS[key]}")
    lines += ["", "Misses (local report only; the listings are not committed, ADR 0007):"]
    for o in sorted(outcomes, key=lambda o: (o.reason, o.candidate.employer_id)):
        if o.reason != FOUND:
            r = o.candidate.row
            lines.append(f"  [{o.reason}] {r.company}: {r.role} ({r.location}) {r.apply_url}")
    total = check.agree + check.disagree + check.we_not_stated + check.we_ambiguous
    lines += [
        "",
        "Term cross-check on matched postings with a curator term (not gold labels):",
        f"  {total} compared: agree {check.agree}, disagree {check.disagree}, "
        f"we said not stated {check.we_not_stated}, we said ambiguous {check.we_ambiguous}",
    ]
    for curator, ours in check.examples:
        lines.append(f"    curator {curator!r} vs ours {ours!r}")
    return "\n".join(lines) + "\n"
