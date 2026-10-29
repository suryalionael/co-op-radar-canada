# Team and work split

| Person | Role | Share of remaining work |
|---|---|---|
| **Lionael Surya (Lio)** | Owner and lead developer. Decides scope, sources and ADRs; writes and reviews all pipeline and site code; publishes results | ~80% (~32 h) |
| **Ei Htoo** | Contributor. Source verification, a second labeller for the agreement check, QA, and the submission form template | ~20% (~7 h) |

Hours are estimates for the remaining Phase 0, v1 and v2 work (v3 is a stretch goal and not split yet). The full task list with owners is on the [kanban board](kanban.md) and in each person's [to-do list](../TODO.md).

## Why the split looks like this

- **Lio must be able to explain every part of the code in an interview** (brief section 10), so Lio owns all pipeline, extractor, classifier and site code, and reviews every pull request.
- **Ei Htoo's tasks are self-contained and high-value:** each one can be done without deep knowledge of the pipeline, has a clear "done", and removes a blocker for Lio. Verified sources and a second labeller make the published results more trustworthy.
- **Decisions stay with Lio:** thresholds, sources, terms checks and ADRs.

## Ei Htoo's tasks (~7 h)

| ID | Task | Est. | Due | Why it matters |
|---|---|---|---|---|
| P0-1 | Check `scripts/candidate_tokens.txt` with the token checker; add verified hits to `config/employers.yaml` until 100+ boards respond | 1 h | Nov 1 | Unblocks the Phase 0 decision run |
| V1-1 | Verify every URL in `config/programs.yaml` (open it, confirm it is the student-program page, fix or replace, set `verified`); add pages to reach ~30 | 1.5 h | Nov 15 | Program watch watches nothing until URLs are verified; the 7-day dry run must start by Nov 17 |
| V1-8 | Second labeller: independently label 40 postings from the label sheet, without looking at Lio's labels | 1 h | Dec 6 | Gives an inter-annotator agreement figure, so the evaluation is not one person's opinion |
| V1-12 | Site QA on a real phone: load time, filters, every card links to its posting, honest labels; file issues | 0.5 h | Dec 12 | v1 acceptance: "loads and filters in under 2 s on a phone" |
| V1-14 | Share the launch with Seneca classmates and clubs | 0.25 h | Dec 13 | Real users |
| V2-1a | Write the GitHub issue form template for posting submissions (`.github/ISSUE_TEMPLATE/submit-posting.yml`) | 1 h | Dec 18 | Lets anyone add postings the pipeline can't reach |
| V2-5a | Build the known-false-match test set for employer matching (headlines like "Apple pie recipe") | 0.5 h | Jan 7 | Protects matching precision |
| V2-6a | Label 100 of the 400 news headlines | 1.5 h | Jan 20 | Shares the largest manual task |

## How we work

- **Branches and pull requests.** Nobody pushes to `main` directly. Branch names: `ei/<task-id>-short-name` or `lio/<task-id>-short-name`. Lio reviews and merges.
- **The board is the source of truth.** Move your card on [`docs/kanban.md`](kanban.md) in the same PR as the work, and tick it in [`TODO.md`](../TODO.md).
- **Weekly check-in:** 15 minutes on Sunday. What moved, what is blocked, which cards come into "This week".
- **Labelling is independent.** Never look at the other person's labels or the extractor output while labelling. Disagreements are counted first, then discussed.
- **Never fabricate numbers.** Every figure in the README, the site or a post comes from a measurement in the repo.
- Setup and conventions: [`CONTRIBUTING.md`](../CONTRIBUTING.md).
