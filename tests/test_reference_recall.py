"""Tests for the recall check against the curated list (ADR 0007). Invented rows only, no network."""

from __future__ import annotations

import datetime as dt
from typing import Any

import httpx

from pipeline import reference_recall as rr
from pipeline.models import (
    DurationStatus,
    Posting,
    Province,
    Remote,
    RoleType,
    Source,
    Status,
    TermStatus,
    Track,
    posting_id,
)  # fmt: skip
from pipeline.reference_list import ReferenceRow
from pipeline.sources.http import PoliteClient

EMPLOYERS = [
    {"id": "maple", "name": "Maplewood Robotics", "board_type": "greenhouse", "board_token": "maplewood"},
    {"id": "lake", "name": "Lakeview Analytics", "board_type": "lever", "board_token": "lakeview"},
]


def row(company: str, url: str | None, term: str | None = None, season: int = 2027) -> ReferenceRow:
    return ReferenceRow(
        season=season, company=company, role="Data Co-op", term=term, location="Toronto, ON", apply_url=url,
        closed=url is None, date_posted_raw="Oct 1, 2026", date_posted=dt.date(2026, 10, 1),
    )  # fmt: skip


def posting(source: Source, token: str, job_id: str, url: str, **changes: Any) -> Posting:
    base = Posting(
        id=posting_id(source, token, job_id), source=source, board_token=token, employer_id=token, title="Data Co-op",
        url=url, location_raw="Toronto, ON", in_canada=True, province=Province.ON, provinces=[Province.ON],
        remote=Remote.unknown, term="Summer 2027", terms=["Summer 2027"], term_status=TermStatus.stated,
        term_start=None, term_end=None, duration_options_months=[], duration_is_range=False,
        duration_status=DurationStatus.not_stated, track=Track.data_science, is_student_role=True,
        role_type=RoleType.coop, evidence={}, description_hash="h", first_seen=dt.date(2026, 10, 29),
        last_seen=dt.date(2026, 10, 30), missed_fetches=0, status=Status.open,
    )  # fmt: skip
    return base.model_copy(update=changes)


def test_reference_set_keeps_open_2027_rows_of_tracked_employers() -> None:
    rows = [
        row("Maplewood Robotics", "https://job-boards.greenhouse.io/maplewood/jobs/1"),
        row("Maplewood Robotics", "https://careers.maplewood.example/jobs?gh_jid=2"),  # token unknown: by name
        row("Maplewood Robotics", None),  # closed
        row("Maplewood Robotics", "https://job-boards.greenhouse.io/maplewood/jobs/3", season=2026),
        row("Untracked Co", "https://jobs.lever.co/untracked/abc"),
        row("Lakeview Analytics", "https://lakeview.wd3.myworkdayjobs.com/x"),  # not a token platform
    ]
    found = rr.reference_set(rows, EMPLOYERS)
    assert [(c.source, c.board_token, c.job_id) for c in found] == [
        (Source.greenhouse, "maplewood", "1"),
        (Source.greenhouse, "maplewood", "2"),
    ]


def test_match_by_job_id_then_url_and_reasons() -> None:
    rows = [
        row("Maplewood Robotics", "https://job-boards.greenhouse.io/maplewood/jobs/1", term="Summer 2027"),
        row("Lakeview Analytics", "https://jobs.lever.co/lakeview/aaa/apply"),
        row("Lakeview Analytics", "https://jobs.lever.co/lakeview/bbb"),
        row("Lakeview Analytics", "https://jobs.lever.co/lakeview/ccc"),
        row("Lakeview Analytics", "https://jobs.lever.co/lakeview/ddd"),
    ]
    postings = [
        posting(Source.greenhouse, "maplewood", "1", "https://job-boards.greenhouse.io/maplewood/jobs/1"),
        # Stored under a different id, found by its URL ("/apply" dropped).
        posting(Source.lever, "lakeview", "other-id", "https://jobs.lever.co/lakeview/aaa"),
        posting(Source.lever, "lakeview", "bbb", "u-bbb", status=Status.closed),
        posting(Source.lever, "lakeview", "ccc", "u-ccc", is_student_role=False, role_type=RoleType.none),
    ]
    outcomes = rr.match(rr.reference_set(rows, EMPLOYERS), postings)
    assert [o.reason for o in outcomes] == ["found", "found", "closed", "not_student", "not_checked"]
    assert str(rr.recall(outcomes)) == "2/5 = 0.40 (95% CI 0.12–0.77)"


def test_url_normalization_keeps_job_ids_in_the_query() -> None:
    a = rr.normalize_url("https://www.example.com/careers/jobs/?job_id=1&gh_jid=1&utm_source=x")
    b = rr.normalize_url("https://example.com/careers/jobs?gh_jid=1&job_id=1")
    c = rr.normalize_url("https://example.com/careers/jobs?gh_jid=2&job_id=2")
    assert a == b != c


def mock_client(payloads: dict[str, Any]) -> PoliteClient:
    def handler(request: httpx.Request) -> httpx.Response:
        for token, payload in payloads.items():
            if f"/{token}" in request.url.path:
                return httpx.Response(200, json=payload)
        return httpx.Response(404)

    return PoliteClient(min_interval=0, client=httpx.Client(transport=httpx.MockTransport(handler)))


def test_explain_misses_from_the_live_board() -> None:
    rows = [row("Lakeview Analytics", f"https://jobs.lever.co/lakeview/{j}") for j in ("gone", "us", "ca")]
    outcomes = rr.match(rr.reference_set(rows, EMPLOYERS), [])
    lever_jobs = [
        {"id": "us", "text": "Data Co-op", "categories": {"location": "Austin, TX"}, "hostedUrl": "u1"},
        {"id": "ca", "text": "Data Co-op", "categories": {"location": "Toronto, ON"}, "hostedUrl": "u2"},
    ]
    rr.explain_misses(outcomes, mock_client({"lakeview": lever_jobs}), {(Source.lever, "lakeview")})
    assert [o.reason for o in outcomes] == ["gone", "filtered", "not_in_snapshot"]

    outcomes = rr.match(rr.reference_set(rows[2:], EMPLOYERS), [])
    rr.explain_misses(outcomes, mock_client({"lakeview": lever_jobs}), set())
    assert outcomes[0].reason == "new_employer"

    outcomes = rr.match(rr.reference_set(rows[2:], EMPLOYERS), [])
    rr.explain_misses(outcomes, mock_client({}), set())
    assert outcomes[0].reason == "board_failed"


def test_recall_on_snapshot_boards_leaves_out_new_employers() -> None:
    rows = [
        row("Maplewood Robotics", "https://job-boards.greenhouse.io/maplewood/jobs/1"),
        row("Lakeview Analytics", "https://jobs.lever.co/lakeview/x"),
    ]
    postings = [posting(Source.greenhouse, "maplewood", "1", "u1")]
    outcomes = rr.match(rr.reference_set(rows, EMPLOYERS), postings)
    assert rr.recall(rr.on_snapshot_boards(outcomes, {(Source.greenhouse, "maplewood")})).n == 1


def test_term_cross_check_is_a_report_not_labels() -> None:
    rows = [
        row("Lakeview Analytics", "https://jobs.lever.co/lakeview/a", term="Summer 2027"),
        row("Lakeview Analytics", "https://jobs.lever.co/lakeview/b", term="Winter 2027"),
        row("Lakeview Analytics", "https://jobs.lever.co/lakeview/c", term="Fall 2027"),
        row("Lakeview Analytics", "https://jobs.lever.co/lakeview/d", term="Summer 2027"),
        row("Lakeview Analytics", "https://jobs.lever.co/lakeview/e"),  # no curator term: not compared
    ]
    postings = [
        posting(Source.lever, "lakeview", "a", "ua"),
        posting(Source.lever, "lakeview", "b", "ub"),  # we said Summer 2027
        posting(Source.lever, "lakeview", "c", "uc", term=None, terms=[], term_status=TermStatus.not_stated),
        posting(Source.lever, "lakeview", "d", "ud", term=None, terms=[], term_status=TermStatus.ambiguous),
        posting(Source.lever, "lakeview", "e", "ue"),
    ]
    check = rr.term_cross_check(rr.match(rr.reference_set(rows, EMPLOYERS), postings))
    assert (check.agree, check.disagree, check.we_not_stated, check.we_ambiguous) == (1, 1, 1, 1)
    assert check.examples == [("Winter 2027", "Summer 2027")]
