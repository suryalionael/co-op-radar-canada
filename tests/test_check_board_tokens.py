"""Tests for the keep/drop reasons in scripts/check_board_tokens.py --pairs. No network: checkers are replaced."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import check_board_tokens as cbt  # noqa: E402


def fake_lever(jobs: list[tuple[str, str]] | None) -> Any:
    def check(token: str) -> dict[str, Any] | None:
        if jobs is None:
            return None
        return {
            "board_name": None,
            "jobs": len(jobs),
            "titles": [t for t, _ in jobs],
            "locations": [loc for _, loc in jobs],
        }

    return check


@pytest.mark.parametrize(
    ("jobs", "decision", "reason"),
    [
        (None, "drop", "board not found on lever"),
        ([], "drop", "board has no jobs"),
        ([("Engineer", "Austin, TX")], "drop", "no job located in Canada or remote-Canada"),
        ([("Data Co-op", "Remote - Canada"), ("Engineer", "Austin, TX")], "keep", "1 job(s) in Canada"),
    ],
)
def test_check_pair_reasons(
    monkeypatch: pytest.MonkeyPatch, jobs: list[tuple[str, str]] | None, decision: str, reason: str
) -> None:
    monkeypatch.setitem(cbt.CHECKERS, "lever", fake_lever(jobs))
    row = cbt.check_pair("lever", "invented-co")
    assert (row["decision"], row["reason"]) == (decision, reason)


def test_unknown_token_is_not_checked() -> None:
    row = cbt.check_pair("greenhouse", "")
    assert row["decision"] == "drop"
    assert row["reason"].startswith("token unknown")
