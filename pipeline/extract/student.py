"""Is this a student role? A thin wrapper over the role-type extractor (role_type.py),
kept for callers that only need yes or no."""

from __future__ import annotations

from pipeline.extract.role_type import extract_role_type


def is_student_role(title: str, employment_type: str | None = None) -> tuple[bool, str | None]:
    result = extract_role_type(title, employment_type=employment_type)
    return result.is_student_role, result.evidence
