# 0002: Raw storage design, Canada filter and size budget

- **Status:** Proposed. Waiting on the Phase 0 size measurement.
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

1. **Loose Canada filter at fetch time.** Keep a posting if its location, title or description mentions Canada, a province or territory, a Canadian city, or "remote". This is a deliberate superset of what the site shows, so a better province extractor later never lacks data. The filter is `passes_loose_filter` in `scripts/coverage_spike.py`; the v1 pipeline will reuse the same rule.
2. **Metadata daily, descriptions once.** Each day writes `raw/postings/YYYY-MM-DD.jsonl.gz`: one line per posting with every API field except the description, plus `description_hash`. Each distinct description is written once to `raw/descriptions/{hash}.html.gz`.
3. **Raw lives on an orphan `data` branch.** The daily Action checks out both branches. `main` holds code, config, labels, small processed outputs (overwritten each run) and the site.
4. **Size budget: 1 GB a year.** If the measured rate projects past that, roll each month into one Parquet file and squash that month's daily commits on the `data` branch, recorded in a new ADR.

## Size estimate

To be filled in from the Phase 0 decision run (`data/coverage/<date>.json`, fields `loose_filter_bytes` and `loose_filter_gzip_bytes`).

| Measure | Value |
|---|---|
| Postings kept by the loose filter | — |
| Bytes per day, JSON lines, descriptions included | — |
| Bytes per day, gzipped | — |
| Upper bound per year (gzipped × 365, no description de-duplication) | — |

The upper bound is pessimistic: with descriptions stored once, most days only add metadata lines plus the descriptions of new or edited postings.

## Consequences

- `main` stays small enough to clone quickly; the full history is one `git fetch origin data` away.
- The daily Action needs write access to two branches.
- If the budget is exceeded, monthly roll-ups lose day-level git history on the `data` branch but keep the data itself.
