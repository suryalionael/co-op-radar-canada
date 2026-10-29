"""Is this a student role? Title words only, so a senior posting that mentions
"our co-op program" in its description is not counted."""

from __future__ import annotations

import re

STUDENT_TITLE = re.compile(
    r"\b(?:interns?|internships?|co[-‐‑ ]?ops?|students?|stagiaires?|stages?|"
    r"summer (?:analyst|associate|student|engineer|developer))\b",
    re.IGNORECASE,
)


def is_student_role(title: str) -> tuple[bool, str | None]:
    m = STUDENT_TITLE.search(title)
    return (True, m.group(0)) if m else (False, None)
