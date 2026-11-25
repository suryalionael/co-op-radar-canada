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
        (row(board_type="lever", board_token="a/../b"), "board_token"),
        (row(board_type="lever", board_token="a?b=c"), "board_token"),
        (row(board_type="lever", board_token=".."), "board_token"),
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


# --- sync from the sheet -------------------------------------------------------------------

from pipeline.companies import sync_sheet  # noqa: E402


def many(n: int, prefix: str = "c") -> str:
    return sheet(*[row(id=f"{prefix}{i}", name=f"Company {i}") for i in range(n)])


def test_good_sheet_replaces_the_committed_copy(tmp_path: Path) -> None:
    committed = tmp_path / "companies.csv"
    result = sync_sheet(lambda: many(3), committed)
    assert (result.ok, result.rows, result.changed, result.reason) == (True, 3, True, None)
    assert [c["id"] for c in load_companies(committed)] == ["c0", "c1", "c2"]


def test_identical_content_reports_unchanged(tmp_path: Path) -> None:
    committed = tmp_path / "companies.csv"
    sync_sheet(lambda: many(3), committed)
    before = committed.read_bytes()
    again = sync_sheet(lambda: many(3).replace("\n", "\r\n"), committed)  # same data, other line endings
    assert (again.ok, again.changed) == (True, False)
    assert committed.read_bytes() == before


def test_failed_download_keeps_the_last_good_copy(tmp_path: Path) -> None:
    committed = tmp_path / "companies.csv"
    sync_sheet(lambda: many(3), committed)
    before = committed.read_bytes()

    def boom() -> str:
        raise OSError("connection reset")

    result = sync_sheet(boom, committed)
    assert not result.ok and "connection reset" in (result.reason or "")
    assert committed.read_bytes() == before


def test_invalid_sheet_is_rejected_and_names_the_row(tmp_path: Path) -> None:
    committed = tmp_path / "companies.csv"
    sync_sheet(lambda: many(3), committed)
    before = committed.read_bytes()
    result = sync_sheet(lambda: sheet(row(), row(name="Other")), committed)  # duplicate id
    assert not result.ok and "row 3" in (result.reason or "")
    assert committed.read_bytes() == before


def test_a_sheet_that_lost_half_its_rows_is_refused(tmp_path: Path) -> None:
    committed = tmp_path / "companies.csv"
    sync_sheet(lambda: many(20), committed)
    before = committed.read_bytes()
    refused = sync_sheet(lambda: many(9), committed)
    assert not refused.ok and "20" in (refused.reason or "") and "9" in (refused.reason or "")
    assert committed.read_bytes() == before
    assert sync_sheet(lambda: many(10), committed).ok  # exactly half is allowed


def test_empty_or_html_body_is_rejected(tmp_path: Path) -> None:
    committed = tmp_path / "companies.csv"
    assert not sync_sheet(lambda: "", committed).ok
    assert not sync_sheet(lambda: "<!doctype html><html>Sign in</html>", committed).ok
    assert not committed.exists()


def test_first_sync_accepts_any_valid_sheet(tmp_path: Path) -> None:
    assert sync_sheet(lambda: many(1), tmp_path / "new" / "companies.csv").ok


def test_committed_companies_csv_covers_the_old_lists() -> None:
    import yaml

    root = Path(__file__).resolve().parent.parent
    rows = load_companies(root / "config" / "companies.csv")
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids))
    assert len(load_employers(root / "config" / "companies.csv")) == 171
    programs = yaml.safe_load((root / "config" / "programs.yaml").read_text())["programs"]
    assert {p["employer_id"] for p in programs} <= set(ids)  # every program employer is a company
    assert all(r["show"] == "yes" for r in rows)


def test_a_sheet_that_lost_its_boards_is_refused(tmp_path: Path) -> None:
    committed = tmp_path / "companies.csv"
    with_boards = sheet(*[row(id=f"c{i}", name=f"C{i}", board_type="lever", board_token=f"t{i}") for i in range(20)])
    sync_sheet(lambda: with_boards, committed)
    before = committed.read_bytes()
    # every row still valid and the count unchanged, but the board columns were pasted over
    blanked = sheet(*[row(id=f"c{i}", name=f"C{i}", board_type="", board_token="") for i in range(20)])
    result = sync_sheet(lambda: blanked, committed)
    assert not result.ok and "board" in (result.reason or "")
    assert committed.read_bytes() == before
    half = sheet(
        *[
            row(id=f"c{i}", name=f"C{i}", board_type="lever" if i < 10 else "", board_token=f"t{i}" if i < 10 else "")
            for i in range(20)
        ]
    )
    assert sync_sheet(lambda: half, committed).ok  # exactly half the boards is allowed
