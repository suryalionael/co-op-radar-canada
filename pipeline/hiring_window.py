"""When does a company usually hire students? Built from the dates its postings appeared.

The window is the shortest run of consecutive months (wrapping across December)
holding at least 60% of the dates. Fewer than 3 dates give no window: one or two
postings say nothing about a pattern.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Literal

MIN_DATES = 3
SHARE = 0.6
SOON_MONTHS = 2

Badge = Literal["open", "soon", "quiet"]


def hiring_window(dates: list[dt.date]) -> dict[str, Any] | None:
    if len(dates) < MIN_DATES:
        return None
    months = [0] * 12
    for d in dates:
        months[d.month - 1] += 1
    need = SHARE * len(dates)
    for length in range(1, 13):
        runs = [(sum(months[(s + i) % 12] for i in range(length)), s) for s in range(12)]
        best, start = max(runs, key=lambda r: (r[0], -r[1]))
        if best >= need:
            return {
                "months": months,
                "start": start + 1,
                "end": (start + length - 1) % 12 + 1,
                "n_dates": len(dates),
                "years": [min(d.year for d in dates), max(d.year for d in dates)],
                "source": "postings",
            }
    raise AssertionError("unreachable: twelve months hold every date")


def researched_window(months: list[int]) -> dict[str, Any]:
    """A window from months someone looked up by hand (config/companies.csv `hiring_months`).

    There are no counts behind it, so each listed month is flagged 1. `start` and `end` are the
    first and last month as written ("Nov-Jan" gives 11 and 1), which is what `badge` needs.
    """
    return {
        "months": [1 if m in months else 0 for m in range(1, 13)],
        "start": months[0],
        "end": months[-1],
        "n_dates": 0,
        "years": [0, 0],
        "source": "researched",
    }


def badge(window: dict[str, Any] | None, open_count: int, today: dt.date) -> Badge:
    if open_count > 0:
        return "open"
    if window and 1 <= (window["start"] - today.month) % 12 <= SOON_MONTHS:
        return "soon"
    return "quiet"
