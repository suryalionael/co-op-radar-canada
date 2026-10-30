"""Tests for the Phase 0 counting rules in docs/decisions/0001-coverage-thresholds.md."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import coverage_spike as cs  # noqa: E402


@pytest.mark.parametrize(
    "location",
    [
        "Toronto, ON",
        "Toronto, Ontario, Canada",
        "Remote - Canada",
        "Remote - ON",
        "Vancouver",
        "Montréal, QC",
        "Waterloo / New York",
        "Kitchener-Waterloo",
        "ON, Canada",
        "Halifax, Nova Scotia",
        "St. John's, NL",
    ],
)
def test_canadian_locations(location: str) -> None:
    assert cs.is_canadian_location(location)


@pytest.mark.parametrize(
    "location",
    [
        "Remote",
        "San Francisco, CA",
        "London, UK",
        "Melbourne, Victoria",
        "Boston, MA",
        "Hybrid - work on site 3 days",
        "Remote - US",
        "",
    ],
)
def test_non_canadian_locations(location: str) -> None:
    assert not cs.is_canadian_location(location)


@pytest.mark.parametrize(
    ("location", "expected"),
    [
        ("Remote", True),
        ("Remote - Anywhere", True),
        ("Fully Remote", True),
        ("Remote - US", False),
        ("Remote, Germany", False),
        ("New York", False),
    ],
)
def test_remote_no_country(location: str, expected: bool) -> None:
    assert cs.is_remote_no_country(location) is expected


@pytest.mark.parametrize(
    "title",
    [
        "Software Engineering Intern (Summer 2027)",
        "Data Science Internship",
        "Co-op Student, Analytics",
        "Coop - Developer",
        "Co op Developer",
        "Summer Analyst",
        "Stagiaire en développement",
        "Stage - Analyste de données",
        "Interns - Product",
    ],
)
def test_student_titles(title: str) -> None:
    assert cs.is_student_title(title)


@pytest.mark.parametrize(
    "title",
    ["Internal Tools Engineer", "International Sales Lead", "Staged Rollout Engineer", "Senior Data Scientist"],
)
def test_non_student_titles(title: str) -> None:
    assert not cs.is_student_title(title)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("This is a Summer 2027 role", "Summer 2027"),
        ("Starting in the Fall term, 2026", "Fall term, 2026"),
        ("For summer of 2027", "summer of 2027"),
        ("Join us for Winter '27", "Winter '27"),
        ("2027 Summer cohort", "2027 Summer"),
        ("No dates here", None),
    ],
)
def test_term_mention(text: str, expected: str | None) -> None:
    assert cs.first_match(cs.TERM_MENTION, text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("a 4-month co-op", "4-month"),
        ("We offer 4, 8 or 12-month terms", "4, 8 or 12-month"),
        ("16 weeks starting May", "16 weeks"),
        ("a four month placement", "four month"),
        ("un stage de 4 mois", "4 mois"),
        ("Great team and perks", None),
    ],
)
def test_duration_mention(text: str, expected: str | None) -> None:
    assert cs.first_match(cs.DURATION_MENTION, text) == expected


def test_html_to_text_handles_greenhouse_double_escaping() -> None:
    assert cs.html_to_text("&lt;p&gt;A 4-month &amp;amp; paid role&lt;/p&gt;") == "A 4-month & paid role"


GREENHOUSE = {
    "jobs": [
        {
            "id": 1,
            "title": "Data Science Intern",
            "location": {"name": "Toronto, ON"},
            "content": "&lt;p&gt;Summer 2027, 4-month term&lt;/p&gt;",
            "absolute_url": "https://example.com/1",
        },
        # Same job listed twice: counted once.
        {"id": 1, "title": "Data Science Intern", "location": {"name": "Toronto, ON"}, "content": ""},
        # Canadian only through its office list.
        {
            "id": 2,
            "title": "Software Engineer",
            "location": {"name": "Hybrid"},
            "offices": [{"name": "Vancouver", "location": "Vancouver, BC"}],
            "content": "",
        },
        # Canada only in the description: not counted as in Canada.
        {"id": 3, "title": "Summer Student", "location": {"name": "New York"}, "content": "Open to Canada"},
        {"id": 4, "title": "Engineering Intern", "location": {"name": "Remote"}, "content": ""},
    ]
}


def test_measure_greenhouse_board() -> None:
    employer = {"id": "acme", "board_type": "greenhouse", "board_token": "acme"}
    r = cs.measure_board(employer, GREENHOUSE)
    assert r.ok
    assert r.total == 4
    assert r.canada == 2
    assert r.canada_student == 1
    assert r.canada_student_with_term == 1
    assert r.canada_student_with_duration == 1
    assert r.remote_student_no_country == 1
    # Loose filter keeps 1 and 2 (location), 3 (description says Canada) and 4 (remote).
    assert r.loose_filter_kept == 4
    assert r.loose_filter_bytes > 0
    assert r.student_postings[0]["term_match"] == "Summer 2027"


def test_measure_lever_board_uses_country_code() -> None:
    payload = [
        {
            "id": "a",
            "text": "Co-op Developer",
            "categories": {"location": "Hybrid"},
            "country": "CA",
            "descriptionPlain": "An 8-month co-op.",
            "hostedUrl": "https://jobs.lever.co/x/a",
        },
        {"id": "b", "text": "Co-op Developer", "categories": {"location": "Austin"}, "country": "US"},
    ]
    employer = {"id": "x", "board_type": "lever", "board_token": "x"}
    r = cs.measure_board(employer, payload)
    assert (r.total, r.canada, r.canada_student, r.canada_student_with_duration) == (2, 1, 1, 1)


def test_measure_ashby_board_uses_secondary_locations() -> None:
    payload = {
        "jobs": [
            {
                "id": "j1",
                "title": "Machine Learning Intern",
                "location": "San Francisco",
                "secondaryLocations": [{"location": "Toronto"}],
                "descriptionPlain": "Winter 2027",
            },
            {"id": "j2", "title": "Account Executive", "location": "Calgary", "descriptionPlain": ""},
        ]
    }
    employer = {"id": "y", "board_type": "ashby", "board_token": "y"}
    r = cs.measure_board(employer, payload)
    assert (r.total, r.canada, r.canada_student, r.canada_student_with_term) == (2, 2, 1, 1)


def test_summary_skips_failed_boards_and_checks_validity() -> None:
    ok = cs.measure_board({"id": "acme", "board_type": "greenhouse", "board_token": "acme"}, GREENHOUSE)
    failed = cs.BoardResult("gone", "lever", "gone", ok=False, error="HTTP 404")
    s = cs.summarize([ok, failed], "2026-11-02")
    assert (s["boards_ok"], s["boards_failed"], s["canada_student"]) == (1, 1, 1)
    assert s["valid_for_decision"] is False
    report = cs.markdown_report(s, [ok, failed])
    assert "Not valid for the decision" in report
    assert "`gone` (lever/gone): HTTP 404" in report


@pytest.mark.parametrize(
    ("count", "start"), [(150, "100 or more"), (100, "100 or more"), (99, "40 to 99"), (40, "40 to 99"), (39, "Fewer")]
)
def test_decision_boundaries(count: int, start: str) -> None:
    assert cs.decision_for(count).startswith(start)


def test_response_shape_check() -> None:
    assert cs.looks_like_job_list("lever", [])
    assert not cs.looks_like_job_list("lever", {"ok": False})
    assert cs.looks_like_job_list("ashby", {"jobs": []})
    assert not cs.looks_like_job_list("greenhouse", {"status": 404})


def test_seed_list_is_well_formed() -> None:
    employers = cs.load_employers(cs.DEFAULT_EMPLOYERS)
    ids = [e["id"] for e in employers]
    assert len(ids) == len(set(ids)), "duplicate employer ids"
    keys = [(e["board_type"], e["board_token"]) for e in employers]
    assert len(keys) == len(set(keys)), "duplicate boards"
    for e in employers:
        assert e["board_type"] in cs.NORMALIZERS, e["id"]
        assert e["board_token"], e["id"]
        # source, when present, names the outside list the board came from (ADR 0007)
        assert set(e.get("source", [])) <= {"reference-list", "coop-watcher"}, e["id"]
