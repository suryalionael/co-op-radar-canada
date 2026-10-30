"""Ashby posting API: https://developers.ashbyhq.com/docs/public-job-posting-api"""

from __future__ import annotations

from typing import Any

from pipeline.models import RawPosting, Source
from pipeline.sources.common import JobFields, iso_date, join_locations, text_or_none, without


def board_url(token: str) -> str:
    return f"https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true"


def job_fields(j: dict[str, Any]) -> JobFields:
    return JobFields(
        employment_type_raw=text_or_none(j.get("employmentType")),  # FullTime, PartTime, Intern, Contract, Temporary
        department=text_or_none(j.get("department")),
        team=text_or_none(j.get("team")),
        workplace_type_raw=text_or_none(j.get("workplaceType")),
        posted_on=iso_date(j.get("publishedAt")),
    )


def parse(payload: Any, employer_id: str, token: str) -> list[RawPosting]:
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise ValueError("expected an object with a 'jobs' list")
    out = []
    for j in payload["jobs"]:
        if j.get("isListed") is False:
            continue
        address = (j.get("address") or {}).get("postalAddress") or {}
        secondary = [s.get("location") for s in j.get("secondaryLocations") or []]
        workplace = j.get("workplaceType") or ("Remote" if j.get("isRemote") else "")
        out.append(
            RawPosting(
                source=Source.ashby,
                board_token=token,
                employer_id=employer_id,
                source_job_id=str(j.get("id") or j.get("jobUrl")),
                title=(j.get("title") or "").strip(),
                url=j.get("jobUrl") or "",
                location_raw=join_locations(
                    [j.get("location"), *secondary, address.get("addressRegion"), address.get("addressCountry")]
                ),
                workplace_hint=workplace,
                description_html=j.get("descriptionHtml") or "",
                raw=without(j, "descriptionHtml", "descriptionPlain"),
            )
        )
    return out
