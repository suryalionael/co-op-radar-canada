# To-do

Checklists per person. Tick a box in the same pull request as the work, and move the card on the [kanban board](docs/kanban.md). Split and rules: [docs/team.md](docs/team.md).

## Lio (~32 h)

### Phase 0 — by Nov 3
- [ ] **P0-2** Phase 0 decision run (`python scripts/coverage_spike.py`); results + decision in ADR 0001, separate commit
- [ ] **P0-3** Bytes per day into ADR 0002; mark it Accepted

### v1 — by Dec 13
- [ ] **V1-2** Vercel project: follow [docs/deploy.md](docs/deploy.md)
- [ ] **V1-3** Merge to `main`, run the Daily workflow by hand once, fix what breaks
- [ ] **V1-4** 7 consecutive green Daily runs (start no later than Dec 6)
- [ ] **V1-5** Review the program-watch dry run (needs Ei's V1-1 first)
- [ ] **V1-6** Tune extractors on real postings; every fix gets a test
- [ ] **V1-7** Label postings: `python -m pipeline.cli label-sheet`, then fill `data/labels/postings.csv`
- [ ] **V1-9** `python -m pipeline.cli evaluate`; publish in README and `docs/evaluation.md`, with agreement from V1-8
- [ ] **V1-10** Review and polish the site draft (`cd site && npm install && npm run dev:sample`)
- [ ] **V1-11** Final About page wording
- [ ] **V1-13** LinkedIn launch post (only real numbers)
- [ ] **OPS-1** Monthly coverage re-runs: Dec 6 · Jan 3 · Feb 7 · Mar 7 · Apr 4 · May 2

### v2 — by Jan 31
- [ ] **V2-0** Google News RSS terms check → ADR or drop
- [ ] **V2-1b** Submission validation Action
- [ ] **V2-2** Employer pages
- [ ] **V2-3** Weekly digest page and RSS
- [ ] **V2-4** News pull, dedupe, pre-filter
- [ ] **V2-5** Employer and program matching
- [ ] **V2-6** Label 300 headlines
- [ ] **V2-7** Rules vs model comparison, evaluation, ADR

## Ei Htoo (~7 h)

### Phase 0 — by Nov 1
- [ ] **P0-1** Run `python scripts/check_board_tokens.py scripts/candidate_tokens.txt > hits.jsonl`; for each hit with `canada_jobs > 0` that is the right company, add an entry to `config/employers.yaml` (copy an existing entry's format). Goal: 100+ boards. Open a PR.

### v1 — by Dec 13
- [ ] **V1-1** For each page in `config/programs.yaml`: open it, confirm it is the student-program page, fix the URL if needed, set `verified: YYYY-MM-DD`. Add pages until there are ~30 (priority: banks, insurers, utilities, governments). Due Nov 15.
- [ ] **V1-8** Label 40 postings that Lio picks, in a separate file `data/labels/postings_second.csv` (same columns as `postings.csv`), without opening Lio's labels. Lio then runs `python -m pipeline.cli agreement`. Due Dec 6.
- [ ] **V1-12** Phone QA of the site: under 2 s to load and filter; every card links to its posting and says "verified from posting text" or "duration not stated". File an issue per problem. Due Dec 12.
- [ ] **V1-14** Share the launch with Seneca classmates and clubs. Dec 13.

### v2 — by Jan 31
- [ ] **V2-1a** `.github/ISSUE_TEMPLATE/submit-posting.yml`: employer, title, URL, location, term, duration, deadline, where the info came from. Due Dec 18.
- [ ] **V2-5a** 30+ headlines that mention an employer name but are not about that employer, with the expected "no match". Due Jan 7.
- [ ] **V2-6a** Label 100 news headlines. Due Jan 20.
