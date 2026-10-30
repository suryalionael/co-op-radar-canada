# Project timeline

Phase-by-phase schedule for Co-op Radar Canada, built from the targets and hour estimates in [`brief.md`](brief.md) section 7. Budget: about 3 hours of project time a week. Each phase ships before the next starts; when behind, cut from that phase's cut list instead of moving the date.

Status as of **2026-10-29**: Phase 0 in progress. Everything is merged to `main` and running on GitHub. The first live coverage run (informational: 70 boards, below ADR 0001's minimum of 100) found **46 Canadian student postings**. The first Daily run published them to the site data. The Phase 0 decision run waits on the seed list reaching 100 boards ([#4](https://github.com/suryalionael/co-op-radar-canada/issues/4)). Work is tracked in GitHub issues; the order is in [#3](https://github.com/suryalionael/co-op-radar-canada/issues/3).

## At a glance

| Phase | Dates | Budget | Ships | Gate to move on |
|---|---|---|---|---|
| Phase 0 · Coverage spike | Oct 28 – Nov 3, 2026 | ~3 h | ADR 0001 results and decision, ADR 0002 storage estimate | Decision recorded in ADR 0001 |
| v1 · Verified postings and program watch | Nov 4 – Dec 13, 2026 | ~17 h | Daily pipeline, evaluated extractors, program watch, public site | v1 acceptance criteria (below) |
| v2 · Submissions, employer pages, news | Dec 14, 2026 – Jan 31, 2027 | ~21 h | Issue form, employer pages, digest and RSS, news feed and classifier | v2 acceptance criteria (below) |
| v3 · Market view and season write-up (stretch) | Feb – May 2027 | as time allows | Market page, StatCan chart, recruiting calendar, season write-up | none (stretch) |

```
           Oct 28   Nov 3         Dec 13          Jan 31     Feb 28            May 31
2026-27      |--P0--|----- v1 ------|------ v2 -----|  (v2 slip) |------ v3 -------|
Recruiting   |<====== Summer 2027 peak: Sept – Jan ======>|
Launch                              ^ before winter break
```

The Summer 2027 recruiting window runs roughly September to January, so v1 has to be public by **Dec 13** for students still applying to use it.

---

## Phase 0 · Coverage spike (Oct 28 – Nov 3, 2026)

Answers the project's biggest unknown: how many Canadian student postings do Greenhouse, Lever and Ashby actually provide?

| When | Task | Status |
|---|---|---|
| Oct 28 | Seed list `config/employers.yaml` (70 boards, verified) | Done |
| Oct 28 | ADR 0001 thresholds and counting rules committed before any results | Done |
| Oct 28 | Repository laid out as in the brief; `scripts/coverage_spike.py` with tests; CI | Done |
| Oct 28 | ADR 0003 (Workday out of scope), ADR 0004 (forbidden sites as link-outs only), ADR 0002 drafted | Done |
| Oct 29 | First live coverage run (informational, 70 boards): 46 Canadian student postings, `data/coverage/2026-10-29.md` | Done |
| Oct 29 – Nov 1 | Grow seed list to at least 100 responding boards (ADR 0001 validity rule): run `scripts/check_board_tokens.py` on `scripts/candidate_tokens.txt`, add the hits | Done Oct 30 (135 boards; 171 after adding boards found through the curated list, ADR 0007) |
| Nov 2 | Decision run of `coverage_spike.py`; add results table and decision to ADR 0001 in a **separate commit** | To do |
| Nov 3 | Put the measured bytes per day into ADR 0002 and accept it | To do |

**Acceptance:** ADR 0001 has thresholds committed before results, plus the results table and decision; storage estimate in ADR 0002.

**What the decision changes:**

| Headline count | Effect on v1 |
|---|---|
| 100 or more | v1 as planned below |
| 40 to 99 | v1 as planned, plus employer discovery (brief 5.5 lever 1) in weeks 1–4 to reach ~300 employers (~2 h, taken from the "new this week" view and track filter if needed) |
| Under 40 | Before the site: employer discovery and the terms check for more ATS platforms (lever 2). Program watch moves to week 1 and leads the site |

Re-run the spike on the first weekend of each month (Dec 6, Jan 3, Feb 7, Mar 7, Apr 4, May 2) and save the output under `data/coverage/`. These runs feed the v3 coverage chart and do not reopen the decision.

---

## v1 · Verified postings and program watch (Nov 4 – Dec 13, 2026)

Six weeks at ~3 h a week. Two things have long lead times and must start early: the **daily Action** (7 consecutive green days before launch) and the **program-watch dry run** (7 days with no false "changed" alerts).

| Week | Dates | Work | Hours |
|---|---|---|---|
| 1 | Nov 4 – 10 | `pipeline/models.py` (pydantic records), Greenhouse/Lever/Ashby sources, `storage.py` writing to the orphan `data` branch, `daily.yml` running. ADR 0005 hosting decision | 3 |
| 2 | Nov 11 – 17 | Closed-status guard with the failed/empty-fetch test. `config/programs.yaml` (~30 pages) and the program-watch fetcher. **Start the 7-day program-watch dry run by Nov 17** | 3 |
| 3 | Nov 18 – 24 | Term and duration extractors with pytest cases (multi-option durations, weeks to months, dates to `inferred_from_dates`) | 3 |
| 4 | Nov 25 – Dec 1 | Province and track extractors. Review the program-watch dry run and fix noisy pages. Start labelling `data/labels/postings.csv` | 3 |
| 5 | Dec 2 – 8 | Finish labelling (all Canadian student postings, up to 200). Evaluation with counts and 95% Wilson intervals in `docs/evaluation.md` and the README. `build_site_data.py`. Daily Action must be green from Dec 6 at the latest | 3 |
| 6 | Dec 9 – 13 | Static site: search, filters, posting cards with provenance labels, program-watch panel, About page with the coverage gap. Deploy. **Launch Dec 13** to Seneca students and on LinkedIn | 2–3 |

**Built ahead (Oct 28, offline, with tests; not yet run on live data):**

| Item | Where | Remaining |
|---|---|---|
| Pydantic records | `pipeline/models.py` | — |
| Greenhouse, Lever, Ashby sources with polite client | `pipeline/sources/` | First live run |
| Raw storage on the `data` branch | `pipeline/storage.py` | Measured size for ADR 0002 |
| Closed-status guard (failed and empty fetches) | `pipeline/postings.py` | — |
| Term, duration, province, track, student extractors | `pipeline/extract/` | Tune on real postings during labelling |
| Program watch: main text, noise removal, change log, robots.txt | `pipeline/program_watch.py` | Verify the URLs in `config/programs.yaml`; 7-day dry run |
| Daily workflow | `.github/workflows/daily.yml` | First run after merge to main |
| Labelling sheet and evaluation with Wilson intervals; labeller agreement | `pipeline/evaluate.py` | Label postings (week 5) |
| Site data build (DuckDB → JSON) | `pipeline/build_site_data.py` | — |
| Static site in the evidence-ledger design, Vercel Analytics | `site/`, `DESIGN.md` | Review (V1-10), deploy (V1-2), phone QA (V1-12) |

With this done, weeks 1–3 mostly become live testing and fixing, and week 6 becomes review and launch instead of building the site.

Owners for every remaining task are on the [kanban board](kanban.md) (Lio about 80%, Ei Htoo about 20%).

**Acceptance criteria** (from the brief):

- Daily Action green for 7 consecutive days.
- Duration precision ≥ 0.95 on the labelled set, reported as counts with a 95% Wilson interval; lower bound under 0.90 is stated in the README; recall reported as measured.
- Re-running the pipeline on the same day gives identical processed output.
- Failed or empty board fetch closes no postings (test).
- Program watch: no false "changed" alerts over the 7-day dry run.
- Site loads and filters in under 2 seconds on a phone.
- Every card links to the original posting and shows "verified from posting text" or "duration not stated".
- About page states what the site does not cover.

**Cut list, in order:** "new this week" view → track filter → program watch reduced to the 15 most important pages. Never cut evaluation, provenance or honest labelling.

---

## v2 · Submissions, employer pages and student-opportunity news (Dec 14, 2026 – Jan 31, 2027)

Seven weeks, ~21 h. Holidays may add time; the plan does not assume it.

| Week | Dates | Work | Hours |
|---|---|---|---|
| 1 | Dec 14 – 20 | GitHub issue form for submissions with a validating Action. Google News RSS terms check (open question 4): approve with an ADR or drop | 3 |
| 2 | Dec 21 – 27 | Employer pages: open postings, program-watch status, news timeline slot, LinkedIn job-search link-out | 2 |
| 3 | Dec 28 – Jan 3 | Daily news pull (GDELT, BetaKit, Canada.ca, approved candidates) into dated snapshots; dedupe; pre-filter from `config/news_queries.yaml` | 3 |
| 4 | Jan 4 – 10 | Employer and program matching with aliases, plus the known-false-match test set. Weekly digest page and RSS | 4 |
| 5 | Jan 11 – 17 | Hand-label 300 pre-filtered headlines plus 100 dropped ones (part 1) | 3 |
| 6 | Jan 18 – 24 | Finish labelling; merge classes with fewer than 20 examples (ADR). Keyword rules vs TF-IDF + logistic regression | 3 |
| 7 | Jan 25 – 31 | Publish classifier evaluation (precision, recall, confusion matrix) and the rules-vs-model ADR. News feed filters and "hint, not an opening" note | 3 |

**Acceptance criteria:** matching precision ≥ 0.9 with counts; pre-filter miss rate from the 100 dropped headlines; classifier evaluation in `docs/evaluation.md` with the chosen method justified; news filters by signal and province with the hint label; no article text anywhere.

**Cut list:** ship items 1–5 (weeks 1–4) by Jan 31 with rule-based signals, and move labelling and the classifier comparison (weeks 5–7) to **Feb 28**. Those can slip but not be dropped.

---

## v3 · Market view and season write-up (stretch, Feb – May 2027)

| Month | Work |
|---|---|
| February | Weekly market page (postings by week, city, track). If v2 slipped, finish the classifier comparison first |
| March | Statistics Canada job-vacancy chart by province beside the site's own counts (confirm the table ID first). Coverage-over-season chart from the monthly spike re-runs |
| April | Recruiting calendar from snapshots and `ProgramChange` history. Lead-lag analysis: do program and funding announcements come before student postings? |
| May | Public write-up of the season: what opened when, by sector and province |

---

## Decision log checkpoints

| ADR | Topic | Due |
|---|---|---|
| 0001 | Coverage thresholds and Phase 0 results | Thresholds: done. Results: Nov 2 |
| 0002 | Raw storage design, Canada filter, size budget | Drafted; accept with the measured size by Nov 3 |
| 0003 | Workday out of scope | Done |
| 0004 | LinkedIn and other forbidden sites as link-outs only | Done |
| 0005 | Hosting: Vercel free tier with Web Analytics | Done |
| 0006 | Multi-value term and province, in-Canada flag | Done |
| 0007 | Curated internship list for seeding and evaluation only | Done |
| 0008 | Structured job-type fields, role type, term status | Done |
| 0009 | Phase 0 coverage evidence from the curated list's platforms | Done |
| later | Google News RSS terms check; each new source from brief 5.5; rules vs model for news | v2 weeks 1 and 7 |
