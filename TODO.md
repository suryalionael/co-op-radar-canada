# To-do

Checklists per person. Each item links to its GitHub issue; the order of work is in [issue #3](https://github.com/suryalionael/co-op-radar-canada/issues/3). Tick a box in the same pull request as the work, and move the card on the [kanban board](docs/kanban.md). Split and rules: [docs/team.md](docs/team.md).

## Lio (~32 h)

### Phase 0 — by Nov 3
- [x] **[P0-2](https://github.com/suryalionael/co-op-radar-canada/issues/5)** Phase 0 decision run (Actions → Phase 0 tools → `coverage-spike`, or `python scripts/coverage_spike.py`); results + decision in ADR 0001, separate commit (Oct 30: 171/171 boards, 177 Canadian student postings → build v1)
- [x] **[P0-3](https://github.com/suryalionael/co-op-radar-canada/issues/6)** Bytes per day into ADR 0002; mark it Accepted (Oct 30: about 0.83 GB a year at 171 boards; re-measure by Nov 7)

### v1 — by Dec 13
- [ ] **[V1-2](https://github.com/suryalionael/co-op-radar-canada/issues/8)** Vercel project: follow [docs/deploy.md](docs/deploy.md)
- [x] **V1-3** Merge to `main`, run the Daily workflow by hand once (Oct 29: green, 46 postings published)
- [ ] **[V1-4](https://github.com/suryalionael/co-op-radar-canada/issues/7)** 7 consecutive green Daily runs (start no later than Dec 6). First run with 171 boards: Oct 31. After it, re-run `python -m pipeline.cli reference-recall --data-root data-branch` and update `docs/evaluation.md`; by Nov 7, re-measure storage for ADR 0002
- [ ] **[V1-5](https://github.com/suryalionael/co-op-radar-canada/issues/11)** Review the program-watch dry run (needs Ei's V1-1 first)
- [x] **[V1-6](https://github.com/suryalionael/co-op-radar-canada/issues/10)** Tune extractors on real postings; every fix gets a test (Oct 30: graduation dates, month-and-year terms, duration ranges on the site)
- [ ] **[V1-7](https://github.com/suryalionael/co-op-radar-canada/issues/12)** Label postings: `python -m pipeline.cli label-sheet`, then fill `data/labels/postings.csv`
- [ ] **[V1-9](https://github.com/suryalionael/co-op-radar-canada/issues/14)** `python -m pipeline.cli evaluate`; publish in README and `docs/evaluation.md`, with agreement from V1-8
- [ ] **[V1-10](https://github.com/suryalionael/co-op-radar-canada/issues/15)** Review and polish the site draft (`cd site && npm install && npm run dev:sample`)
- [ ] **[V1-11](https://github.com/suryalionael/co-op-radar-canada/issues/15)** Final About page wording
- [ ] **[V1-13](https://github.com/suryalionael/co-op-radar-canada/issues/17)** LinkedIn launch post (only real numbers)
- [ ] **OPS-1** Monthly coverage re-runs: Dec 6 · Jan 3 · Feb 7 · Mar 7 · Apr 4 · May 2

### v2 — by Jan 31
- [ ] **V2-0** Google News RSS terms check → ADR or drop
- [ ] **V2-1b** Submission validation Action
- [ ] **V2-1c** Action that opens a PR from an accepted submission issue (Issue form → Action → PR, the curated list's pattern; $0)
- [ ] **V2-2** Employer pages
- [ ] **V2-3** Weekly digest page and RSS
- [ ] **V2-4** News pull, dedupe, pre-filter
- [ ] **V2-5** Employer and program matching
- [ ] **V2-6** Label 300 headlines
- [ ] **V2-7** Rules vs model comparison, evaluation, ADR

### v3 — stretch (backlog, not split yet)
- [ ] **V3-1** Recruiting calendar: per employer, first-posting month and how fast roles close, seeded from the curated list's 2026 and 2027 posting dates and closed flags (aggregates only, ADR 0007)

## Ei Htoo (~7 h)

### Phase 0 — by Nov 1
- [x] **[P0-1](https://github.com/suryalionael/co-op-radar-canada/issues/4)** (Oct 30: 135 boards, all responding) On GitHub: Actions → Phase 0 tools → Run workflow → `check-tokens` (or locally: `python scripts/check_board_tokens.py scripts/candidate_tokens.txt > hits.jsonl`). The run summary lists the hits. For each hit with `canada_jobs > 0` that is the right company, add an entry to `config/employers.yaml` (copy an existing entry's format). Goal: 100+ boards. Open a PR.

### v1 — by Dec 13
- [ ] **[V1-1](https://github.com/suryalionael/co-op-radar-canada/issues/9)** (Oct 30: 30 pages verified, #21 merged; done when the next Daily run shows `pages: 30`) For each page in `config/programs.yaml`: open it, confirm it is the student-program page, fix the URL if needed, set `verified: YYYY-MM-DD`. Add pages until there are ~30 (priority: banks, insurers, utilities, governments). Due Nov 15.
- [ ] **[V1-8](https://github.com/suryalionael/co-op-radar-canada/issues/13)** Label 40 postings that Lio picks, in a separate file `data/labels/postings_second.csv` (same columns as `postings.csv`), without opening Lio's labels. Lio then runs `python -m pipeline.cli agreement`. Due Dec 6.
- [ ] **[V1-12](https://github.com/suryalionael/co-op-radar-canada/issues/16)** Phone QA of the site: under 2 s to load and filter; every card links to its posting and says "verified from posting text" or "duration not stated". File an issue per problem. Due Dec 12.
- [ ] **[V1-14](https://github.com/suryalionael/co-op-radar-canada/issues/17)** Share the launch with Seneca classmates and clubs. Dec 13.

### v2 — by Jan 31
- [x] **V2-1a** `.github/ISSUE_TEMPLATE/submit-posting.yml`: employer, title, URL, location, term, duration, deadline, where the info came from. Due Dec 18.
- [ ] **V2-5a** 30+ headlines that mention an employer name but are not about that employer, with the expected "no match". Due Jan 7.
- [ ] **V2-6a** Label 100 news headlines. Due Jan 20.
