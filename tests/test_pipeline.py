"""Tests for sources, raw storage, the posting ledger and processed output."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

import httpx
import pyarrow.parquet as pq
import pytest

from pipeline.models import BoardFetch, RawPosting, Source, Status
from pipeline.postings import PostingLedger, build_postings, write_postings
from pipeline.sources import ashby, fetch_board, greenhouse, keep_canadian, lever
from pipeline.sources.http import PoliteClient
from pipeline.storage import read_description, read_postings_day, write_postings_day

EMPLOYER = {"id": "acme", "board_type": "greenhouse", "board_token": "acme"}

GREENHOUSE_PAYLOAD = {
    "jobs": [
        {
            "id": 101,
            "title": "Data Science Co-op (Summer 2027)",
            "location": {"name": "Toronto, ON"},
            "content": "&lt;p&gt;A 4-month co-op on our analytics team.&lt;/p&gt;",
            "absolute_url": "https://boards.greenhouse.io/acme/jobs/101",
            "updated_at": "2026-10-01T00:00:00-04:00",
            "first_published": "2026-09-28T09:00:00-04:00",
            "departments": [{"id": 1, "name": "Co-op Experience"}],
            "metadata": [
                {"id": 9, "name": "Employment Type", "value": "Intern/Student", "value_type": "single_select"}
            ],
        },
        {
            "id": 102,
            "title": "Account Executive",
            "location": {"name": "Austin, TX"},
            "content": "&lt;p&gt;Sell things.&lt;/p&gt;",
            "absolute_url": "https://boards.greenhouse.io/acme/jobs/102",
        },
    ]
}


def mock_client(handler: Any) -> PoliteClient:
    return PoliteClient(min_interval=0, client=httpx.Client(transport=httpx.MockTransport(handler)))


# --- Sources --------------------------------------------------------------------


def test_greenhouse_parse_and_canada_filter() -> None:
    parsed = greenhouse.parse(GREENHOUSE_PAYLOAD, "acme", "acme")
    assert [p.source_job_id for p in parsed] == ["101", "102"]
    assert "content" not in parsed[0].raw
    kept = keep_canadian(parsed)
    assert [p.source_job_id for p in kept] == ["101"]
    assert len(kept[0].description_hash) == 64


def test_lever_parse() -> None:
    payload = [
        {
            "id": "abc",
            "text": "Software Co-op",
            "categories": {"location": "Waterloo", "allLocations": ["Waterloo", "Toronto"]},
            "country": "CA",
            "workplaceType": "hybrid",
            "description": "<p>An 8-month co-op.</p>",
            "descriptionPlain": "An 8-month co-op.",
            "lists": [{"text": "What you'll do", "content": "<li>Build things</li>"}],
            "hostedUrl": "https://jobs.lever.co/x/abc",
        }
    ]
    [p] = lever.parse(payload, "x", "x")
    assert p.location_raw == "Waterloo / Toronto / Canada"
    assert p.workplace_hint == "hybrid"
    assert "Build things" in p.description_html
    assert "descriptionPlain" not in p.raw


def test_ashby_parse_skips_unlisted() -> None:
    payload = {
        "jobs": [
            {"id": "1", "title": "ML Intern", "location": "Toronto", "isRemote": False, "jobUrl": "u1"},
            {"id": "2", "title": "Hidden", "location": "Toronto", "isListed": False, "jobUrl": "u2"},
        ]
    }
    assert [p.source_job_id for p in ashby.parse(payload, "y", "y")] == ["1"]


def test_lever_job_fields() -> None:
    record = {
        "categories": {"commitment": "Coop Student", "team": "Platform", "department": "Engineering"},
        "workplaceType": "hybrid",
        "createdAt": 1793500000000,
    }
    fields = lever.job_fields(record)
    assert (fields.employment_type_raw, fields.team, fields.department) == ("Coop Student", "Platform", "Engineering")
    assert fields.workplace_type_raw == "hybrid"
    assert fields.posted_on == dt.date(2026, 11, 1)
    assert lever.job_fields({}).employment_type_raw is None


def test_ashby_job_fields() -> None:
    record = {
        "employmentType": "Intern",
        "department": "Internships",
        "team": "Product Engineering",
        "workplaceType": "Hybrid",
        "publishedAt": "2026-10-12T15:04:05.000+00:00",
    }
    fields = ashby.job_fields(record)
    assert (fields.employment_type_raw, fields.department, fields.team) == (
        "Intern",
        "Internships",
        "Product Engineering",
    )
    assert (fields.workplace_type_raw, fields.posted_on) == ("Hybrid", dt.date(2026, 10, 12))


def test_greenhouse_job_fields_come_from_custom_metadata() -> None:
    [job, other] = GREENHOUSE_PAYLOAD["jobs"]
    fields = greenhouse.job_fields(job)
    assert (fields.employment_type_raw, fields.department) == ("Intern/Student", "Co-op Experience")
    assert fields.posted_on == dt.date(2026, 9, 28)
    # Unrelated custom fields are not mistaken for an employment type.
    survey = {"metadata": [{"name": "Which category should this job be listed under?", "value": "Internship"}]}
    assert greenhouse.job_fields(survey).employment_type_raw is None
    assert greenhouse.job_fields(other).employment_type_raw is None


def test_parsers_reject_wrong_shape() -> None:
    with pytest.raises(ValueError):
        greenhouse.parse({"status": 404}, "a", "a")
    with pytest.raises(ValueError):
        lever.parse({"ok": False}, "a", "a")


def test_fetch_board_success() -> None:
    client = mock_client(lambda request: httpx.Response(200, json=GREENHOUSE_PAYLOAD))
    status, kept = fetch_board(client, EMPLOYER)
    assert status.ok and (status.job_count, status.kept_count) == (2, 1)
    assert len(kept) == 1


@pytest.mark.parametrize(
    "response",
    [httpx.Response(404), httpx.Response(500), httpx.Response(200, text="<html>not json</html>"),
     httpx.Response(200, json={"unexpected": True})],
)  # fmt: skip
def test_fetch_board_failures_are_reported_not_raised(response: httpx.Response) -> None:
    status, kept = fetch_board(mock_client(lambda request: response), EMPLOYER)
    assert not status.ok and status.error
    assert kept == []


def test_fetch_board_network_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    status, _ = fetch_board(mock_client(handler), EMPLOYER)
    assert not status.ok and "ConnectError" in (status.error or "")


# --- Ledger: the closed-status guard -------------------------------------------

DAY = [dt.date(2026, 11, 1) + dt.timedelta(days=i) for i in range(6)]


def raw(job_id: str, title: str = "Data Co-op") -> RawPosting:
    return RawPosting(
        source=Source.greenhouse,
        board_token="acme",
        employer_id="acme",
        source_job_id=job_id,
        title=title,
        url=f"https://example.com/{job_id}",
        location_raw="Toronto, ON",
        description_hash="h",
    )


def board(ok: bool = True, job_count: int = 1) -> BoardFetch:
    return BoardFetch(
        source=Source.greenhouse,
        board_token="acme",
        employer_id="acme",
        fetched_at=dt.datetime(2026, 11, 1, tzinfo=dt.UTC),
        ok=ok,
        error=None if ok else "HTTP 500",
        job_count=job_count,
    )


def status_of(ledger: PostingLedger, job_id: str) -> tuple[Status, int]:
    t = ledger.postings[raw(job_id).key]
    return t.status, t.missed_fetches


def test_posting_closes_after_two_successful_misses() -> None:
    ledger = PostingLedger()
    ledger.apply_day(DAY[0], [board(job_count=2)], [raw("1"), raw("2")])
    ledger.apply_day(DAY[1], [board()], [raw("2")])
    assert status_of(ledger, "1") == (Status.open, 1)
    ledger.apply_day(DAY[2], [board()], [raw("2")])
    assert status_of(ledger, "1") == (Status.closed, 2)
    assert status_of(ledger, "2") == (Status.open, 0)


def test_failed_fetch_closes_nothing() -> None:
    ledger = PostingLedger()
    ledger.apply_day(DAY[0], [board()], [raw("1")])
    for day in DAY[1:5]:
        ledger.apply_day(day, [board(ok=False, job_count=0)], [])
    assert status_of(ledger, "1") == (Status.open, 0)
    assert ledger.postings[raw("1").key].last_seen == DAY[0]


def test_empty_fetch_after_jobs_counts_as_failed() -> None:
    ledger = PostingLedger()
    ledger.apply_day(DAY[0], [board(job_count=5)], [raw("1")])
    for day in DAY[1:5]:
        ledger.apply_day(day, [board(ok=True, job_count=0)], [])
    assert status_of(ledger, "1") == (Status.open, 0)


def test_postings_filtered_out_still_count_as_seen_board() -> None:
    # The board returned jobs, none of them Canadian: a real, successful fetch.
    ledger = PostingLedger()
    ledger.apply_day(DAY[0], [board(job_count=3)], [raw("1")])
    ledger.apply_day(DAY[1], [board(job_count=3)], [])
    ledger.apply_day(DAY[2], [board(job_count=3)], [])
    assert status_of(ledger, "1") == (Status.closed, 2)


def test_closed_posting_reopens() -> None:
    ledger = PostingLedger()
    ledger.apply_day(DAY[0], [board(job_count=2)], [raw("1"), raw("2")])
    ledger.apply_day(DAY[1], [board()], [raw("2")])
    ledger.apply_day(DAY[2], [board()], [raw("2")])
    ledger.apply_day(DAY[3], [board(job_count=2)], [raw("1"), raw("2")])
    assert status_of(ledger, "1") == (Status.open, 0)
    assert ledger.postings[raw("1").key].first_seen == DAY[0]


def test_other_boards_are_untouched() -> None:
    other = BoardFetch(
        source=Source.lever, board_token="other", employer_id="other",
        fetched_at=dt.datetime(2026, 11, 1, tzinfo=dt.UTC), ok=True, job_count=4,
    )  # fmt: skip
    ledger = PostingLedger()
    ledger.apply_day(DAY[0], [board()], [raw("1")])
    ledger.apply_day(DAY[1], [other], [])
    ledger.apply_day(DAY[2], [other], [])
    assert status_of(ledger, "1") == (Status.open, 0)


# --- Storage and processed output ----------------------------------------------


def write_fixture_days(root: Path) -> None:
    parsed = keep_canadian(greenhouse.parse(GREENHOUSE_PAYLOAD, "acme", "acme"))
    status = BoardFetch(
        source=Source.greenhouse, board_token="acme", employer_id="acme",
        fetched_at=dt.datetime(2026, 11, 1, 12, tzinfo=dt.UTC), ok=True, job_count=2, kept_count=1,
    )  # fmt: skip
    write_postings_day(root, DAY[0], [status], parsed)
    write_postings_day(root, DAY[1], [status], parsed)


def test_storage_round_trip_and_description_written_once(tmp_path: Path) -> None:
    write_fixture_days(tmp_path)
    boards, postings = read_postings_day(tmp_path, DAY[1])
    assert boards[0].ok and len(postings) == 1
    assert postings[0].description_html == ""  # descriptions live under their hash
    assert "4-month co-op" in read_description(tmp_path, postings[0].description_hash)
    assert len(list((tmp_path / "raw" / "descriptions").iterdir())) == 1


def test_raw_snapshot_is_byte_identical_on_rerun(tmp_path: Path) -> None:
    write_fixture_days(tmp_path)
    first = (tmp_path / "raw" / "postings" / f"{DAY[1]}.jsonl.gz").read_bytes()
    write_fixture_days(tmp_path)
    assert (tmp_path / "raw" / "postings" / f"{DAY[1]}.jsonl.gz").read_bytes() == first


def test_processing_is_reproducible(tmp_path: Path) -> None:
    write_fixture_days(tmp_path)
    write_postings(build_postings(tmp_path), tmp_path / "a.parquet")
    write_postings(build_postings(tmp_path), tmp_path / "b.parquet")
    assert (tmp_path / "a.parquet").read_bytes() == (tmp_path / "b.parquet").read_bytes()


def test_processed_postings_have_provenance_and_extraction(tmp_path: Path) -> None:
    write_fixture_days(tmp_path)
    [p] = build_postings(tmp_path)
    assert p.url.startswith("https://") and p.first_seen == DAY[0] and p.last_seen == DAY[1]
    assert p.description_hash
    assert (p.term, p.duration_options_months, p.province, p.track) == ("Summer 2027", [4.0], "ON", "data_science")
    assert p.evidence["duration"] == "4-month"
    assert p.is_student_role and p.in_canada

    path = tmp_path / "out.parquet"
    write_postings(build_postings(tmp_path), path)
    rows = pq.read_table(path).to_pylist()
    assert (rows[0]["employment_type_raw"], rows[0]["department"]) == ("Intern/Student", "Co-op Experience")
    assert rows[0]["posted_on"] == dt.date(2026, 9, 28)
    for row in rows:
        assert row["url"] and row["first_seen"], "every record needs a source URL and fetch date"
        assert json.loads(row["evidence"])


def test_term_in_past_is_flagged_not_corrected(tmp_path: Path) -> None:
    job = {
        **GREENHOUSE_PAYLOAD["jobs"][0],
        "id": 103,
        "title": "Data Co-op (Winter 2026)",
        "content": "&lt;p&gt;Join us.&lt;/p&gt;",
        "first_published": "2026-10-05T09:00:00-04:00",
    }
    parsed = keep_canadian(greenhouse.parse({"jobs": [job]}, "acme", "acme"))
    status = BoardFetch(
        source=Source.greenhouse, board_token="acme", employer_id="acme",
        fetched_at=dt.datetime(2026, 11, 1, 12, tzinfo=dt.UTC), ok=True, job_count=1, kept_count=1,
    )  # fmt: skip
    write_postings_day(tmp_path, DAY[0], [status], parsed)
    [p] = build_postings(tmp_path)
    assert p.term == "Winter 2026"  # kept exactly as stated
    assert p.flag_term_in_past is True
    assert p.term_status == "stated"
