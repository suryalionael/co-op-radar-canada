"""Pydantic records shared by the pipeline and the site build.

Field names are the contract between the pipeline and the site (brief section 6).
Two additions to the brief's model are recorded in ADR 0006: `terms` and
`provinces` hold every value found, while `term` and `province` keep the first
one for display.
"""

from __future__ import annotations

import datetime as dt
import hashlib
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Source(StrEnum):
    greenhouse = "greenhouse"
    lever = "lever"
    ashby = "ashby"
    submission = "submission"


class Province(StrEnum):
    ON = "ON"
    QC = "QC"
    BC = "BC"
    AB = "AB"
    MB = "MB"
    SK = "SK"
    NS = "NS"
    NB = "NB"
    NL = "NL"
    PE = "PE"
    YT = "YT"
    NT = "NT"
    NU = "NU"
    REMOTE_CA = "REMOTE_CA"
    UNKNOWN = "UNKNOWN"


class Remote(StrEnum):
    onsite = "onsite"
    hybrid = "hybrid"
    remote = "remote"
    unknown = "unknown"


class DurationStatus(StrEnum):
    stated = "stated"
    inferred_from_dates = "inferred_from_dates"
    not_stated = "not_stated"


class Track(StrEnum):
    data_science = "data_science"
    data_analytics = "data_analytics"
    data_eng = "data_eng"
    ml_ai = "ml_ai"
    software = "software"
    business_ops = "business_ops"
    other = "other"


class Status(StrEnum):
    open = "open"
    closed = "closed"


def posting_id(source: str, board_token: str, source_job_id: str) -> str:
    """Stable key for a posting: a short hash of (source, board_token, source_job_id)."""
    return hashlib.sha256(f"{source}:{board_token}:{source_job_id}".encode()).hexdigest()[:16]


class RawPosting(BaseModel):
    """One job as a source returned it, normalized to common field names.

    `raw` keeps every field from the API except the description, which is stored
    once per distinct text under its hash (ADR 0002).
    """

    model_config = ConfigDict(frozen=True)

    source: Source
    board_token: str
    employer_id: str
    source_job_id: str
    title: str
    url: str
    location_raw: str
    workplace_hint: str = ""  # structured remote/hybrid field from the API, if any
    description_html: str = Field(default="", exclude=True)
    description_hash: str = ""
    raw: dict[str, object] = Field(default_factory=dict)

    @property
    def key(self) -> str:
        return posting_id(self.source, self.board_token, self.source_job_id)


class BoardFetch(BaseModel):
    """Outcome of fetching one board on one day."""

    source: Source
    board_token: str
    employer_id: str
    fetched_at: dt.datetime
    ok: bool
    error: str | None = None
    job_count: int = 0  # jobs the API returned, before the loose Canada filter
    kept_count: int = 0  # jobs kept by the loose Canada filter


class Posting(BaseModel):
    id: str
    source: Source
    board_token: str
    employer_id: str
    title: str
    url: str
    location_raw: str
    in_canada: bool
    province: Province
    provinces: list[Province]
    remote: Remote
    term: str | None
    terms: list[str]
    term_start: dt.date | None
    term_end: dt.date | None
    duration_options_months: list[float]
    duration_status: DurationStatus
    track: Track
    is_student_role: bool
    evidence: dict[str, str]
    description_hash: str
    first_seen: dt.date
    last_seen: dt.date
    missed_fetches: int
    status: Status
    deadline: dt.date | None = None


class ProgramWatch(BaseModel):
    program_id: str
    employer_id: str
    name: str
    url: str
    last_hash: str | None
    last_checked: dt.date | None
    last_fetch_ok: bool
    last_changed: dt.date | None
    change_excerpt: str | None
    expected_open: dt.date | None
    expected_open_src: str | None


class ChangeKind(StrEnum):
    content_change = "content_change"
    manual_note = "manual_note"


class ProgramChange(BaseModel):
    program_id: str
    changed_on: dt.date
    change_excerpt: str
    kind: ChangeKind
