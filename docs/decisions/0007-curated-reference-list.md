# 0007: Curated internship list for seeding and evaluation only

- **Status:** Accepted
- **Date:** 2026-10-30
- **Deciders:** Lionael Surya

## Context

[negarprh/Canadian-Tech-Internships-2027](https://github.com/negarprh/Canadian-Tech-Internships-2027) is a hand-curated list of Canadian tech internships (about 1.3k stars). `README.md` holds the 2027 season and `README-2026.md` the previous one. Each row has the company, role, location, an Apply link and the date posted. The curator adds the work term in parentheses after the role when it is known.

The list is useful to us in three ways:

1. Its Apply links show which employers use Greenhouse, Lever or Ashby, which seeds `config/employers.yaml`.
2. It is an independent list we can check our pipeline's recall against.
3. Its links show which job-board platforms Canadian tech internships are posted on, which is evidence for the Phase 0 coverage question.

The repository has **no license** (the GitHub API reports `license: null`). Without a license, the listings are not ours to copy or republish.

## Decision

The list is a **read-only, run-time source for seeding and evaluation**. It is never a source of postings on the site.

- `scripts/reference_list_coverage.py` fetches both READMEs from `raw.githubusercontent.com` with our usual User-Agent and pause between requests.
- Raw copies go to `data/reference/raw/`, which is gitignored. No listing (company plus role plus link) is committed or published.
- Committed outputs are limited to aggregate counts (`data/coverage/reference_platform_breakdown.csv`) and our own candidate board-token lists (`data/coverage/reference_candidate_tokens.csv`, `data/coverage/token_check_log.csv`).
- Employers found through the list are added to `config/employers.yaml` only after `scripts/check_board_tokens.py` confirms the board, as for any other candidate. Their postings then come from the employer's own Greenhouse, Lever or Ashby board, never from the list.
- The curator's parenthetical terms are **not gold labels**. They may be used only in a cross-check report against our term extractor, and never go into `data/labels/`.
- Tests use invented fixture rows in the list's format, never real rows.

## Consequences

- We get a seed list and an outside recall check at no cost and without republishing anyone's work.
- If the curator adds a license later, this ADR can be revisited; until then, the rules above hold.
- The list leans toward software roles and is not exhaustive, so recall against it is a lower bound on what we miss, not a full measure. `docs/evaluation.md` says so.
