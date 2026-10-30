# Sources

Every source the project reads, its terms, its status, and what is stored. A source is added here, with an ADR, before any code fetches from it (brief section 10).

| Source | Used for | Access | Status | Stored |
|---|---|---|---|---|
| Greenhouse job board API | Postings (v1) | `boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true`, public JSON | Approved | Posting metadata daily; each distinct description once (ADR 0002) |
| Lever postings API | Postings (v1) | `api.lever.co/v0/postings/{company}?mode=json`, public JSON | Approved | Same as Greenhouse |
| Ashby posting API | Postings (v1) | `api.ashbyhq.com/posting-api/job-board/{board}`, public JSON | Approved | Same as Greenhouse |
| Curated internship list ([negarprh/Canadian-Tech-Internships-2027](https://github.com/negarprh/Canadian-Tech-Internships-2027)) | Seeding employers, recall check, platform breakdown (not postings) | `raw.githubusercontent.com`, two README files; no license, so read-only at run time (ADR 0007) | Approved for seeding and evaluation only | Raw copies gitignored; only aggregate counts and our own token lists committed |
| Student-program pages | Program watch (v1) | Public pages listed in `config/programs.yaml`; each URL verified by hand before it is watched | Approved | Main page text (boilerplate removed) daily on the `data` branch; a short excerpt of added lines on change |
| GitHub issue form | Submissions (v2) | Issues labelled `submission` | Planned | Submitted fields after review |
| GDELT DOC 2.0 API | News (v2) | Public API | Approved | Headline, outlet, date, URL, query, matched terms only |
| BetaKit RSS | News (v2) | Site RSS feed | Approved | Same as GDELT |
| Canada.ca news feeds | News (v2) | Open Government Licence | Approved | Same as GDELT |
| Newswire.ca, GlobeNewswire | News (v2) | RSS | Candidate: terms check + ADR | — |
| University newsroom RSS | News (v2) | RSS | Candidate: terms check + ADR | — |
| Google News RSS | News (v2) | RSS search | Candidate: automated use not clearly permitted; check before v2 | — |
| Statistics Canada Web Data Service | Market context (v3) | Open API | Approved; table ID to confirm | Aggregate counts |

**Never sources** (ADR 0004): LinkedIn, Indeed, Glassdoor, Reddit. They may appear only as outbound links.

**Out of scope** (ADR 0003): Workday career sites.

**Politeness:** every request sends `User-Agent: co-op-radar-canada/0.1 (student project; +https://github.com/suryalionael/co-op-radar-canada)` and waits at least 1 second between requests to the same host (2 seconds for program pages).
