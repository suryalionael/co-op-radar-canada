# 0001: Coverage thresholds and Phase 0 results

- **Status:** Thresholds accepted. Results pending.
- **Date:** 2026-10-28
- **Deciders:** Lionael Surya

## Context

The project depends on one unmeasured assumption: that the public Greenhouse, Lever and Ashby job-board APIs carry enough Canadian student postings to be worth building a site on. Large Canadian banks, insurers and governments post on Workday, which is out of scope, so the real number could be small.

Phase 0 measures that number once, with a throwaway script (`scripts/coverage_spike.py`), before any pipeline or site work. To keep the decision honest, the thresholds and the counting rules below are written and committed **before** the script is run. The git history of this file is the proof: the commit that adds the thresholds must come before the commit that adds the results.

## What is counted

The headline number is **Canadian student postings across the seed boards**, counted from one fetch of every board in `config/employers.yaml`.

A posting counts if all of the following hold:

1. **Its board fetch succeeded.** HTTP 200 with a parseable job list. Boards that fail or return 404 are reported separately and contribute nothing.
2. **It is in Canada.** Its location field (not the description) mentions "Canada", a Canadian province or territory (full name or two-letter code in a location context), or a Canadian city from the script's city list. "Remote" counts only when Canada is also mentioned (for example "Remote, Canada" or "Remote - Ontario").
3. **It is a student role.** Its title matches, case-insensitively, one of: `intern`, `internship`, `co-op`, `coop`, `co op`, `student`, `summer`, `stagiaire`, `stage` (as a whole word).

Each posting is counted once, keyed on `(source, board_token, job_id)`, even when it lists several locations.

These rules are deliberately simple. They are a measuring stick for this decision only and are not the v1 extractors.

**Reported separately, not part of the headline number:**

- Student postings whose location is only "Remote" with no country (they might be open to Canadians).
- How many of the counted postings mention a term (season + year) or a duration (number + weeks/months) in the title or description, using a quick regex.
- Bytes per board after the loose Canada filter, for the storage budget in ADR 0002.

## Validity rules

- Board tokens returning 404 are fixed or removed from `config/employers.yaml` before the decision run. The decision run must have at least 100 boards responding successfully. If it has fewer, the result is recorded but the decision waits until the seed list is fixed.
- The script sleeps between requests to the same host and sends a descriptive User-Agent.
- One run decides. Later monthly re-runs are recorded for the v3 coverage chart but do not reopen this decision.

## Decision table

| Canadian student postings across seed boards | Decision |
|---|---|
| 100 or more | Build v1 as planned. |
| 40 to 99 | Build v1, and run employer discovery (brief section 5.5, lever 1) during v1 to reach about 300 employers. |
| Fewer than 40 | Before building the site, run employer discovery and the terms check for more ATS platforms (section 5.5, lever 2). Lead the site with program watch. |

Late October is near the peak for Summer 2027 postings, so this run is close to a best case. A count near a boundary should be read as the lower option.

## Results

Not yet run. To be added in a separate commit after the thresholds above are committed.

| Measure | Value |
|---|---|
| Run date | — |
| Boards in seed list | — |
| Boards responding successfully | — |
| Boards failed or 404 | — |
| Total postings | — |
| Postings in Canada | — |
| **Canadian student postings (headline)** | — |
| Student postings, remote with no country | — |
| Canadian student postings mentioning a term | — |
| Canadian student postings mentioning a duration | — |

## Decision

Pending the results.

## Consequences

- If coverage is thin, the product leans on program watch, which covers the employers the posting APIs cannot reach.
- The counting rules here are intentionally looser than the v1 extractors, so the v1 site may show fewer postings than this number.
