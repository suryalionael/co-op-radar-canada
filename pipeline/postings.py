"""Build the processed postings table from every raw snapshot, oldest day first.

Processing always starts from scratch, so re-running a day never double-counts
(brief section 4). Open/closed status follows the guard in section 4:

- A board fetch counts as **failed** if it errored, or if it returned zero jobs
  when its last successful fetch had jobs.
- A failed fetch changes nothing for that board's postings.
- After a successful fetch, a posting that was not in it gets one more
  `missed_fetches`; at 2 it is `closed`. A posting that comes back reopens.
"""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from pipeline.extract import extract_posting
from pipeline.models import BoardFetch, Posting, RawPosting, Status
from pipeline.storage import posting_days, read_description, read_postings_day

CLOSE_AFTER_MISSES = 2


@dataclass
class Tracked:
    latest: RawPosting
    first_seen: dt.date
    last_seen: dt.date
    missed_fetches: int = 0

    @property
    def status(self) -> Status:
        return Status.closed if self.missed_fetches >= CLOSE_AFTER_MISSES else Status.open


BoardKey = tuple[str, str]  # (source, board_token)


class PostingLedger:
    """Follows every posting across days. Feed it one day at a time, oldest first."""

    def __init__(self) -> None:
        self.postings: dict[str, Tracked] = {}
        self.last_ok_count: dict[BoardKey, int] = {}

    def fetch_succeeded(self, board: BoardFetch) -> bool:
        if not board.ok:
            return False
        previous = self.last_ok_count.get((board.source, board.board_token), 0)
        return not (board.job_count == 0 and previous > 0)

    def apply_day(self, day: dt.date, boards: list[BoardFetch], postings: list[RawPosting]) -> None:
        by_board: dict[BoardKey, list[RawPosting]] = {}
        for p in postings:
            by_board.setdefault((p.source, p.board_token), []).append(p)

        for board in boards:
            key: BoardKey = (board.source, board.board_token)
            if not self.fetch_succeeded(board):
                continue
            self.last_ok_count[key] = board.job_count
            seen_today = set()
            for p in by_board.get(key, []):
                seen_today.add(p.key)
                tracked = self.postings.get(p.key)
                if tracked is None:
                    self.postings[p.key] = Tracked(latest=p, first_seen=day, last_seen=day)
                else:
                    tracked.latest, tracked.last_seen, tracked.missed_fetches = p, day, 0
            for pid, tracked in self.postings.items():
                if (tracked.latest.source, tracked.latest.board_token) == key and pid not in seen_today:
                    tracked.missed_fetches += 1


def build_postings(data_root: Path) -> list[Posting]:
    ledger = PostingLedger()
    for day in posting_days(data_root):
        boards, raw = read_postings_day(data_root, day)
        ledger.apply_day(day, boards, raw)

    out = []
    for pid, t in sorted(ledger.postings.items()):
        p = t.latest
        fields = extract_posting(p, read_description(data_root, p.description_hash))
        out.append(
            Posting(
                id=pid,
                source=p.source,
                board_token=p.board_token,
                employer_id=p.employer_id,
                title=p.title,
                url=p.url,
                location_raw=p.location_raw,
                description_hash=p.description_hash,
                first_seen=t.first_seen,
                last_seen=t.last_seen,
                missed_fetches=t.missed_fetches,
                status=t.status,
                **fields,
            )
        )
    return out


def postings_table(postings: list[Posting]) -> pa.Table:
    rows = []
    for p in postings:
        row = p.model_dump()
        row["evidence"] = json.dumps(row["evidence"], ensure_ascii=False, sort_keys=True)
        for key in ("source", "province", "remote", "duration_status", "track", "role_type", "status"):
            row[key] = str(row[key])
        row["provinces"] = [str(v) for v in row["provinces"]]
        rows.append(row)
    schema = pa.schema(
        [
            ("id", pa.string()),
            ("source", pa.string()),
            ("board_token", pa.string()),
            ("employer_id", pa.string()),
            ("title", pa.string()),
            ("url", pa.string()),
            ("location_raw", pa.string()),
            ("in_canada", pa.bool_()),
            ("province", pa.string()),
            ("provinces", pa.list_(pa.string())),
            ("remote", pa.string()),
            ("term", pa.string()),
            ("terms", pa.list_(pa.string())),
            ("term_start", pa.date32()),
            ("term_end", pa.date32()),
            ("duration_options_months", pa.list_(pa.float64())),
            ("duration_status", pa.string()),
            ("track", pa.string()),
            ("is_student_role", pa.bool_()),
            ("role_type", pa.string()),
            ("evidence", pa.string()),  # JSON object: field -> text span
            ("description_hash", pa.string()),
            ("first_seen", pa.date32()),
            ("last_seen", pa.date32()),
            ("missed_fetches", pa.int32()),
            ("status", pa.string()),
            ("deadline", pa.date32()),
            ("employment_type_raw", pa.string()),
            ("department", pa.string()),
            ("team", pa.string()),
            ("workplace_type_raw", pa.string()),
            ("posted_on", pa.date32()),
        ]
    )
    return pa.Table.from_pylist(rows, schema=schema)


def write_postings(postings: list[Posting], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(postings_table(postings), path, compression="zstd")
