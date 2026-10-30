"""Helpers shared by the source parsers."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class JobFields:
    """A board's own structured job-type fields, verbatim (ADR 0008). None when the board does not say."""

    employment_type_raw: str | None = None  # Lever commitment, Ashby employmentType, Greenhouse custom field
    department: str | None = None
    team: str | None = None
    workplace_type_raw: str | None = None
    posted_on: dt.date | None = None  # when the board says the job was first published


def text_or_none(value: Any) -> str | None:
    """A field value as clean text. Lists are joined with ", "; blanks become None."""
    if isinstance(value, list):
        value = ", ".join(str(v).strip() for v in value if v is not None and str(v).strip())
    if value is None or isinstance(value, dict):
        return None
    text = " ".join(str(value).split())
    return text or None


def iso_date(value: Any) -> dt.date | None:
    """The date part of an ISO 8601 timestamp, as the source wrote it (no time-zone shift)."""
    if not isinstance(value, str):
        return None
    try:
        return dt.date.fromisoformat(value[:10])
    except ValueError:
        return None


def join_locations(parts: list[Any]) -> str:
    """Join every location field into one string, dropping blanks and repeats."""
    seen: list[str] = []
    for p in parts:
        p = (p or "").strip() if isinstance(p, str) else ""
        if p and p not in seen:
            seen.append(p)
    return " / ".join(seen)


def without(record: dict[str, Any], *keys: str) -> dict[str, Any]:
    return {k: v for k, v in record.items() if k not in keys}
