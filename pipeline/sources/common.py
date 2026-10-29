"""Helpers shared by the source parsers."""

from __future__ import annotations

from typing import Any


def join_locations(parts: list[Any]) -> str:
    """Join every location field into one string, dropping blanks and repeats."""
    seen: list[str] = []
    for p in parts:
        p = (p or "").strip() if isinstance(p, str) else ""
        if p and p not in seen:
            seen.append(p)
    return " / ".join(seen)


def without(record: dict[str, Any], *keys: str) -> dict[str, Any]:
    return {k: v for k, v in record.items() if k not in keys}
