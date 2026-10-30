# 0002: Raw storage design, Canada filter and size budget

- **Status:** Accepted (2026-10-30), to be re-measured after seven Daily runs at 171 boards.
- **Date:** 2026-10-28
- **Deciders:** Lionael Surya

## Context

The pipeline keeps every fetch as an immutable raw snapshot, so processing can be re-run from scratch and every fact traces back to what the source said on a given day. Committing full API responses (with description HTML) to `main` every day would add megabytes a day, and git keeps every version forever: compressing old files later never shrinks the repository.

## Options

1. Commit full daily responses to `main`. Simple, but the repository grows without bound and clones get slow.
2. Store raw files as GitHub Release assets. Keeps the git history small, but files are harder to diff and browse, and the daily Action has to manage uploads.
3. Store compact snapshots on an orphan `data` branch, with descriptions de-duplicated by hash. (Brief section 4.1.)

## Decision

Option 3.

1. **Loose Canada filter at fetch time.** Keep a posting if its location, title or description mentions Canada, a province or territory, a Canadian city, or "remote". This is a deliberate superset of what the site shows, so a better province extractor later never lacks data. The rule is `passes_loose_filter` in `pipeline/geo.py`, used by the daily fetch. (`scripts/coverage_spike.py` keeps its own frozen copy so Phase 0 numbers stay comparable.)
2. **Metadata daily, descriptions once.** Each day writes `raw/postings/YYYY-MM-DD.jsonl.gz`: one line per posting with every API field except the description, plus `description_hash`, and `raw/boards/YYYY-MM-DD.json`: whether each board fetch succeeded and how many jobs it returned, which the closed-status guard needs when processing replays history. Each distinct description is written once to `raw/descriptions/{hash}.html.gz`.
3. **Raw lives on an orphan `data` branch.** The daily Action checks out both branches. `main` holds code, config, labels, small processed outputs (overwritten each run) and the site.
4. **Size budget: 1 GB a year.** If the measured rate projects past that, roll each month into one Parquet file and squash that month's daily commits on the `data` branch, recorded in a new ADR.

## Size estimate

Two measurements, both from 2026-10-30.

**Upper bound, from the Phase 0 decision run** (`data/coverage/2026-10-30.json`, 171 boards):

| Measure | Value |
|---|---|
| Postings kept by the loose filter | 8,878 |
| Bytes per day, JSON lines, descriptions included | 122.96 MB |
| Bytes per day, gzipped | 13.21 MB |
| Upper bound per year (gzipped × 365, no description de-duplication) | 4.82 GB |

**Realistic rate, from the Daily runs** (`data/run_log.jsonl`, 70 boards, 5,062–5,103 postings kept). Each day writes the metadata snapshot plus only the descriptions not stored before:

| Measure | 70 boards (measured) | 171 boards (scaled by postings kept, ×1.74) |
|---|---|---|
| Metadata snapshot per day, gzipped | 0.82 MB | 1.43 MB |
| New descriptions per day, gzipped (after the first day) | 0.37–0.59 MB | about 0.83 MB |
| Total per day | about 1.3 MB | about 2.26 MB |
| Per year | about 0.47 GB | **about 0.83 GB** |
| One-time first-day descriptions | 17.6 MB | about 13 MB more for the new boards |

The 171-board column is an estimate scaled from 70 boards. It is under the 1 GB budget, but with little room: most of it is the daily metadata snapshot, which repeats unchanged postings.

## Acceptance

Accepted on 2026-10-30 with the estimate above. Re-measure from `data/run_log.jsonl` after the first seven Daily runs at 171 boards (by 2026-11-07). If the measured rate projects past 1 GB a year, switch to the monthly roll-up in decision point 4 and record it in a new ADR. Storing only the postings that changed each day, instead of a full snapshot, is the first alternative to look at.

## Consequences

- `main` stays small enough to clone quickly; the full history is one `git fetch origin data` away.
- The daily Action needs write access to two branches.
- If the budget is exceeded, monthly roll-ups lose day-level git history on the `data` branch but keep the data itself.
