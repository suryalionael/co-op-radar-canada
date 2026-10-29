"""Work-term extractor: which term a posting is for, and its dates when stated.

Finds, in the title first and then the description:

- a season and year: "Summer 2027", "Fall term 2026", "Winter '27", "2027 Summer",
  "été 2027"
- a month range: "May–August 2027", "January to April 2027",
  "September 2026 - April 2027"
- a start month: "May 2027 start", "starting January 2027", "start date: May 2027"

Canadian co-op terms follow the school calendar: Winter is January to April,
Summer is May to August, Fall is September to December. A month range or start
month is named after the term its first month falls in.

Nothing is guessed: a posting that says "summer co-op" with no year gets no term.
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

    @property
    def term(self) -> str | None:
        return self.terms[0] if self.terms else None


def _scan(text: str, result: TermResult) -> None:
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
        month = MONTHS[(m["m1"] or m["m2"]).lower()]
        year = int(m["y1"] or m["y2"])
        hits.append((m.start(), f"{season_for_month(month)} {year}", m.group(0)))
        if result.start is None:
            result.start = dt.date(year, month, 1)
            result.dates_evidence = m.group(0)

    for m in SEASON_YEAR.finditer(text):
        season = SEASONS[(m["season"] or m["season2"]).lower()]
        hits.append((m.start(), f"{season} {_year(m['year'] or m['year2'])}", m.group(0)))

    for _, term, matched in sorted(hits):
        if term not in result.terms:
            result.terms.append(term)
            if result.evidence is None:
                result.evidence = matched


def extract_term(title: str, description: str) -> TermResult:
    """Terms from the title come first; the description adds any others."""
    result = TermResult()
    _scan(title, result)
    _scan(description, result)
    return result
