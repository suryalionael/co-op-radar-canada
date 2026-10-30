# Kanban board

Each card links to its GitHub issue, which has the steps and the definition of done; the order of work is in [issue #3](https://github.com/suryalionael/co-op-radar-canada/issues/3). Move a card by cutting its row into another column, in the same pull request as the work. IDs match [`TODO.md`](../TODO.md) and the [timeline](timeline.md). Owners: **Lio** (Lionael Surya), **Ei** (Ei Htoo). Work split: [team.md](team.md).

Columns: **Backlog** → **This week** → **In progress** → **Review** (PR open) → **Done**.

## In progress

| ID | Card | Owner | Est. | Due |
|---|---|---|---|---|

## Review

| ID | Card | Owner | Est. | Due |
|---|---|---|---|---|
| [V1-10](https://github.com/suryalionael/co-op-radar-canada/issues/15) | Site draft is built (search, filters in the URL, evidence quotes, program watch, About, analytics, empty state): review it with `npm run dev:sample`, then polish | Lio | 2 h | Dec 12 |
| [V1-1](https://github.com/suryalionael/co-op-radar-canada/issues/9) | 30 program pages verified Oct 30 (PR open); done when the next Daily run shows `pages: 30` | Ei | 1.5 h | Nov 15 |

## This week (Oct 28 – Nov 3)

| ID | Card | Owner | Est. | Due |
|---|---|---|---|---|
| [P0-2](https://github.com/suryalionael/co-op-radar-canada/issues/5) | Phase 0 decision run; add results and decision to ADR 0001 in a separate commit | Lio | 0.5 h | Nov 2 |
| [P0-3](https://github.com/suryalionael/co-op-radar-canada/issues/6) | Put the measured bytes per day into ADR 0002 and accept it | Lio | 0.25 h | Nov 3 |

## Backlog

### v1 (Nov 4 – Dec 13)

| ID | Card | Owner | Est. | Due |
|---|---|---|---|---|
| [V1-2](https://github.com/suryalionael/co-op-radar-canada/issues/8) | Create the Vercel project (root `site/`), connect the repo, turn on Web Analytics | Lio | 0.5 h | Nov 10 |
| [V1-4](https://github.com/suryalionael/co-op-radar-canada/issues/7) | Daily Action: 7 consecutive green days (must start by Dec 6) | Lio | 0.5 h | Dec 12 |
| [V1-5](https://github.com/suryalionael/co-op-radar-canada/issues/11) | Review the 7-day program-watch dry run; fix noisy pages | Lio | 1 h | Nov 24 |
| [V1-6](https://github.com/suryalionael/co-op-radar-canada/issues/10) | Tune extractors on real postings; add each fixed case as a test | Lio | 2 h | Dec 1 |
| [V1-7](https://github.com/suryalionael/co-op-radar-canada/issues/12) | Hand-label postings (all Canadian student postings, up to 200) | Lio | 3 h | Dec 6 |
| [V1-8](https://github.com/suryalionael/co-op-radar-canada/issues/13) | Second labeller: independently label 40 postings for the agreement check | Ei | 1 h | Dec 6 |
| [V1-9](https://github.com/suryalionael/co-op-radar-canada/issues/14) | Publish evaluation (counts, Wilson intervals, agreement) in README and `docs/evaluation.md` | Lio | 0.5 h | Dec 8 |
| [V1-11](https://github.com/suryalionael/co-op-radar-canada/issues/15) | Final About page wording (coverage gap, sources, disclaimer) | Lio | 0.25 h | Dec 11 |
| [V1-12](https://github.com/suryalionael/co-op-radar-canada/issues/16) | Site QA on a real phone; file issues for anything broken | Ei | 0.5 h | Dec 12 |
| [V1-13](https://github.com/suryalionael/co-op-radar-canada/issues/17) | Launch: LinkedIn post about the project | Lio | 0.5 h | Dec 13 |
| [V1-14](https://github.com/suryalionael/co-op-radar-canada/issues/17) | Share the launch with Seneca classmates and clubs | Ei | 0.25 h | Dec 13 |
| OPS-1 | Monthly coverage re-run (first weekend: Dec 6, Jan 3, Feb 7, Mar 7, Apr 4, May 2) | Lio | 1.5 h total | monthly |

### v2 (Dec 14 – Jan 31)

| ID | Card | Owner | Est. | Due |
|---|---|---|---|---|
| V2-0 | Google News RSS terms check; approve with an ADR or drop | Lio | 0.5 h | Dec 18 |
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
| V1-0 | Site data build (DuckDB → JSON), evidence quotes in the pipeline, DESIGN.md | Lio | Oct 28 |
| V1-0 | Labeller agreement tool (Cohen's kappa) for V1-8 | Lio | Oct 28 |
| V1-3 | Merged to `main`; first live Daily run green: 70/70 boards, 46 open Canadian student postings published | Lio | Oct 29 |
| OPS-1 | First coverage run (informational, 70 boards): 46 Canadian student postings, `data/coverage/2026-10-29.md` | Lio | Oct 29 |
| [P0-1](https://github.com/suryalionael/co-op-radar-canada/issues/4) | Seed list grown to 135 boards (65 added), all with a Canadian job on Oct 30 | Ei | Oct 30 |
| V2-1a | Issue form for posting submissions, `.github/ISSUE_TEMPLATE/submit-posting.yml` (#20) | Ei | Oct 30 |
| TEAM | Team split, kanban board, to-do lists, contributing guide, deploy guide | Lio | Oct 28 |
