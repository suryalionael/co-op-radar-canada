"""Greenhouse job board API: https://developers.greenhouse.io/job-board.html"""

from __future__ import annotations

from typing import Any

from pipeline.models import RawPosting, Source
from pipeline.sources.common import join_locations, without


def board_url(token: str) -> str:
    return f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"


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
