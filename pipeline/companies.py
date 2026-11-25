"""The company list: a spreadsheet the team edits, kept in the repo as config/companies.csv.

The Google Sheet is the source of truth. A daily step downloads it as CSV, checks it,
and writes the committed copy (see `sync_sheet`); everything else reads that copy.
Because the sheet is edited by hand, every cell is validated and a bad sheet is
rejected whole, with a message that names each problem and its sheet row.

Columns (extra columns are ignored):

    id              stable key, lowercase letters, digits, "-" and "_"; never changed once used
    name, sector    shown on the site
    show            "yes" or "no" (blank means yes); "no" hides the company and its postings
    website, careers_url
                    optional https links
    board_type, board_token
                    greenhouse, lever or ashby, and the board's token; blank means no postings feed
    hq_province     optional
    hiring_months   researched months, e.g. "Sep-Oct", "9,10", "Nov-Jan" (wraps the year)
    hiring_note, hiring_source
                    where the hiring months came from, shown with them
    notes           internal; never published
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from typing import Any

COLUMNS = [
    "id",
    "name",
    "sector",
    "show",
    "website",
    "careers_url",
    "board_type",
    "board_token",
    "hq_province",
    "hiring_months",
    "hiring_note",
    "hiring_source",
    "notes",
]
BOARD_TYPES = {"greenhouse", "lever", "ashby"}
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
MONTH_NAMES = {
    name: i + 1
    for i, name in enumerate(
        [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ]
    )
}
MONTH_ALIASES = {name[:3]: n for name, n in MONTH_NAMES.items()} | {"sept": 9}


class SheetError(ValueError):
    """The sheet is not usable. `problems` lists every reason, each naming its row."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("; ".join(problems))


def _month(token: str) -> int:
    t = token.strip().lower().rstrip(".")
    if t.isdigit() and 1 <= int(t) <= 12:
        return int(t)
    if t in MONTH_NAMES:
        return MONTH_NAMES[t]
    if t in MONTH_ALIASES:
        return MONTH_ALIASES[t]
    raise ValueError(f"not a month: {token.strip()!r}")


def parse_hiring_months(text: str) -> list[int]:
    """Month numbers in order, e.g. "Sep-Oct" -> [9, 10]; "Nov-Jan" -> [11, 12, 1]; "" -> []."""
    text = text.strip()
    if not text:
        return []
    months: list[int] = []
    for part in text.split(","):
        ends = re.split(r"\s*(?:-|–|—|\bto\b)\s*", part.strip(), maxsplit=1, flags=re.IGNORECASE)
        if len(ends) == 2:
            start, end = _month(ends[0]), _month(ends[1])
            run = [(start - 1 + i) % 12 + 1 for i in range(((end - start) % 12) + 1)]
        else:
            run = [_month(ends[0])]
        months += [m for m in run if m not in months]
    return months


def parse_companies(csv_text: str) -> list[dict[str, str]]:
    """Validate a sheet exported as CSV and return its rows. Raises SheetError listing every problem."""
    if not csv_text.strip():
        raise SheetError(["the sheet is empty"])
    reader = csv.DictReader(io.StringIO(csv_text.lstrip("﻿")))
    missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise SheetError([f"missing columns: {', '.join(missing)}"])

    rows: list[dict[str, str]] = []
    problems: list[str] = []
    seen: dict[str, int] = {}
    for number, raw in enumerate(reader, start=2):  # the header is sheet row 1
        row = {c: (raw.get(c) or "").strip() for c in COLUMNS}
        if not any(row.values()):
            continue
        row["show"] = (row["show"] or "yes").lower()
        row["board_type"] = row["board_type"].lower()

        def bad(column: str, why: str, number: int = number) -> None:
            problems.append(f"row {number}: {column} {why}")

        if not ID_PATTERN.match(row["id"]):
            bad("id", f"must be lowercase letters, digits, - or _ (got {row['id']!r})")
        elif row["id"] in seen:
            problems.append(f"row {number}: duplicate id {row['id']!r} (also row {seen[row['id']]})")
        else:
            seen[row["id"]] = number
        if not row["name"]:
            bad("name", "is empty")
        if row["show"] not in {"yes", "no"}:
            bad("show", f"must be yes or no (got {row['show']!r})")
        if row["board_type"] and row["board_type"] not in BOARD_TYPES:
            bad("board_type", f"must be one of {', '.join(sorted(BOARD_TYPES))} (got {row['board_type']!r})")
        if row["board_type"] and not row["board_token"]:
            bad("board_token", "is required when board_type is set")
        for column in ("website", "careers_url"):
            if row[column] and not row[column].lower().startswith("https://"):
                bad(column, f"must start with https:// (got {row[column]!r})")
        try:
            parse_hiring_months(row["hiring_months"])
        except ValueError as err:
            bad("hiring_months", f"has a bad month ({err})")
        rows.append(row)

    if problems:
        raise SheetError(problems)
    if not rows:
        raise SheetError(["the sheet has no companies"])
    return rows


def load_companies(path: Path) -> list[dict[str, str]]:
    return parse_companies(path.read_text(encoding="utf-8"))


def load_employers(path: Path, include_hidden: bool = False) -> list[dict[str, Any]]:
    """Companies that have a job board, shaped like the old config/employers.yaml entries."""
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "sector": r["sector"] or None,
            "board_type": r["board_type"],
            "board_token": r["board_token"],
            "hq_province": r["hq_province"] or None,
        }
        for r in load_companies(path)
        if r["board_type"] and (include_hidden or r["show"] == "yes")
    ]
