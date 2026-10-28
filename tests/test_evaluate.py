from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from pipeline.evaluate import Ratio, read_labels, score, wilson_interval, write_label_sheet
from pipeline.models import DurationStatus, Posting, Province, Remote, Source, Status, Track


def test_wilson_interval_matches_known_values() -> None:
    low, high = wilson_interval(57, 59)
    assert (round(low, 2), round(high, 2)) == (0.88, 0.99)
    assert wilson_interval(0, 0) == (0.0, 1.0)
    low, high = wilson_interval(10, 10)
    assert high == 1.0 and 0.72 < low < 0.73


def test_ratio_format() -> None:
    assert str(Ratio(57, 59)) == "57/59 = 0.97 (95% CI 0.88–0.99)"
    assert str(Ratio(0, 0)) == "0/0 (no cases)"


def posting(pid: str, durations: list[float], term: str | None, provinces: list[Province]) -> Posting:
    return Posting(
        id=pid, source=Source.greenhouse, board_token="a", employer_id="a", title="Co-op", url="https://x",
        location_raw="Toronto", in_canada=True, province=provinces[0] if provinces else Province.UNKNOWN,
        provinces=provinces, remote=Remote.unknown, term=term, terms=[term] if term else [], term_start=None,
        term_end=None, duration_options_months=durations,
        duration_status=DurationStatus.stated if durations else DurationStatus.not_stated, track=Track.software,
        is_student_role=True, evidence={}, description_hash="h", first_seen=dt.date(2026, 11, 1),
        last_seen=dt.date(2026, 11, 1), missed_fetches=0, status=Status.open,
    )  # fmt: skip


def label(pid: str, duration: str, term: str, province: str) -> dict[str, str]:
    return {
        "id": pid, "term": term, "duration_options_months": duration, "province": province,
        "track": "software", "is_student_role": "yes",
    }  # fmt: skip


def test_score_precision_counts_only_predicted_values() -> None:
    postings = {
        "1": posting("1", [4.0], "Summer 2027", [Province.ON]),  # right
        "2": posting("2", [8.0], None, [Province.ON]),  # wrong duration, missed term
        "3": posting("3", [], None, []),  # not stated, and truly not stated
        "4": posting("4", [], "Fall 2027", [Province.BC]),  # duration missed
    }
    labels = [
        label("1", "4", "Summer 2027", "ON"),
        label("2", "4", "Summer 2027", "ON"),
        label("3", "", "", ""),
        label("4", "4;8", "Fall 2027", "BC"),
        label("unknown", "4", "", ""),  # not in postings: ignored
    ]
    scores = {s.field: s for s in score(labels, postings)}
    d = scores["duration"]
    assert (d.precision.k, d.precision.n) == (1, 2)
    assert (d.recall.k, d.recall.n) == (1, 3)
    t = scores["term"]
    assert (t.precision.k, t.precision.n, t.recall.k, t.recall.n) == (2, 2, 2, 3)
    assert (scores["province"].precision.k, scores["province"].precision.n) == (3, 3)


def test_label_sheet_append_skips_labelled(tmp_path: Path) -> None:
    sheet = tmp_path / "postings.csv"
    ps = [posting("1", [], None, []), posting("2", [], None, [])]
    assert write_label_sheet(ps, sheet, set()) == 2
    rows = read_labels(sheet)
    assert [r["id"] for r in rows] == ["1", "2"]
    assert rows[0]["duration_options_months"] == ""  # predictions are not exported
    assert write_label_sheet(ps, sheet, {r["id"] for r in rows}) == 0


@pytest.mark.parametrize(("k", "n"), [(1, 3), (95, 100), (200, 200)])
def test_interval_contains_point_estimate(k: int, n: int) -> None:
    low, high = wilson_interval(k, n)
    assert low <= k / n <= high
