"""Greenhouse job board API: https://developers.greenhouse.io/job-board.html"""

from __future__ import annotations

import re
from typing import Any

from pipeline.models import RawPosting, Source
from pipeline.sources.common import JobFields, iso_date, join_locations, text_or_none, without

# Greenhouse has no standard employment-type field. Some employers add a custom
# field to their job posts ("metadata"); these are the names seen for it.
EMPLOYMENT_TYPE_FIELD = re.compile(
    r"^\s*(?:employment|job|position|worker|contract)\s+(?:type|status)\s*$|^\s*type of employment\s*$|"
    r"^\s*commitment\s*$",
    re.IGNORECASE,
)
WORKPLACE_FIELD = re.compile(
    r"^\s*(?:working conditions|workplace(?: type)?|work location type|remote status)\s*$", re.I
)


def board_url(token: str) -> str:
    return f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"


def _metadata(j: dict[str, Any], pattern: re.Pattern[str]) -> str | None:
    for field in j.get("metadata") or []:
        if isinstance(field, dict) and pattern.search(str(field.get("name") or "")):
            value = text_or_none(field.get("value"))
            if value:
                return value
    return None


def job_fields(j: dict[str, Any]) -> JobFields:
    departments = [d.get("name") for d in j.get("departments") or [] if isinstance(d, dict)]
    return JobFields(
        employment_type_raw=_metadata(j, EMPLOYMENT_TYPE_FIELD),
        department=text_or_none(" / ".join(d for d in departments if d)),
        workplace_type_raw=_metadata(j, WORKPLACE_FIELD),
        posted_on=iso_date(j.get("first_published")),
    )


def parse(payload: Any, employer_id: str, token: str) -> list[RawPosting]:
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise ValueError("expected an object with a 'jobs' list")
    out = []
    for j in payload["jobs"]:
        offices = j.get("offices") or []
        location = join_locations(
            [(j.get("location") or {}).get("name")]
            + [o.get("location") for o in offices]
            + [o.get("name") for o in offices]
        )
        out.append(
            RawPosting(
                source=Source.greenhouse,
                board_token=token,
                employer_id=employer_id,
                source_job_id=str(j["id"]),
                title=(j.get("title") or "").strip(),
                url=j.get("absolute_url") or "",
                location_raw=location,
                description_html=j.get("content") or "",
                raw=without(j, "content"),
            )
        )
    return out
