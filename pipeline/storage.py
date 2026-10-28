"""Raw snapshot storage on the orphan `data` branch (ADR 0002).

Layout under the data root (a checkout of the `data` branch):

    raw/postings/YYYY-MM-DD.jsonl.gz      one line per posting kept that day, no description
    raw/boards/YYYY-MM-DD.json            one entry per board fetch: ok or failed, job counts
    raw/descriptions/{hash}.html.gz       each distinct description, written once
    raw/programs/YYYY-MM-DD.jsonl.gz      program-watch page text, one line per page

Files are written deterministically (sorted lines, sorted keys, gzip mtime 0),
so re-running a day with the same input produces byte-identical files.
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from pipeline.models import BoardFetch, RawPosting


def _dumps(record: Any) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, default=str)


def _write_gz(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(data, mtime=0))


def _sort_key(p: RawPosting) -> tuple[str, str, str]:
    return (p.source, p.board_token, p.source_job_id)


def write_postings_day(
    root: Path, day: dt.date, boards: list[BoardFetch], postings: list[RawPosting]
) -> dict[str, int]:
    """Write one day's posting snapshot and any new descriptions. Returns byte counts."""
    lines = [_dumps(p.model_dump(mode="json")) for p in sorted(postings, key=_sort_key)]
    _write_gz(root / "raw" / "postings" / f"{day}.jsonl.gz", ("\n".join(lines) + "\n").encode() if lines else b"")

    board_records = sorted((b.model_dump(mode="json") for b in boards), key=lambda b: (b["source"], b["board_token"]))
    boards_path = root / "raw" / "boards" / f"{day}.json"
    boards_path.parent.mkdir(parents=True, exist_ok=True)
    boards_path.write_text(json.dumps(board_records, ensure_ascii=False, indent=1, sort_keys=True) + "\n")

    new_description_bytes = 0
    for p in postings:
        path = description_path(root, p.description_hash)
        if not path.exists():
            _write_gz(path, p.description_html.encode())
            new_description_bytes += path.stat().st_size
    return {
        "postings_gz_bytes": (root / "raw" / "postings" / f"{day}.jsonl.gz").stat().st_size,
        "new_description_gz_bytes": new_description_bytes,
    }


def description_path(root: Path, description_hash: str) -> Path:
    return root / "raw" / "descriptions" / f"{description_hash}.html.gz"


def read_description(root: Path, description_hash: str) -> str:
    path = description_path(root, description_hash)
    return gzip.decompress(path.read_bytes()).decode() if path.exists() else ""


def posting_days(root: Path) -> list[dt.date]:
    """Every day that has a board-status file, oldest first."""
    return sorted(dt.date.fromisoformat(p.stem) for p in (root / "raw" / "boards").glob("*.json"))


def read_postings_day(root: Path, day: dt.date) -> tuple[list[BoardFetch], list[RawPosting]]:
    boards_path = root / "raw" / "boards" / f"{day}.json"
    boards = [BoardFetch.model_validate(b) for b in json.loads(boards_path.read_text())]
    path = root / "raw" / "postings" / f"{day}.jsonl.gz"
    postings = []
    if path.exists():
        for line in gzip.decompress(path.read_bytes()).decode().splitlines():
            if line.strip():
                postings.append(RawPosting.model_validate_json(line))
    return boards, postings


def write_programs_day(root: Path, day: dt.date, records: list[dict[str, Any]]) -> None:
    lines = [_dumps(r) for r in sorted(records, key=lambda r: str(r["program_id"]))]
    _write_gz(root / "raw" / "programs" / f"{day}.jsonl.gz", ("\n".join(lines) + "\n").encode() if lines else b"")


def iter_programs_days(root: Path) -> Iterator[tuple[dt.date, list[dict[str, Any]]]]:
    for path in sorted((root / "raw" / "programs").glob("*.jsonl.gz")):
        day = dt.date.fromisoformat(path.name.removesuffix(".jsonl.gz"))
        lines = gzip.decompress(path.read_bytes()).decode().splitlines()
        yield day, [json.loads(line) for line in lines if line.strip()]
