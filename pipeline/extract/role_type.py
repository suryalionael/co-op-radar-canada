"""Role-type extractor: is this a co-op, an internship, another student role, or none?

Signals, strongest first (ADR 0008):

1. The board's structured employment type (Lever `commitment`, Ashby
   `employmentType`, a Greenhouse custom field), e.g. "Coop Student" or "Intern".
2. The title.
3. The description, which can only *refine* a role the first two already call a
   student role (a "Summer Student" title whose description says "this co-op
   term"). It never makes a role a student role on its own, so a senior posting
   that mentions "our co-op program" is not counted.

A structured field that says nothing student-like ("Full-time", "FullTime")
is no signal either way: many boards leave it at its default for interns.

Between the structured field and the title, the more specific type wins
(co-op over intern over student) and ties go to the structured field. Ashby's
fixed list has "Intern" but no co-op value, so a title saying "Co-op" refines it.

Every rule matches whole words only:

- co-op: "co-op", "coop", "co op" (plural allowed). "Cooperative", "cooperation"
  and "coop" inside a longer word do not match.
- intern: "intern", "interns", "internship(s)", "stagiaire", and French "stage"
  followed by en/de/d'/du/à ("Stage en données"). "Internal", "International"
  and English "Early Stage" do not match.
- student: "student(s)" unless it names a service for students ("Student
  Success", "Student Services") or follows "for/to/with" ("Advisor for students").
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pipeline.models import RoleType

COOP = re.compile(r"\bco[-‐‑ ]?ops?\b", re.IGNORECASE)
INTERN = re.compile(
    r"\binterns?\b|\binternships?\b|\bstagiaires?\b|\bstages?\b(?=\s+(?:en|de|du|d['’]|à)\b)|"
    r"\bsummer (?:analyst|associate|engineer|developer)s?\b",
    re.IGNORECASE,
)
STUDENT = re.compile(
    r"(?<!\bfor )(?<!\bto )(?<!\bwith )\bstudents?\b"
    r"(?!\s+(?:success|services?|experience|recruit\w*|affairs|engagement|support|advis\w*|loans?|housing|"
    r"life|enrol\w*|outreach|counsel\w*|financ\w*|information systems?|records)\b)",
    re.IGNORECASE,
)
PATTERNS: list[tuple[RoleType, re.Pattern[str]]] = [
    (RoleType.coop, COOP),
    (RoleType.intern, INTERN),
    (RoleType.student, STUDENT),
]
SPECIFICITY = {RoleType.coop: 3, RoleType.intern: 2, RoleType.student: 1, RoleType.none: 0}


@dataclass
class RoleTypeResult:
    role_type: RoleType = RoleType.none
    evidence: str | None = None  # the exact matched text
    field: str | None = None  # where it matched: employment_type, title or description

    @property
    def is_student_role(self) -> bool:
        return self.role_type is not RoleType.none


def match(text: str) -> tuple[RoleType, str | None]:
    """The most specific role type named in the text, with the matched span."""
    for role_type, pattern in PATTERNS:
        m = pattern.search(text)
        if m:
            return role_type, m.group(0)
    return RoleType.none, None


def extract_role_type(title: str, description: str = "", employment_type: str | None = None) -> RoleTypeResult:
    structured = RoleTypeResult(*match(employment_type or ""), "employment_type")
    from_title = RoleTypeResult(*match(title), "title")
    best = structured
    if SPECIFICITY[from_title.role_type] > SPECIFICITY[best.role_type]:
        best = from_title
    if not best.is_student_role:
        return RoleTypeResult()
    if best.role_type is RoleType.student and description:
        refined = RoleTypeResult(*match(description), "description")
        if refined.role_type in (RoleType.coop, RoleType.intern):
            return refined
    return best
