"""Work-term duration extractor.

A wrong duration is worse than "not stated" (the target is precision >= 0.95),
so this extractor is strict. A phrase like "4 months" counts only when:

- the same sentence names the work itself (co-op, internship, term, placement,
  contract, stage, position, role, program, duration, length), and
- nothing right around it says it is about something else: experience
  ("6+ months of experience"), leave, probation, vacation, notice, vesting,
  "within 3 months", "every 6 months", "at least 4 months", "up to 12 months".

When a posting offers several lengths ("4, 8 or 12-month terms") every option
is kept. A range ("8–12 months", "8 to 12 months") keeps its two ends as options
and sets `is_range`, so "8 or 12" and "anywhere from 8 to 12" stay distinguishable.

Weeks are converted to months and rounded to the nearest whole month
(16 weeks becomes 4); the original phrase stays in the evidence.

If no duration is stated but the term extractor found start and end dates, the
duration is computed from them and marked `inferred_from_dates`. Otherwise it is
`not_stated`. Durations are never guessed from what an employer usually offers.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field

from pipeline.models import DurationStatus

WORD_NUMBERS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "eighteen": 18,
    "twenty": 20,
    "twenty-four": 24,
    "quatre": 4,
    "huit": 8,
    "douze": 12,
    "seize": 16,
}
_NUM = r"(?:\d{1,2}(?:\.\d)?|" + "|".join(sorted(WORD_NUMBERS, key=len, reverse=True)) + r")"
_SEP = r"\s*(?:,\s*(?:or\s+|and\s+)?|/|\bor\b|\band\b|\bto\b|-|–|\bou\b|\bà\b|\bet\b)\s*"
DURATION = re.compile(
    rf"(?<![\w$.])(?P<nums>{_NUM}(?:{_SEP}{_NUM})*)(?P<plus>\s*\+)?\s*[-‐‑]?\s*"
    r"(?P<unit>months?|mos?\b|weeks?|wks?\b|mois|semaines?)\b",
    re.IGNORECASE,
)
NUMBER = re.compile(_NUM, re.IGNORECASE)

ROLE_WORDS = re.compile(
    r"\b(?:co-?op|co op|intern(?:ship)?s?|terms?|work terms?|placements?|contracts?|stages?|positions?|roles?|"
    r"programs?|programmes?|assignments?|duration|length|durée|fixed-term|temporary)\b",
    re.IGNORECASE,
)
NEGATIVE_AFTER = re.compile(
    r"^\W{0,3}(?:\w+\s+){0,3}?(?:of\s+)?(?:\w+\s+)?"
    r"(?:experience|exp\b|ago|probation|leave|vacation|holiday|pto|paid time off|notice|vesting|old|of age|"
    r"remaining|left|onboarding|training|warranty|salary|bonus|expérience)\b",
    re.IGNORECASE,
)
NEGATIVE_BEFORE = re.compile(
    r"(?:within|every|after|at least|minimum(?: of)?|min\.?|up to|over|more than|less than|past|last|"
    r"previous|prior|first|probation(?:ary)?(?: period)?(?: of)?|au moins)\s*(?:the\s+)?(?:a\s+)?$",
    re.IGNORECASE,
)
SENTENCE_END = re.compile(r"[.!?;\n•]")
RANGE_SPAN = re.compile(rf"^{_NUM}\s*(?:-|–|—|\bto\b|\bà\b)\s*{_NUM}\s*[-‐‑]?\s*\D", re.IGNORECASE)
WEEKS_PER_MONTH = 52 / 12
MAX_MONTHS = 24


@dataclass
class DurationResult:
    options_months: list[float] = field(default_factory=list)
    status: DurationStatus = DurationStatus.not_stated
    evidence: str | None = None
    is_range: bool = False  # the options are the two ends of a stated range


def _to_number(token: str) -> float:
    token = token.lower()
    return float(WORD_NUMBERS[token]) if token in WORD_NUMBERS else float(token)


def _sentence_around(text: str, start: int, end: int) -> tuple[str, str]:
    """Text before and after a match, cut at sentence boundaries."""
    before = text[max(0, start - 120) : start]
    cuts = list(SENTENCE_END.finditer(before))
    if cuts:
        before = before[cuts[-1].end() :]
    after = text[end : end + 120]
    cut = SENTENCE_END.search(after)
    if cut:
        after = after[: cut.start()]
    return before, after


def _accept(text: str, m: re.Match[str]) -> bool:
    if m["plus"]:
        return False  # "6+ months" is about experience
    before, after = _sentence_around(text, m.start(), m.end())
    if NEGATIVE_BEFORE.search(before) or NEGATIVE_AFTER.search(after):
        return False
    return bool(ROLE_WORDS.search(before) or ROLE_WORDS.search(after))


def _months(m: re.Match[str]) -> list[float]:
    values = [_to_number(n) for n in NUMBER.findall(m["nums"])]
    if m["unit"].lower().startswith(("w", "s")):  # weeks, wks, semaines
        values = [float(max(1, round(v / WEEKS_PER_MONTH))) for v in values]
    return values


def find_stated(text: str) -> tuple[list[float], list[str]]:
    options: list[float] = []
    evidence: list[str] = []
    for m in DURATION.finditer(text):
        if not _accept(text, m):
            continue
        values = _months(m)
        if not values or any(v <= 0 or v > MAX_MONTHS for v in values):
            continue
        options.extend(values)
        evidence.append(m.group(0).strip())
    return options, evidence


def extract_duration(
    title: str,
    description: str,
    term_start: dt.date | None = None,
    term_end: dt.date | None = None,
    dates_evidence: str | None = None,
) -> DurationResult:
    options, evidence = [], []
    for text in (title, description):
        found, spans = find_stated(text)
        options += found
        evidence += spans
    if options:
        is_range = any(RANGE_SPAN.search(span) for span in evidence)
        return DurationResult(
            sorted(set(options)), DurationStatus.stated, " | ".join(dict.fromkeys(evidence)), is_range
        )

    if term_start and term_end and term_end > term_start:
        months = round((term_end - term_start).days / (365.25 / 12))
        if 1 <= months <= MAX_MONTHS:
            return DurationResult([float(months)], DurationStatus.inferred_from_dates, dates_evidence)
    return DurationResult()
