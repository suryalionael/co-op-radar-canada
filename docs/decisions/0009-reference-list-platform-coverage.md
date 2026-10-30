# 0009: Phase 0 coverage evidence from a curated internship list

- **Status:** Accepted (evidence only; the Phase 0 decision stays in ADR 0001)
- **Date:** 2026-10-30
- **Deciders:** Lionael Surya

## Context

ADR 0001 asks whether Greenhouse, Lever and Ashby carry enough Canadian student postings to build on. It answers by counting postings on our own seed boards. That count cannot show what we *miss*: postings at employers whose boards we cannot reach at all.

The curated list in ADR 0007 gives a second view. A human found the internships first, and each Apply link shows which job-board platform the employer uses. `scripts/reference_list_coverage.py` classifies every link. The counts are in `data/coverage/reference_platform_breakdown.csv`.

This ADR records that evidence. It does not change ADR 0001's thresholds or counting rules, and it is not the Phase 0 decision run.

## Evidence

From the list as fetched on 2026-10-30. Closed rows show "Closed🔒" instead of a link, so platforms can be read only from **open** rows. The 2027 file has 698 rows, 295 of them open, at 107 companies. The 2026 file has only 29 open rows out of 1,409, too few to break down.

**What our planned sources can reach** (Greenhouse, Lever, Ashby):

| Measure | Reachable | Share |
|---|---|---|
| Open 2027 listings | 70 of 295 | 0.24 (95% CI 0.19–0.29) |
| Companies with an open 2027 listing | 34 of 107 | 0.32 (95% CI 0.24–0.41) |

Greenhouse has 42 listings at 17 companies, Ashby 17 at 10, and Lever 11 at 7. For 18 of the Greenhouse listings, the link goes through the employer's own careers page (`gh_jid`), so the board token is not in the URL. Several of those employers are already in our config under their own token.

**What makes up the remainder** (225 listings):

| Platform | Listings | Companies | Reachable by us |
|---|---|---|---|
| Workday | 108 (37%) | 33 | No: out of scope (ADR 0003) |
| Other hosts, own careers sites | 35 (12%) | 11 | No (6 of these listings are on SmartRecruiters, 1 company) |
| iCIMS | 28 (9%) | 6 | No |
| Eightfold | 18 (6%) | 1 | No |
| Oracle Cloud | 16 (5%) | 7 | No |
| Rippling | 6 (2%) | 4 | No |
| Workable | 5 (2%) | 4 | No |
| BambooHR | 4 (1%) | 4 | No |
| JazzHR | 2 (1%) | 2 | No |
| SuccessFactors | 2 (1%) | 2 | No |
| Avature | 1 (<1%) | 1 | No |

Workday alone is about 37% of the open listings, roughly half of what we cannot reach. Workday, iCIMS, Oracle and Eightfold together are about 58%. These are the large enterprise systems used by banks, insurers, telecoms and big tech, the employers ADR 0003 covers through program watch instead.

## Decision

1. Treat this as supporting evidence for ADR 0001. **About a quarter of curated tech internship listings, and about a third of the companies, are on platforms our pipeline reads.** The site's coverage statement should say so in those terms (README, About page).
2. Keep Workday out of scope (ADR 0003). Its share here confirms it is the biggest gap, but not that it has become a permitted source.
3. List the smaller platforms as **candidates for brief section 5.5, lever 2** (terms check and ADR per platform before any code). Each one reaches only a few employers in this list, so none is worth building now:

   | Platform | Employers here | What to check later |
   |---|---|---|
   | SmartRecruiters | 1 | Has a published Posting API. Already named in lever 2 |
   | Workable | 4 | Whether its public jobs widget endpoint is documented and permitted for third-party reading |
   | Rippling | 4 | Whether Rippling publishes a public job-board API for customer boards |
   | BambooHR | 4 | Careers pages load a JSON job list, but no public API documentation was found: likely not permitted |
   | JazzHR | 2 | Its API needs the customer's key, so probably no public read path |

   These are leads, not findings. None of them was checked for this ADR, and no fetcher is built.

## Consequences

- The README's "What it does not cover" section now quotes these shares.
- The 40 employers added from this list (`data/coverage/token_check_log.csv`) raise our reachable share among the list's companies, but cannot move the platform split itself.
- The figures come from one curator's list, which leans toward software roles and is not exhaustive. Re-run `scripts/reference_list_coverage.py` with the monthly coverage runs (OPS-1) to see how the split moves through the season.
