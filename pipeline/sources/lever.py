"""Lever postings API: https://github.com/lever/postings-api"""

from __future__ import annotations

from typing import Any

from pipeline.models import RawPosting, Source
from pipeline.sources.common import join_locations, without

DESCRIPTION_FIELDS = (
    "description",
    "descriptionPlain",
    "lists",
    "additional",
    "additionalPlain",
    "opening",
    "openingPlain",
    "descriptionBody",
    "descriptionBodyPlain",
)


def board_url(token: str) -> str:
    return f"https://api.lever.co/v0/postings/{token}?mode=json"


def _description_html(j: dict[str, Any]) -> str:
    parts = [j.get("description") or ""]
    for section in j.get("lists") or []:
        parts.append(f"<h3>{section.get('text', '')}</h3><ul>{section.get('content', '')}</ul>")
    parts.append(j.get("additional") or "")
    return "\n".join(p for p in parts if p)


def parse(payload: Any, employer_id: str, token: str) -> list[RawPosting]:
    if not isinstance(payload, list):
        raise ValueError("expected a list of postings")
    out = []
    for j in payload:
        cats = j.get("categories") or {}
        # Lever's two-letter country code is a location field too.
        country = "Canada" if (j.get("country") or "").upper() == "CA" else j.get("country")
        out.append(
            RawPosting(
                source=Source.lever,
                board_token=token,
                employer_id=employer_id,
                source_job_id=str(j["id"]),
                title=(j.get("text") or "").strip(),
                url=j.get("hostedUrl") or "",
                location_raw=join_locations([cats.get("location"), *(cats.get("allLocations") or []), country]),
                workplace_hint=j.get("workplaceType") or "",
                description_html=_description_html(j),
                raw=without(j, *DESCRIPTION_FIELDS),
            )
        )
    return out
