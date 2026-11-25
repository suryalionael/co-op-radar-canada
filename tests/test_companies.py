"""The company list comes from a spreadsheet anyone on the team can edit, so every cell is checked."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.companies import COLUMNS, SheetError, load_companies, load_employers, parse_companies, parse_hiring_months

HEADER = ",".join(COLUMNS)


def sheet(*rows: str, header: str = HEADER) -> str:
    return "\n".join([header, *rows]) + "\n"


def row(**cells: str) -> str:
    base = dict.fromkeys(COLUMNS, "")
    base |= {"id": "acme", "name": "Acme", "show": "yes"} | cells
    return ",".join(f'"{base[c]}"' for c in COLUMNS)


@pytest.mark.parametrize(
    ("text", "months"),
    [
        ("", []),
        ("Sep-Oct", [9, 10]),
        ("Sep to Oct", [9, 10]),
        ("September–October", [9, 10]),
        ("9,10", [9, 10]),
        ("Sept", [9]),
        ("Nov-Jan", [11, 12, 1]),
        ("Sep, Nov", [9, 11]),
        ("jan", [1]),
        ("10-9", [10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
    ],
)
def test_parse_hiring_months(text: str, months: list[int]) -> None:
    assert parse_hiring_months(text) == months


@pytest.mark.parametrize("text", ["banana", "13", "0", "Sep-", "Sep-Foo", "2026"])
def test_unparseable_months_raise(text: str) -> None:
    with pytest.raises(ValueError, match="month"):
        parse_hiring_months(text)


def test_good_sheet_parses() -> None:
    rows = parse_companies(sheet(row(), row(id="b", name="B", show="", board_type="Lever", board_token="b-co")))
    assert [r["id"] for r in rows] == ["acme", "b"]
    assert rows[1]["show"] == "yes"  # blank means yes
    assert rows[1]["board_type"] == "lever"  # lower-cased


def test_bom_crlf_and_extra_columns_are_accepted() -> None:
    text = "﻿" + sheet(row(), header=HEADER + ",extra").replace("\n", "\r\n")
    # an extra header with no cell in the data row is still fine
    assert [r["id"] for r in parse_companies(text)] == ["acme"]


def test_formula_like_cell_stays_plain_text() -> None:
    assert parse_companies(sheet(row(name="=1+1")))[0]["name"] == "=1+1"


def test_blank_rows_are_skipped() -> None:
    assert [r["id"] for r in parse_companies(sheet(row(), ",".join([""] * len(COLUMNS)), row(id="b", name="B")))] == [
        "acme",
        "b",
    ]


@pytest.mark.parametrize(
    ("bad_row", "message"),
    [
        (row(id=""), "id"),
        (row(id="Has Space"), "id"),
        (row(name=""), "name"),
        (row(show="maybe"), "show"),
        (row(board_type="workday", board_token="x"), "board_type"),
        (row(board_type="lever", board_token=""), "board_token"),
        (row(website="http://acme.com"), "website"),
        (row(careers_url="javascript:alert(1)"), "careers_url"),
        (row(hiring_months="banana"), "hiring_months"),
    ],
)
def test_bad_cells_are_rejected_with_the_row_number(bad_row: str, message: str) -> None:
    with pytest.raises(SheetError) as err:
        parse_companies(sheet(row(id="ok", name="Ok"), bad_row))
    assert any("row 3" in p and message in p for p in err.value.problems), err.value.problems


def test_duplicate_id_names_both_rows() -> None:
    with pytest.raises(SheetError) as err:
        parse_companies(sheet(row(), row(name="Other")))
    assert any("row 3" in p and "row 2" in p and "duplicate" in p for p in err.value.problems)


def test_every_problem_is_reported_at_once() -> None:
    with pytest.raises(SheetError) as err:
        parse_companies(sheet(row(show="maybe"), row(id="b", name="", website="http://x")))
    assert len(err.value.problems) == 3


def test_missing_columns_and_empty_sheets_are_rejected() -> None:
    with pytest.raises(SheetError, match="columns"):
        parse_companies("id,name\nacme,Acme\n")
    with pytest.raises(SheetError, match="no companies"):
        parse_companies(HEADER + "\n")
    with pytest.raises(SheetError, match="empty"):
        parse_companies("")


def test_load_employers_shapes_rows_and_hides(tmp_path: Path) -> None:
    path = tmp_path / "companies.csv"
    path.write_text(
        sheet(
            row(id="a", name="A", sector="fintech", board_type="lever", board_token="a-co", hq_province="ON"),
            row(id="b", name="B"),  # no board
            row(id="c", name="C", show="no", board_type="ashby", board_token="c-co"),
        ),
        encoding="utf-8",
    )
    assert load_employers(path) == [
        {"id": "a", "name": "A", "sector": "fintech", "board_type": "lever", "board_token": "a-co", "hq_province": "ON"}
    ]
    assert [e["id"] for e in load_employers(path, include_hidden=True)] == ["a", "c"]
    assert [c["id"] for c in load_companies(path)] == ["a", "b", "c"]
