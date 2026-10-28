"""Command line entry points used by the daily Action.

    python -m pipeline.cli fetch-postings   --data-root data-branch
    python -m pipeline.cli process-postings --data-root data-branch
    python -m pipeline.cli fetch-programs   --data-root data-branch
    python -m pipeline.cli process-programs --data-root data-branch
    python -m pipeline.cli build-site-data  # data/processed -> site/public/data
    python -m pipeline.cli label-sheet      --data-root data-branch
    python -m pipeline.cli evaluate         --data-root data-branch

Fetch commands write raw snapshots to the data root (a checkout of the `data`
branch). Process commands rebuild data/processed/ from every snapshot. Each
command appends one line to data/run_log.jsonl. A source that fails is logged
and skipped; it never stops the other sources.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from pipeline import build_site_data, program_watch
from pipeline.evaluate import markdown_table, read_labels, score, write_label_sheet
from pipeline.postings import build_postings, write_postings
from pipeline.sources import fetch_board
from pipeline.sources.http import PoliteClient
from pipeline.storage import iter_programs_days, write_postings_day, write_programs_day

ROOT = Path(__file__).resolve().parent.parent
EMPLOYERS = ROOT / "config" / "employers.yaml"
PROGRAMS = ROOT / "config" / "programs.yaml"
PROCESSED = ROOT / "data" / "processed"
RUN_LOG = ROOT / "data" / "run_log.jsonl"
LABELS = ROOT / "data" / "labels" / "postings.csv"


def log_run(entry: dict[str, Any]) -> None:
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    with RUN_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False, sort_keys=True, default=str) + "\n")
    print(json.dumps(entry, default=str))


def fetch_postings(data_root: Path, day: dt.date) -> int:
    with EMPLOYERS.open(encoding="utf-8") as f:
        employers = yaml.safe_load(f)["employers"]
    client = PoliteClient()
    boards, postings = [], []
    try:
        for employer in employers:
            status, kept = fetch_board(client, employer)
            boards.append(status)
            postings.extend(kept)
            if not status.ok:
                print(
                    f"board failed: {employer['board_type']}/{employer['board_token']}: {status.error}", file=sys.stderr
                )
    finally:
        client.close()
    sizes = write_postings_day(data_root, day, boards, postings)
    failed = [f"{b.source}/{b.board_token}: {b.error}" for b in boards if not b.ok]
    log_run(
        {
            "command": "fetch-postings",
            "day": day,
            "boards": len(boards),
            "boards_failed": len(failed),
            "failed": failed,
            "postings_kept": len(postings),
            **sizes,
        }
    )
    # Exit non-zero only if every board failed: that points at the runner, not a source.
    return 1 if boards and len(failed) == len(boards) else 0


def process_postings(data_root: Path) -> int:
    postings = build_postings(data_root)
    write_postings(postings, PROCESSED / "postings.parquet")
    student = [p for p in postings if p.is_student_role and p.in_canada and p.status == "open"]
    log_run(
        {
            "command": "process-postings",
            "postings": len(postings),
            "open_canadian_student": len(student),
            "with_stated_duration": sum(p.duration_status == "stated" for p in student),
        }
    )
    return 0


def fetch_programs(data_root: Path, day: dt.date) -> int:
    programs = program_watch.load_programs(PROGRAMS)
    client = PoliteClient(min_interval=2.0)
    now = dt.datetime.now(dt.UTC)
    try:
        records = [program_watch.fetch_program(client, p, now) for p in programs]
    finally:
        client.close()
    write_programs_day(data_root, day, records)
    failed = [f"{r['program_id']}: {r['error']}" for r in records if not r["ok"]]
    log_run({"command": "fetch-programs", "day": day, "pages": len(records), "failed": failed})
    return 1 if records and len(failed) == len(records) else 0


def process_programs(data_root: Path) -> int:
    programs = program_watch.load_programs(PROGRAMS)
    watch, changes = program_watch.build_program_watch(programs, list(iter_programs_days(data_root)))
    program_watch.write_program_watch(watch, changes, PROCESSED)
    log_run({"command": "process-programs", "pages": len(watch), "changes": len(changes)})
    return 0


def label_sheet(data_root: Path, limit: int = 200) -> int:
    """Add postings to data/labels/postings.csv for hand labelling (brief v1 item 4).

    Every open Canadian student posting first, up to `limit`. If there are fewer,
    the rest is filled with other Canadian postings, which still exercise the
    province and track extractors. Posting ids are hashes, so ordering by id is
    an unbiased shuffle that stays the same between runs.
    """
    postings = [p for p in build_postings(data_root) if p.in_canada and p.status == "open"]
    student = sorted((p for p in postings if p.is_student_role), key=lambda p: p.id)
    others = sorted((p for p in postings if not p.is_student_role), key=lambda p: p.id)
    chosen = (student + others)[:limit]
    already = {r["id"] for r in read_labels(LABELS)} if LABELS.exists() else set()
    added = write_label_sheet(chosen, LABELS, already)
    print(f"Added {added} rows to {LABELS.relative_to(ROOT)} ({len(student)} Canadian student postings open).")
    return 0


def evaluate(data_root: Path) -> int:
    postings = {p.id: p for p in build_postings(data_root)}
    labels = [r for r in read_labels(LABELS) if any((r.get(c) or "").strip() for c in ("track", "is_student_role"))]
    print(f"{len(labels)} labelled rows\n")
    print(markdown_table(score(labels, postings)))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m pipeline.cli")
    parser.add_argument(
        "command",
        choices=[
            "fetch-postings",
            "process-postings",
            "fetch-programs",
            "process-programs",
            "build-site-data",
            "label-sheet",
            "evaluate",
        ],
    )
    parser.add_argument("--data-root", type=Path, default=ROOT / "data-branch", help="checkout of the data branch")
    parser.add_argument("--date", type=dt.date.fromisoformat, default=None, help="snapshot date (default: today, UTC)")
    args = parser.parse_args(argv)
    day = args.date or dt.datetime.now(dt.UTC).date()

    if args.command == "fetch-postings":
        return fetch_postings(args.data_root, day)
    if args.command == "process-postings":
        return process_postings(args.data_root)
    if args.command == "fetch-programs":
        return fetch_programs(args.data_root, day)
    if args.command == "build-site-data":
        meta = build_site_data.build()
        log_run({"command": "build-site-data", **meta["counts"]})
        return 0
    if args.command == "label-sheet":
        return label_sheet(args.data_root)
    if args.command == "evaluate":
        return evaluate(args.data_root)
    return process_programs(args.data_root)


if __name__ == "__main__":
    sys.exit(main())
