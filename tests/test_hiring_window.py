"""A company's hiring window is the shortest run of months holding most of its posting dates."""

from __future__ import annotations

import datetime as dt

from pipeline.hiring_window import badge, hiring_window


def days(*month_counts: tuple[int, int], year: int = 2026) -> list[dt.date]:
    return [dt.date(year, m, 1 + i) for m, n in month_counts for i in range(n)]


def test_too_few_dates_gives_no_window() -> None:
    assert hiring_window(days((9, 2))) is None


def test_window_covers_most_dates() -> None:
    w = hiring_window(days((9, 4), (10, 2), (3, 1)))
    assert w is not None
    assert (w["start"], w["end"], w["n_dates"]) == (9, 10, 7)
    assert w["months"][8] == 4 and len(w["months"]) == 12
    assert w["years"] == [2026, 2026]


def test_window_wraps_new_year() -> None:
    dates = [dt.date(2025, 11, 3), dt.date(2025, 12, 1), dt.date(2025, 12, 8), dt.date(2026, 1, 5), dt.date(2026, 1, 9)]
    w = hiring_window(dates)
    assert w is not None
    assert (w["start"], w["end"]) == (12, 1)
    assert w["years"] == [2025, 2026]


def test_badge() -> None:
    w = hiring_window(days((9, 3)))
    assert badge(None, 3, dt.date(2027, 3, 1)) == "open"
    assert badge(w, 0, dt.date(2027, 7, 15)) == "soon"
    assert badge(w, 0, dt.date(2027, 3, 1)) == "quiet"
    assert badge(None, 0, dt.date(2027, 3, 1)) == "quiet"


def test_researched_window_flags_the_listed_months() -> None:
    from pipeline.hiring_window import researched_window

    w = researched_window([9, 10])
    assert w["months"] == [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0]
    assert (w["start"], w["end"], w["source"], w["n_dates"], w["years"]) == (9, 10, "researched", 0, [0, 0])


def test_researched_window_wraps_the_year() -> None:
    from pipeline.hiring_window import researched_window

    w = researched_window([11, 12, 1])
    assert (w["start"], w["end"]) == (11, 1)
    assert sum(w["months"]) == 3 and w["months"][10] == w["months"][0] == 1


def test_postings_window_says_where_it_came_from() -> None:
    w = hiring_window(days((9, 3)))
    assert w is not None and w["source"] == "postings"
