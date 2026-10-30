"""Tests for the curated reference-list parser (ADR 0007).

The fixtures are invented companies and roles in the list's format, never real rows:
the list has no license, so none of its listings are copied into this repository.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pytest

from pipeline.reference_list import classify_url, parse_readme

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import reference_list_coverage as rlc  # noqa: E402

BADGE = "[![Apply](https://img.shields.io/badge/-Apply-blue?style=for-the-badge)]"
GH = "https://job-boards.greenhouse.io/maplewoodrobotics/jobs/1234567"
GH_JID = "https://careers.northernledger.example/jobs?gh_jid=7654321"
LEVER = "https://jobs.lever.co/lakeview/0a1b2c3d-0000-4000-8000-000000000000"

MARKDOWN = f"""# Invented internships

Some intro text | with a pipe that is not a table.

| Company | Role | Location | Apply | Date Posted |
|--------|------|----------|:-----:|--------------|
| Maplewood Robotics | Firmware Intern (Summer 2027) | Waterloo, ON | {BADGE}({GH}) | Oct 27, 2026 |
| ↳ | Data Co-op | Toronto, ON | Closed🔒 | Oct 20, 2026 |
 | Northern Ledger \\| Labs | Software Dev Co-op (Winter 2027) | Remote, Canada | {BADGE}({GH_JID}) | Sep 3, 2026 |
| Lakeview Analytics | Analyst Intern | Montreal, QC | {BADGE}({LEVER}) | Jan 14 |
"""

HTML = """<table>
<tr><th>Company</th><th>Role</th><th>Location</th><th>Apply</th><th>Date Posted</th></tr>
<tr><td><strong>Prairie Systems</strong></td><td>QA Intern (Fall 2027)</td><td>Calgary, AB</td>
<td><a href="https://jobs.ashbyhq.com/prairie/11111111-2222-3333-4444-555555555555"><img src="https://img.shields.io/x"></a></td>
<td>Oct 1, 2026</td></tr>
<tr><td>↳</td><td>Dev Intern</td><td>Calgary, AB</td><td>Closed🔒</td><td>Oct 2, 2026</td></tr>
</table>"""


def test_markdown_rows() -> None:
    rows = parse_readme(MARKDOWN, 2027)
    assert [r.company for r in rows] == [
        "Maplewood Robotics",
        "Maplewood Robotics",  # "↳" resolves to the company above
        "Northern Ledger | Labs",  # escaped pipe inside a cell
        "Lakeview Analytics",
    ]
    assert all(r.season == 2027 for r in rows)


def test_term_in_parentheses() -> None:
    first, second, third, fourth = parse_readme(MARKDOWN, 2027)
    assert first.term == "Summer 2027"
    assert first.role == "Firmware Intern (Summer 2027)"
    assert third.term == "Winter 2027"
    assert second.term is None and fourth.term is None


def test_closed_row_has_no_url() -> None:
    closed = parse_readme(MARKDOWN, 2027)[1]
    assert closed.closed is True
    assert closed.apply_url is None


def test_dates_without_a_year_are_not_guessed() -> None:
    rows = parse_readme(MARKDOWN, 2027)
    assert rows[0].date_posted == dt.date(2026, 10, 27)
    assert rows[3].date_posted_raw == "Jan 14"
    assert rows[3].date_posted is None


def test_html_table() -> None:
    rows = parse_readme(HTML, 2026)
    assert [(r.company, r.term, r.closed) for r in rows] == [
        ("Prairie Systems", "Fall 2027", False),
        ("Prairie Systems", None, True),
    ]
    assert rows[0].apply_url == "https://jobs.ashbyhq.com/prairie/11111111-2222-3333-4444-555555555555"


@pytest.mark.parametrize(
    ("url", "platform", "token", "job_id"),
    [
        ("https://job-boards.greenhouse.io/maplewood/jobs/123", "greenhouse", "maplewood", "123"),
        ("https://boards.greenhouse.io/maplewood/jobs/123?gh_src=x", "greenhouse", "maplewood", "123"),
        ("https://boards.greenhouse.io/embed/job_app?for=maplewood&token=123", "greenhouse", "maplewood", "123"),
        ("https://careers.example.com/open-roles?gh_jid=987", "greenhouse", None, "987"),
        ("https://jobs.lever.co/lakeview/abc-def", "lever", "lakeview", "abc-def"),
        ("https://jobs.ashbyhq.com/prairie/xyz", "ashby", "prairie", "xyz"),
        ("https://example.wd3.myworkdayjobs.com/Careers/job/Toronto/Intern_R1", "workday", None, None),
        ("https://abcd.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/job/1", "oracle", None, None),
        ("https://careers-example.icims.com/jobs/1/intern/job", "icims", None, None),
        ("https://careers.example.com/jobs/1?icims=1", "icims", None, None),
        ("https://example.eightfold.ai/careers?pid=1", "eightfold", None, None),
        ("https://careers.example.com/job?id=1&ats=successfactors", "successfactors", None, None),
        ("https://ats.rippling.com/example/jobs/1", "rippling", None, None),
        ("https://apply.workable.com/example/j/ABC/", "workable", None, None),
        ("https://example.bamboohr.com/careers/12", "bamboohr", None, None),
        ("https://example.applytojob.com/apply/abc", "jazzhr", None, None),
        ("https://example.avature.net/careers/JobDetail/1", "avature", None, None),
        ("https://jobs.example.org/intern", "other", None, None),
        (None, "none", None, None),
    ],
)
def test_classify_url(url: str | None, platform: str, token: str | None, job_id: str | None) -> None:
    p = classify_url(url)
    assert (p.platform, p.token, p.job_id) == (platform, token, job_id)


def test_other_records_host() -> None:
    assert classify_url("https://www.jobs.example.org/intern").host == "jobs.example.org"


def test_breakdown_counts_listings_and_companies() -> None:
    rows = parse_readme(MARKDOWN, 2027)
    by_platform = {r["platform"]: r for r in rlc.platform_breakdown(rows)}
    assert by_platform["all"]["listings"] == 4
    assert by_platform["all"]["companies"] == 3
    assert by_platform["greenhouse"]["listings"] == 2  # one board link, one gh_jid link
    assert by_platform["greenhouse"]["companies"] == 2
    assert by_platform["none"]["listings"] == 1  # the closed row
    assert by_platform["none"]["open_listings"] == 0


def test_candidate_tokens_include_unknown_greenhouse_tokens() -> None:
    rows = parse_readme(MARKDOWN, 2027)
    tokens = rlc.candidate_tokens(
        rows, configured={("lever", "lakeview"), ("greenhouse", "name:northern ledger | labs")}
    )
    assert [(t["platform"], t["token"], t["company"], t["in_employers_yaml"]) for t in tokens] == [
        ("greenhouse", "", "Northern Ledger | Labs", "yes"),  # token unknown, matched by employer name
        ("greenhouse", "maplewoodrobotics", "Maplewood Robotics", "no"),
        ("lever", "lakeview", "Lakeview Analytics", "yes"),
    ]
