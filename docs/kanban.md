# Kanban board

Move a card by cutting its row into another column, in the same pull request as the work. IDs match [`TODO.md`](../TODO.md) and the [timeline](timeline.md). Owners: **Lio** (Lionael Surya), **Ei** (Ei Htoo). Work split: [team.md](team.md).

Columns: **Backlog** → **This week** → **In progress** → **Review** (PR open) → **Done**.

## In progress

| ID | Card | Owner | Est. | Due |
|---|---|---|---|---|
| V1-10 | Site: `build_site_data.py` and Next.js static site (search, filters, posting cards, program-watch panel, About page); first draft by Claude, then review and polish | Lio | 2 h | Dec 12 |

## Review

| ID | Card | Owner | Est. | Due |
|---|---|---|---|---|

## This week (Oct 28 – Nov 3)

| ID | Card | Owner | Est. | Due |
|---|---|---|---|---|
| P0-1 | Check candidate board tokens; add verified hits to `config/employers.yaml` until 100+ boards respond | Ei | 1 h | Nov 1 |
| P0-2 | Phase 0 decision run; add results and decision to ADR 0001 in a separate commit | Lio | 0.5 h | Nov 2 |
| P0-3 | Put the measured bytes per day into ADR 0002 and accept it | Lio | 0.25 h | Nov 3 |

## Backlog

### v1 (Nov 4 – Dec 13)

| ID | Card | Owner | Est. | Due |
|---|---|---|---|---|
| V1-1 | Verify every URL in `config/programs.yaml`, set `verified`, add pages to reach ~30 | Ei | 1.5 h | Nov 15 |
| V1-2 | Create the Vercel project (root `site/`), connect the repo, turn on Web Analytics | Lio | 0.5 h | Nov 10 |
| V1-3 | Merge to `main`; first live pipeline run; fix what breaks | Lio | 1.5 h | Nov 10 |
| V1-4 | Daily Action: 7 consecutive green days (must start by Dec 6) | Lio | 0.5 h | Dec 12 |
| V1-5 | Review the 7-day program-watch dry run; fix noisy pages | Lio | 1 h | Nov 24 |
| V1-6 | Tune extractors on real postings; add each fixed case as a test | Lio | 2 h | Dec 1 |
| V1-7 | Hand-label postings (all Canadian student postings, up to 200) | Lio | 3 h | Dec 6 |
| V1-8 | Second labeller: independently label 40 postings for the agreement check | Ei | 1 h | Dec 6 |
| V1-9 | Publish evaluation (counts, Wilson intervals, agreement) in README and `docs/evaluation.md` | Lio | 0.5 h | Dec 8 |
| V1-11 | Final About page wording (coverage gap, sources, disclaimer) | Lio | 0.25 h | Dec 11 |
| V1-12 | Site QA on a real phone; file issues for anything broken | Ei | 0.5 h | Dec 12 |
| V1-13 | Launch: LinkedIn post about the project | Lio | 0.5 h | Dec 13 |
| V1-14 | Share the launch with Seneca classmates and clubs | Ei | 0.25 h | Dec 13 |
| OPS-1 | Monthly coverage re-run (first weekend: Dec 6, Jan 3, Feb 7, Mar 7, Apr 4, May 2) | Lio | 1.5 h total | monthly |

### v2 (Dec 14 – Jan 31)

| ID | Card | Owner | Est. | Due |
|---|---|---|---|---|
| V2-0 | Google News RSS terms check; approve with an ADR or drop | Lio | 0.5 h | Dec 18 |
| V2-1a | Issue form template for posting submissions | Ei | 1 h | Dec 18 |
| V2-1b | Action that validates submissions | Lio | 1 h | Dec 20 |
| V2-2 | Employer pages: postings, program watch, news, LinkedIn link-out | Lio | 2 h | Dec 27 |
| V2-3 | Weekly digest page and RSS | Lio | 2 h | Jan 10 |
| V2-4 | Daily news pull, dedupe, pre-filter | Lio | 3 h | Jan 3 |
| V2-5 | Employer and program matching with aliases | Lio | 2.5 h | Jan 10 |
| V2-5a | Known-false-match test set for matching | Ei | 0.5 h | Jan 7 |
| V2-6 | Label 300 of the 400 headlines | Lio | 3.5 h | Jan 24 |
| V2-6a | Label 100 of the 400 headlines | Ei | 1.5 h | Jan 20 |
| V2-7 | Keyword rules vs TF-IDF + logistic regression; publish evaluation and ADR | Lio | 4 h | Jan 31 |

### v3 (stretch, Feb – May): not split yet

Weekly market page · StatCan vacancy chart · coverage-over-season chart · recruiting calendar · lead-lag analysis · season write-up.

## Done

| ID | Card | Owner | Done |
|---|---|---|---|
| P0-0 | Seed list of 70 verified boards | Lio | Oct 28 |
| P0-0 | ADR 0001 thresholds committed before results | Lio | Oct 28 |
| P0-0 | Coverage spike script with tests; CI | Lio | Oct 28 |
| V1-0 | Pipeline built ahead: models, sources, raw storage, closed-status guard, extractors, program watch, evaluation tooling, daily workflow | Lio | Oct 28 |
| ADR | 0002 (draft), 0003, 0004, 0005 (Vercel), 0006 | Lio | Oct 28 |
