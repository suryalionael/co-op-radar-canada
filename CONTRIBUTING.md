# Contributing

Who does what is in [docs/team.md](docs/team.md); open tasks are on the [kanban board](docs/kanban.md) and in [TODO.md](TODO.md).

## Setup

Python 3.12 and Node 20 or newer.

```bash
git clone https://github.com/suryalionael/co-op-radar-canada.git
cd co-op-radar-canada
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

For pipeline work on real data, check out the raw snapshots (the `data` branch) next to the code. The folder is gitignored:

```bash
git fetch origin data
git worktree add data-branch origin/data
python -m pipeline.cli process-postings --data-root data-branch
```

For the site:

```bash
cd site
npm install
npm run dev        # http://localhost:3000, uses the sample data in site/public/data
```

## Workflow

1. Pick your card on the board (or ask Lio for one).
2. Branch from `main`: `ei/<task-id>-short-name` or `lio/<task-id>-short-name`, e.g. `ei/v1-1-verify-program-urls`.
3. Make small commits with descriptive messages.
4. Before pushing, run what CI runs:
   ```bash
   ruff check . && ruff format --check . && mypy && pytest
   cd site && npm run typecheck && npm run build:sample   # if you touched site/
   ```
5. Open a pull request. Move your card to **Review** and tick the box in `TODO.md` in the same PR.
6. Lio reviews and merges. Nobody pushes to `main` directly.

## Rules that matter

- **Public, permitted sources only.** Never fetch from LinkedIn, Indeed, Glassdoor, Reddit or Workday career sites (ADRs 0003, 0004). Ask Lio before adding any new source.
- **Never store or republish news article text**, only headline, outlet, date and link.
- **Never fabricate or round up numbers.** Every figure in the README, on the site or in a post comes from a measurement in the repo.
- **Labelling is independent.** Do not look at the other person's labels or the extractor's output while labelling.
- **Every extracted fact keeps its evidence**, the exact text it came from.

## Adding an employer (P0-1)

The easiest way to check tokens: on GitHub, open **Actions → Phase 0 tools → Run workflow**, choose `check-tokens`, and read the table in the run summary. To check your own list, commit a file of tokens on your branch and give its path.

Copy an existing entry in `config/employers.yaml`. Only add a board if the token checker found it, it has at least one Canadian job, and it is clearly the right company (check the Greenhouse `board_name` or open a job link). Set `verified` to the date you checked. If the candidate came from an outside list, add `source: [reference-list]`, `[coop-watcher]` or both (ADR 0007), and record the check in `data/coverage/token_check_log.csv` (`python scripts/check_board_tokens.py --pairs pairs.csv --log ...`). `pytest` checks the file for duplicate ids and boards.

## Verifying a program page (V1-1)

Open the URL in a browser. It counts if it is the employer's own page about student, co-op, intern or new-grad hiring. If it redirects, use the final URL. Set `verified: YYYY-MM-DD`. If you cannot find a real page for an entry, delete the entry and say so in the PR.
