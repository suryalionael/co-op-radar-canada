# 0001: Coverage thresholds and Phase 0 results

- **Status:** Accepted. Thresholds 2026-10-28; results and decision 2026-10-30.
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

Decision run on 2026-10-30 with `scripts/coverage_spike.py`. Output: `data/coverage/2026-10-30.json` and `.md`, committed just before this section.

| Measure | Value |
|---|---|
| Run date | 2026-10-30 |
| Boards in seed list | 171 |
| Boards responding successfully | 171 |
| Boards failed or 404 | 0 |
| Total postings | 16,453 |
| Postings in Canada | 3,274 |
| **Canadian student postings (headline)** | **177** |
| Student postings, remote with no country | 0 |
| Canadian student postings mentioning a term | 76 |
| Canadian student postings mentioning a duration | 63 |

The run is valid for the decision: at least 100 boards responded (171 of 171). A dry check of every board earlier the same day also found no failures and no empty boards.

**Where the 177 come from.** The seed list grew from 70 to 171 boards on 2026-10-30, in two ways:

| Boards | Count | Canadian student postings |
|---|---|---|
| Original seed list (verified 2026-10-28) | 70 | 48 |
| Added from our own candidate lists (P0-1, #19) | 61 | 3 |
| Added because a curated internship list linked to them (ADR 0007) | 40 | 126 |

The last group was chosen *because* those employers had student roles listed, so it pulls the headline up. Without it, the count would be 51, in the "40 to 99" row. The postings are also concentrated: 43 boards have at least one, and the top five (Equitable Bank 19, Lyft 16, Kensington Tours 15, Astera Labs 13, Geotab's internship board 12) hold 75 of the 177.

## Decision

**Build v1 as planned** (the "100 or more" row). The count was taken with the rules and the table committed before any results, across every seed board, as this ADR set out. It is not near a boundary.

Two notes, so the number is not over-read:

- **The "40 to 99" row's extra step, employer discovery, has in effect already happened.** The 40 list-found boards *are* employer discovery (brief section 5.5, lever 1). The headline therefore measures the seed list after discovery, not a random sample of Canadian employers. A student-facing claim should use the site's own counts, not 177.
- **The v1 extractors are stricter than these counting rules.** The Daily pipeline published 48 open student postings from the 70 original boards. The first Daily run with all 171 boards (2026-10-31) will give the comparable v1 number.

## Consequences

- If coverage is thin, the product leans on program watch, which covers the employers the posting APIs cannot reach.
- The counting rules here are intentionally looser than the v1 extractors, so the v1 site may show fewer postings than this number.
