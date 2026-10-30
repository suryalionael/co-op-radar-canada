"""Tests for the rule-based extractors. Text is written in the style of real postings."""

from __future__ import annotations

import datetime as dt

import pytest

from pipeline.extract.duration import extract_duration, find_stated
from pipeline.extract.province import extract_location
from pipeline.extract.role_type import extract_role_type
from pipeline.extract.student import is_student_role
from pipeline.extract.term import extract_term, term_end_date, term_in_past
from pipeline.extract.track import extract_track
from pipeline.models import DurationStatus, Province, Remote, RoleType, Track

# --- Term -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("title", "description", "terms"),
    [
        ("Software Developer Co-op (Summer 2027)", "", ["Summer 2027"]),
        ("Data Intern", "This is a Fall term 2026 opportunity.", ["Fall 2026"]),
        ("Intern", "Join us for Winter '27!", ["Winter 2027"]),
        ("Intern", "Our 2027 Summer cohort starts soon.", ["Summer 2027"]),
        ("Stagiaire", "Stage d'été 2027 à Montréal", ["Summer 2027"]),
        ("Co-op", "Available terms: Summer 2027 or Fall 2027.", ["Summer 2027", "Fall 2027"]),
        ("Intern", "We hire summer interns every year.", []),
        ("Intern", "", []),
    ],
)
def test_terms(title: str, description: str, terms: list[str]) -> None:
    assert extract_term(title, description).terms == terms


@pytest.mark.parametrize(
    ("title", "description", "terms"),
    [
        # Start months map to the school calendar: Jan–Apr Winter, May–Aug Summer, Sep–Dec Fall.
        ("May 2027 GIS Co-op", "", ["Summer 2027"]),
        ("Co-op Student", "The co-op starts May 2027.", ["Summer 2027"]),
        ("Co-op Student", "Starting May 2027, you will join the team.", ["Summer 2027"]),
        ("Intern", "This work term runs January–April 2027.", ["Winter 2027"]),
        ("Co-op (Jan 2027)", "", ["Winter 2027"]),
        ("Intern (Winter/January 2027, 8 Months)", "", ["Winter 2027"]),
        ("Developer Co-op", "Our September 2027 co-op cohort.", ["Fall 2027"]),
        ("Co-op Student", "Placement: December 2027.", ["Fall 2027"]),
        # A month and year in the description that is a deadline or a date, not a term.
        ("Co-op Student", "Please apply by May 2027.", []),
        ("Co-op Student", "Applications close January 2027 for this co-op.", []),
        ("Intern", "Open to students graduating in May 2027.", []),
        ("Analyst", "Our office opened in May 2019.", []),
    ],
)
def test_month_and_year_terms(title: str, description: str, terms: list[str]) -> None:
    assert extract_term(title, description).terms == terms


def test_spring_is_ambiguous_and_not_mapped() -> None:
    r = extract_term("Software Intern (Spring 2027)", "")
    assert r.terms == [] and r.term is None
    assert r.status == "ambiguous"
    assert r.ambiguous == ["Spring 2027"]


def test_spring_beside_a_clear_term() -> None:
    r = extract_term("Co-op, Spring 2027", "Also open for Summer 2027.")
    assert r.terms == ["Summer 2027"]
    assert r.status == "stated"
    assert r.ambiguous == ["Spring 2027"]


def test_term_end_dates() -> None:
    assert term_end_date("Winter 2026") == dt.date(2026, 4, 30)
    assert term_end_date("Summer 2027") == dt.date(2027, 8, 31)
    assert term_end_date("Fall 2027") == dt.date(2027, 12, 31)
    assert term_end_date("Spring 2027") is None


def test_term_in_past_flag() -> None:
    october = dt.date(2026, 10, 15)
    assert term_in_past(["Winter 2026"], None, october)  # stated term ended before it was posted
    assert not term_in_past(["Winter 2027"], None, october)
    assert not term_in_past(["Fall 2026"], None, october)  # still running
    assert not term_in_past(["Winter 2026", "Winter 2027"], None, october)  # one option is still ahead
    assert not term_in_past([], None, october)
    assert not term_in_past(["Winter 2026"], None, None)


def test_title_term_comes_first() -> None:
    r = extract_term("Co-op, Fall 2027", "Our Summer 2027 cohort is full.")
    assert r.term == "Fall 2027"
    assert r.terms == ["Fall 2027", "Summer 2027"]
    assert r.evidence == "Fall 2027"


def test_month_range_gives_term_and_dates() -> None:
    r = extract_term("Co-op Student", "The work term runs May–August 2027.")
    assert r.term == "Summer 2027"
    assert (r.start, r.end) == (dt.date(2027, 5, 1), dt.date(2027, 8, 31))
    assert r.dates_evidence == "May–August 2027"


def test_month_range_across_years() -> None:
    r = extract_term("Intern", "From September 2026 to April 2027, you will...")
    assert r.term == "Fall 2026"
    assert (r.start, r.end) == (dt.date(2026, 9, 1), dt.date(2027, 4, 30))


def test_month_range_with_implied_first_year() -> None:
    r = extract_term("Intern", "Term: September - April 2027")
    assert r.start == dt.date(2026, 9, 1)


def test_start_month() -> None:
    r = extract_term("Intern", "Start date: January 2027")
    assert r.term == "Winter 2027"
    assert r.start == dt.date(2027, 1, 1)
    assert r.end is None
    assert extract_term("Intern", "This is a May 2027 start.").term == "Summer 2027"


# --- Duration -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "options"),
    [
        ("This is a 4-month co-op position.", [4.0]),
        ("We offer 4, 8 or 12-month terms.", [4.0, 8.0, 12.0]),
        ("Co-op terms are 4 or 8 months long.", [4.0, 8.0]),
        ("The internship runs for 16 weeks.", [4.0]),
        ("A twelve-month internship in our data team.", [12.0]),
        ("Duration: 8 months", [8.0]),
        ("Length of term: 4 months (May to August)", [4.0]),
        ("Stage de 4 mois à Montréal", [4.0]),
        ("This 12 week internship pays well.", [3.0]),
        ("Work term: 4/8 months", [4.0, 8.0]),
    ],
)
def test_stated_durations(text: str, options: list[float]) -> None:
    assert sorted(set(find_stated(text)[0])) == options


@pytest.mark.parametrize(
    "text",
    [
        "6+ months of experience with Python.",
        "You have 6 months of experience in a co-op role.",
        "Interns get 2 weeks of vacation.",
        "Co-op students complete a 2-week onboarding program.",
        "Applications are reviewed within 3 months of the posting date.",
        "The role includes a 3-month probation period.",
        "Must have at least 4 months remaining in your program.",
        "We were founded 18 months ago.",
        "12 months of parental leave for every employee.",
        "Our team shipped 3 products in 6 months.",
        "Salary review every 6 months.",
    ],
)
def test_not_a_duration(text: str) -> None:
    assert find_stated(text)[0] == []


def test_duration_status_stated_keeps_evidence() -> None:
    r = extract_duration("Data Co-op (4 months)", "Join our 4-month co-op.")
    assert r.status is DurationStatus.stated
    assert r.options_months == [4.0]
    assert r.evidence == "4 months | 4-month"


def test_duration_inferred_from_dates() -> None:
    r = extract_duration("Co-op", "", dt.date(2027, 5, 1), dt.date(2027, 8, 31), "May–August 2027")
    assert (r.status, r.options_months, r.evidence) == (DurationStatus.inferred_from_dates, [4.0], "May–August 2027")


def test_stated_beats_dates() -> None:
    r = extract_duration("Co-op", "An 8-month co-op.", dt.date(2027, 5, 1), dt.date(2027, 8, 31))
    assert (r.status, r.options_months) == (DurationStatus.stated, [8.0])


def test_duration_not_stated() -> None:
    r = extract_duration("Software Intern", "Great team, great perks.")
    assert (r.status, r.options_months, r.evidence) == (DurationStatus.not_stated, [], None)


@pytest.mark.parametrize(
    ("text", "months", "is_range"),
    [
        ("This is a 4 months co-op.", [4.0], False),
        ("An 8-month co-op term.", [8.0], False),
        ("A 16months co-op placement.", [16.0], False),
        ("Internship length: 12 Months.", [12.0], False),
        ("Data Analyst Intern (8–12 months)", [8.0, 12.0], True),
        ("Co-op term of 8 to 12 months.", [8.0, 12.0], True),
        ("Co-op terms of 4 or 8 months.", [4.0, 8.0], False),
        ("Co-op terms of 4, 8 or 12 months.", [4.0, 8.0, 12.0], False),
    ],
)
def test_duration_patterns_and_ranges(text: str, months: list[float], is_range: bool) -> None:
    r = extract_duration(text, "")
    assert (r.options_months, r.status, r.is_range) == (months, DurationStatus.stated, is_range)


# --- Location and remote --------------------------------------------------------


@pytest.mark.parametrize(
    ("location", "in_canada", "provinces"),
    [
        ("Toronto, ON", True, [Province.ON]),
        ("Toronto, Ontario, Canada", True, [Province.ON]),
        ("Vancouver / Toronto", True, [Province.BC, Province.ON]),
        ("Montréal, QC / New York", True, [Province.QC]),
        ("North Vancouver, BC", True, [Province.BC]),
        ("Quebec City", True, [Province.QC]),
        ("London, ON", True, [Province.ON]),
        ("London, UK", False, []),
        ("Remote - Canada", True, [Province.REMOTE_CA]),
        ("Remote - Ontario", True, [Province.ON]),
        ("Canada", True, []),
        ("Remote", False, []),
        ("San Francisco, CA", False, []),
    ],
)
def test_location(location: str, in_canada: bool, provinces: list[Province]) -> None:
    r = extract_location(location)
    assert (r.in_canada, r.provinces) == (in_canada, provinces)


def test_province_is_first_or_unknown() -> None:
    assert extract_location("Calgary / Edmonton").province is Province.AB
    assert extract_location("Canada").province is Province.UNKNOWN


@pytest.mark.parametrize(
    ("location", "hint", "remote"),
    [
        ("Remote - Canada", "", Remote.remote),
        ("Toronto, ON (Hybrid)", "", Remote.hybrid),
        ("Toronto, ON", "Hybrid", Remote.hybrid),
        ("Toronto, ON", "On-site", Remote.onsite),
        ("Toronto, ON", "", Remote.unknown),
    ],
)
def test_remote(location: str, hint: str, remote: Remote) -> None:
    assert extract_location(location, hint).remote is remote


# --- Track and student role -----------------------------------------------------


@pytest.mark.parametrize(
    ("title", "track"),
    [
        ("Machine Learning Engineer Intern", Track.ml_ai),
        ("AI Research Intern", Track.ml_ai),
        ("Data Engineering Co-op", Track.data_eng),
        ("Data Scientist Intern", Track.data_science),
        ("Data Analyst Co-op", Track.data_analytics),
        ("Business Intelligence Intern", Track.data_analytics),
        ("Software Developer Co-op", Track.software),
        ("Backend Engineering Intern", Track.software),
        ("Mechanical Engineering Intern", Track.other),
        ("Marketing Co-op", Track.business_ops),
        ("Finance Intern", Track.business_ops),
    ],
)
def test_track_from_title(title: str, track: Track) -> None:
    assert extract_track(title, "")[0] is track


def test_track_falls_back_to_description() -> None:
    description = "You will build data pipelines and ETL jobs. Experience with ETL tools is a plus."
    assert extract_track("Co-op Student, Summer 2027", description)[0] is Track.data_eng
    assert extract_track("Co-op Student", "One mention of software.")[0] is Track.other


@pytest.mark.parametrize(
    ("title", "student"),
    [
        ("Software Engineering Intern", True),
        ("Co-op Developer", True),
        ("Summer Student - Operations", True),
        ("Summer Analyst", True),
        ("Stagiaire en données", True),
        ("Internal Tools Engineer", False),
        ("Senior Software Engineer", False),
        ("Summer Campaign Manager", False),
    ],
)
def test_student_role(title: str, student: bool) -> None:
    assert is_student_role(title)[0] is student


# --- Role type (ADR 0008) --------------------------------------------------------


@pytest.mark.parametrize(
    ("title", "employment_type", "role_type"),
    [
        # Regression cases: substring matching would call these student roles.
        ("Internal Audit Analyst", None, RoleType.none),
        ("International Payments Analyst", None, RoleType.none),
        ("Cooperative Housing Coordinator", None, RoleType.none),
        ("Early Stage Investment Associate", None, RoleType.none),
        ("Student Success Manager", None, RoleType.none),
        ("Manager, Services for Students", None, RoleType.none),
        # Real student titles still match.
        ("Data Science Intern", "", RoleType.intern),
        ("Data Science Intern", None, RoleType.intern),
        ("Software Developer (Co-op Opportunities)", None, RoleType.coop),
        ("Internal Communications Co-op", None, RoleType.coop),
        ("Coop Software Developer", None, RoleType.coop),
        ("Engineering Interns", None, RoleType.intern),
        ("Stage en développement logiciel", None, RoleType.intern),
        ("Summer Student - Operations", None, RoleType.student),
        ("Student, IT Support", None, RoleType.student),
        # The structured employment type is the first signal.
        ("Data Analyst", "Coop Student", RoleType.coop),
        ("Platform Engineer", "Intern", RoleType.intern),
        ("Analyst", "Intern/Student", RoleType.intern),
        ("Analyst", "Student", RoleType.student),
        ("Software Engineering Intern", "Full-time", RoleType.intern),  # a default "Full-time" is no signal
        ("Senior Engineer", "FullTime", RoleType.none),
        # Ashby's fixed list has no co-op value, so a co-op title refines "Intern".
        ("Software Engineer, Backend (Co-op)", "Intern", RoleType.coop),
    ],
)
def test_role_type(title: str, employment_type: str | None, role_type: RoleType) -> None:
    assert extract_role_type(title, "", employment_type).role_type is role_type


def test_role_type_records_the_field_that_matched() -> None:
    structured = extract_role_type("Data Analyst", "", "Coop Student")
    assert (structured.field, structured.evidence) == ("employment_type", "Coop")
    titled = extract_role_type("Data Science Intern", "", "")
    assert (titled.field, titled.evidence) == ("title", "Intern")


def test_description_only_refines_a_student_role() -> None:
    co_op = "This is a 4-month co-op work term."
    refined = extract_role_type("Summer Student, Engineering", co_op)
    assert (refined.role_type, refined.field, refined.evidence) == (RoleType.coop, "description", "co-op")
    # A senior role that mentions the co-op program is not a student role.
    assert (
        extract_role_type("Senior Software Engineer", "You will mentor our co-op students.").role_type is RoleType.none
    )
    # An intern title is not overridden by the description.
    assert extract_role_type("Data Intern", "Open to co-op students.").role_type is RoleType.intern


# --- Evidence quotes ------------------------------------------------------------


def test_quote_context_cuts_at_words() -> None:
    from pipeline.extract import quote_context

    text = "We are a growing fintech in Toronto. This is a 4-month co-op on our analytics team, starting in May."
    quote = quote_context("4-month", text, width=20)
    assert quote == "…Toronto. This is a 4-month co-op on our…"
    assert quote_context("4-month", "A 4-month co-op") == "A 4-month co-op"
    assert quote_context("missing", text) is None


def test_extract_posting_adds_contexts() -> None:
    from pipeline.extract import extract_posting
    from pipeline.models import RawPosting, Source

    raw = RawPosting(
        source=Source.greenhouse, board_token="a", employer_id="a", source_job_id="1",
        title="Data Co-op (Summer 2027)", url="u", location_raw="Toronto, ON",
    )  # fmt: skip
    fields = extract_posting(raw, "<p>This is a 4-month co-op on our analytics team.</p>")
    assert fields["evidence"]["term_context"] == "Data Co-op (Summer 2027)"
    assert fields["evidence"]["duration_context"] == "This is a 4-month co-op on our analytics team."
