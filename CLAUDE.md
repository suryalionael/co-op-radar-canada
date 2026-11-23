# Co-op Radar Canada: notes for Claude Code

A free tracker of Canadian tech co-op and internship postings: a Python pipeline (`pipeline/`, tests in `tests/`) writes JSON that a static Next.js site (`site/`) shows. Read `PRODUCT.md` for who it's for and `docs/brief.md` for the full brief.

## Rules

- Public, permitted sources only. Never fetch from LinkedIn, Indeed, Glassdoor, Reddit or Workday career sites. Ask before adding any new source.
- Never invent numbers: metrics, counts and evaluation results come from the data.
- Commits are authored by Lio. Do not add Claude as a co-author or contributor.
- Checks before pushing: `ruff check .`, `ruff format --check .`, `mypy pipeline`, `pytest -q`, and in `site/`: `npm run typecheck`, `npm run build`.
- UI work goes through the impeccable skill (`.claude/skills/impeccable/`). The design direction is in `.impeccable/surfaces/`.

## Delegation

Route work to the cheapest model that can do it well:

- **`quick-worker` (Haiku):** lookups, greps, summaries of files, running a command and reporting, small mechanical edits with an exact spec.
- **`sonnet-worker` (Sonnet):** contained coding tasks with a clear goal and a few files, such as a function and its test, a component change to spec, or docs from code.
- **Main model:** design decisions, debugging failures with no known cause, changes across the pipeline and site, anything touching data correctness or sources.

Give a subagent a complete, self-contained prompt: the goal, the exact files, and what "done" looks like. Check its result before building on it.
