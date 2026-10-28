# 0004: LinkedIn and other forbidden sites as link-outs only

- **Status:** Accepted
- **Date:** 2026-10-28
- **Deciders:** Lionael Surya

## Context

LinkedIn, Indeed, Glassdoor and Reddit carry many student postings and discussions, and they are where many students already search. Their terms of use forbid automated collection.

## Decision

These sites are never sources. Nothing is fetched from them: no scraping, no unofficial APIs, no third-party scrapers or datasets built from them.

They may appear only as plain outbound links that a visitor clicks, for example a LinkedIn job search for an employer on that employer's page.

## Consequences

- Coverage is limited to official job-board APIs, RSS feeds, open-data APIs and submissions.
- Adding any new source requires checking its terms and writing an ADR first (brief section 10).
