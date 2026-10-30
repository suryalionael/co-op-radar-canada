"""Work-term extractor: which term a posting is for, and its dates when stated.

Finds, in the title first and then the description:

- a season and year: "Summer 2027", "Fall term 2026", "Winter '27", "2027 Summer",
  "été 2027"
- a month range: "May–August 2027", "January to April 2027",
  "September 2026 - April 2027"
- a start month: "May 2027 start", "starting January 2027", "start date: May 2027"
- a month and year on their own: "May 2027 GIS Co-op", "(Winter/January 2027)",
  "Jan 2027". In the title this always counts. In the description it counts only
  when the same sentence names the work term (co-op, internship, term, start...)
  and no deadline word comes right before it ("apply by May 2027" is not a term).

Canadian co-op terms follow the school calendar: Winter is January to April,
Summer is May to August, Fall is September to December. A month range or start
month is named after the term its first month falls in.

"Spring" means different months at different schools (May to August at some,
a shorter April to June term at others), so "Spring 2027" is never mapped to a
term. It is reported as `ambiguous` with its evidence kept.

Nothing is guessed: a posting that says "summer co-op" with no year gets no term.
A term that ended before the posting was published ("Winter 2026" on a role
posted in October 2026) is kept exactly as stated; `term_in_past` flags it.
"""

from __future__ import annotations

import calendar
import datetime as dt
import re
from dataclasses import dataclass, field

SEASONS = {
    "winter": "Winter",
    "hiver": "Winter",
    "spring": "Spring",
    "printemps": "Spring",
    "summer": "Summer",
    "été": "Summer",
    "ete": "Summer",
    "fall": "Fall",
    "autumn": "Fall",
    "automne": "Fall",
}
MONTHS = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
MONTHS |= {name.lower(): i for i, name in enumerate(calendar.month_abbr) if name}
MONTHS |= {"sept": 9}
MONTHS |= {
    "janvier": 1,
    "février": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
}

AMBIGUOUS_SEASONS = {"Spring"}
TERM_STATUS_STATED, TERM_STATUS_AMBIGUOUS, TERM_STATUS_NOT_STATED = "stated", "ambiguous", "not_stated"

_SEASON = r"(?P<season>" + "|".join(SEASONS) + r")"
_SEASON2 = r"(?P<season2>" + "|".join(SEASONS) + r")"
_MONTH = "|".join(sorted(MONTHS, key=len, reverse=True))
_YEAR = r"(?:20\d\d)"

SEASON_YEAR = re.compile(
    rf"\b{_SEASON}\s*(?:term|session|semester|co-?op|internship)?\s*(?:of\s+)?[,'’-]?\s*"
    rf"(?P<year>{_YEAR}|['’]\d\d)\b"
    rf"|\b(?P<year2>{_YEAR})\s+{_SEASON2}\b",
    re.IGNORECASE,
)
MONTH_RANGE = re.compile(
    rf"\b(?P<m1>{_MONTH})\.?\s*(?P<y1>{_YEAR})?\s*(?:-|–|—|to|through|until|à|au)\s*"
    rf"(?P<m2>{_MONTH})\.?\s*,?\s*(?P<y2>{_YEAR})\b",
    re.IGNORECASE,
)
START_MONTH = re.compile(
    rf"\b(?:start(?:ing)?(?:\s+(?:date|in|on))?\s*:?\s*(?:early\s+|mid-?\s*|late\s+)?)"
    rf"(?P<m1>{_MONTH})\.?\s*,?\s*(?P<y1>{_YEAR})\b"
    rf"|\b(?P<m2>{_MONTH})\.?\s*,?\s*(?P<y2>{_YEAR})\s+start\b",
    re.IGNORECASE,
)

MONTH_YEAR = re.compile(rf"\b(?P<m1>{_MONTH})\.?\s*,?\s*(?P<y1>{_YEAR})\b", re.IGNORECASE)
WORK_TERM_WORDS = re.compile(
    r"\b(?:co-?op|co op|intern(?:ship)?s?|stages?|stagiaires?|terms?|work terms?|placements?|start(?:s|ing)?|"
    r"begin(?:s|ning)?|commenc\w*|from|duration|session|semester|cohort)\b",
    re.IGNORECASE,
)
DEADLINE_BEFORE = re.compile(
    r"(?:apply|applications?|submit\w*|deadline|closes?|closing|due|posted|before|until|by|graduat\w*|"
    r"expected to graduate|class of)\W*(?:\w+\W+){0,2}$",
    re.IGNORECASE,
)
SENTENCE_END = re.compile(r"[.!?;\n•]")


def season_for_month(month: int) -> str:
    if month <= 4:
        return "Winter"
    if month <= 8:
        return "Summer"
    return "Fall"


def _year(text: str) -> int:
    text = text.lstrip("'’")
    return int(text) if len(text) == 4 else 2000 + int(text)


@dataclass
class TermResult:
    terms: list[str] = field(default_factory=list)  # every distinct term, in order found
    start: dt.date | None = None
    end: dt.date | None = None
    evidence: str | None = None  # text of the first match
    dates_evidence: str | None = None  # text the dates came from
    ambiguous: list[str] = field(default_factory=list)  # e.g. "Spring 2027": kept as evidence, never mapped

    @property
    def term(self) -> str | None:
        return self.terms[0] if self.terms else None

    @property
    def status(self) -> str:
        if self.terms:
            return TERM_STATUS_STATED
        return TERM_STATUS_AMBIGUOUS if self.ambiguous else TERM_STATUS_NOT_STATED


def _sentence_before(text: str, at: int) -> str:
    before = text[max(0, at - 120) : at]
    cuts = list(SENTENCE_END.finditer(before))
    return before[cuts[-1].end() :] if cuts else before


def _sentence_after(text: str, at: int) -> str:
    after = text[at : at + 120]
    cut = SENTENCE_END.search(after)
    return after[: cut.start()] if cut else after


def _plain_month_counts(text: str, m: re.Match[str], in_title: bool) -> bool:
    """A month and year with no "start" or range around it: always in a title; in a
    description only beside work-term words and not right after a deadline word."""
    if in_title:
        return True
    before, after = _sentence_before(text, m.start()), _sentence_after(text, m.end())
    if DEADLINE_BEFORE.search(before):
        return False
    return bool(WORK_TERM_WORDS.search(before) or WORK_TERM_WORDS.search(after))


def _scan(text: str, result: TermResult, in_title: bool = False) -> None:
    hits: list[tuple[int, str, str]] = []  # (position, term, matched text)

    for m in MONTH_RANGE.finditer(text):
        m1, m2 = MONTHS[m["m1"].lower()], MONTHS[m["m2"].lower()]
        y2 = int(m["y2"])
        y1 = int(m["y1"]) if m["y1"] else (y2 - 1 if m1 > m2 else y2)
        term = f"{season_for_month(m1)} {y1}"
        hits.append((m.start(), term, m.group(0)))
        if result.start is None:
            result.start = dt.date(y1, m1, 1)
            result.end = dt.date(y2, m2, calendar.monthrange(y2, m2)[1])
            result.dates_evidence = m.group(0)

    taken = [(m.start(), m.end()) for m in MONTH_RANGE.finditer(text)]

    for m in START_MONTH.finditer(text):
        if any(a <= m.start() < b for a, b in taken):
            continue
        taken.append((m.start(), m.end()))
        month = MONTHS[(m["m1"] or m["m2"]).lower()]
        year = int(m["y1"] or m["y2"])
        hits.append((m.start(), f"{season_for_month(month)} {year}", m.group(0)))
        if result.start is None:
            result.start = dt.date(year, month, 1)
            result.dates_evidence = m.group(0)

    for m in MONTH_YEAR.finditer(text):
        if any(a <= m.start() < b for a, b in taken) or not _plain_month_counts(text, m, in_title):
            continue
        month, year = MONTHS[m["m1"].lower()], int(m["y1"])
        hits.append((m.start(), f"{season_for_month(month)} {year}", m.group(0)))
        if result.start is None:
            result.start = dt.date(year, month, 1)
            result.dates_evidence = m.group(0)

    for m in SEASON_YEAR.finditer(text):
        season = SEASONS[(m["season"] or m["season2"]).lower()]
        if season in AMBIGUOUS_SEASONS:
            if m.group(0) not in result.ambiguous:
                result.ambiguous.append(m.group(0))
            continue
        hits.append((m.start(), f"{season} {_year(m['year'] or m['year2'])}", m.group(0)))

    for _, term, matched in sorted(hits):
        if term not in result.terms:
            result.terms.append(term)
            if result.evidence is None:
                result.evidence = matched


def extract_term(title: str, description: str) -> TermResult:
    """Terms from the title come first; the description adds any others."""
    result = TermResult()
    _scan(title, result, in_title=True)
    _scan(description, result)
    return result


TERM_END_MONTH = {"Winter": 4, "Summer": 8, "Fall": 12}


def term_end_date(term: str) -> dt.date | None:
    """Last day of a named term on the school calendar: "Winter 2026" ends 2026-04-30."""
    season, _, year = term.partition(" ")
    month = TERM_END_MONTH.get(season)
    if month is None or not year.isdigit():
        return None
    return dt.date(int(year), month, calendar.monthrange(int(year), month)[1])


def term_in_past(terms: list[str], term_end: dt.date | None, posted: dt.date | None) -> bool:
    """True when every stated term had ended before the posting date. The term itself is never changed."""
    if posted is None or not terms:
        return False
    ends = [term_end_date(t) for t in terms]
    if term_end is not None:
        ends[0] = max(term_end, ends[0]) if ends[0] else term_end
    return all(end is not None and end < posted for end in ends)
