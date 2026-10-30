"""The site gets only open Canadian student postings, with employer names and evidence."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from pipeline.build_site_data import build
from pipeline.models import (
    ChangeKind,
    DurationStatus,
    Posting,
    ProgramChange,
    ProgramWatch,
    Province,
    Remote,
    RoleType,
    Source,
    Status,
    Track,
)  # fmt: skip
from pipeline.postings import write_postings
from pipeline.program_watch import write_program_watch


def posting(pid: str, **changes: object) -> Posting:
    base = Posting(
        id=pid, source=Source.greenhouse, board_token="acme", employer_id="acme", title="Data Co-op",
        url=f"https://x/{pid}", location_raw="Toronto, ON", in_canada=True, province=Province.ON,
        provinces=[Province.ON], remote=Remote.hybrid, term="Summer 2027", terms=["Summer 2027"],
        term_start=None, term_end=None, duration_options_months=[4.0], duration_status=DurationStatus.stated,
        track=Track.data_science, is_student_role=True, role_type=RoleType.coop,
        evidence={"term": "Summer 2027", "duration": "4-month", "province": "Toronto"},
        description_hash="h", first_seen=dt.date(2026, 11, 2), last_seen=dt.date(2026, 11, 3),
        missed_fetches=0, status=Status.open,
    )  # fmt: skip
    return base.model_copy(update=changes)


def setup(tmp_path: Path) -> tuple[Path, Path, Path]:
    processed, out = tmp_path / "processed", tmp_path / "out"
    employers = tmp_path / "employers.yaml"
    employers.write_text("employers:\n  - {id: acme, name: Acme Corp, sector: software}\n")
    return processed, out, employers


def test_empty_when_no_processed_data(tmp_path: Path) -> None:
    processed, out, employers = setup(tmp_path)
    meta = build(processed, out, employers, tmp_path / "none.jsonl")
    assert json.loads((out / "postings.json").read_text()) == []
    assert meta["counts"]["open_student_postings"] == 0
    assert meta["data_as_of"] == {"postings": None, "programs": None}


def test_only_open_canadian_student_postings(tmp_path: Path) -> None:
    processed, out, employers = setup(tmp_path)
    write_postings(
        [
            posting("a"),
            posting("b", first_seen=dt.date(2026, 11, 3)),
            posting("closed", status=Status.closed),
            posting("senior", is_student_role=False, title="Senior Engineer"),
            posting("usa", in_canada=False, provinces=[], province=Province.UNKNOWN),
        ],
        processed / "postings.parquet",
    )
    run_log = tmp_path / "run_log.jsonl"
    run_log.write_text(
        '{"command": "fetch-postings", "day": "2026-11-02"}\n{"command": "fetch-postings", "day": "2026-11-03"}\n'
    )
    meta = build(processed, out, employers, run_log)
    rows = json.loads((out / "postings.json").read_text())
    assert [r["id"] for r in rows] == ["b", "a"]  # newest first
    assert rows[0]["employer"] == "Acme Corp"
    assert rows[0]["evidence"] == {"term": "Summer 2027", "duration": "4-month"}
    assert rows[0]["first_seen"] == "2026-11-03"
    assert meta["data_as_of"]["postings"] == "2026-11-03"
    assert meta["counts"]["duration_stated"] == 2


def test_output_is_stable(tmp_path: Path) -> None:
    processed, out, employers = setup(tmp_path)
    write_postings([posting("a")], processed / "postings.parquet")
    build(processed, out, employers, tmp_path / "none.jsonl")
    first = (out / "postings.json").read_bytes()
    build(processed, out, employers, tmp_path / "none.jsonl")
    assert (out / "postings.json").read_bytes() == first


def test_programs(tmp_path: Path) -> None:
    processed, out, employers = setup(tmp_path)
    watch = [
        ProgramWatch(
            program_id="fswep", employer_id="goc", name="FSWEP", url="https://x", last_hash="h",
            last_checked=dt.date(2026, 11, 3), last_fetch_ok=True, last_changed=dt.date(2026, 11, 2),
            change_excerpt="Applications open", expected_open=None, expected_open_src=None,
        )
    ]  # fmt: skip
    changes = [
        ProgramChange(
            program_id="fswep", changed_on=dt.date(2026, 11, 2), change_excerpt="Applications open",
            kind=ChangeKind.content_change,
        )
    ]  # fmt: skip
    write_program_watch(watch, changes, processed)
    build(processed, out, employers, tmp_path / "none.jsonl")
    data = json.loads((out / "programs.json").read_text())
    assert data["programs"][0]["last_changed"] == "2026-11-02"
    assert data["changes"][0]["kind"] == "content_change"
