# Deploying the site (Vercel, ADR 0005)

One-time setup, about 15 minutes (card **V1-2**, Lio). Do it after this branch is merged to `main`.

1. Sign in at vercel.com with GitHub (Hobby plan, free).
2. **Add New → Project**, import `suryalionael/co-op-radar-canada`.
3. **Root Directory:** `site`. Vercel detects Next.js; keep the default build command (`npm run build`). The site is a static export, so there is no server to configure.
4. **Production branch:** `main`. Deploy.
5. In the project, open **Analytics** and enable **Web Analytics**. The `<Analytics />` component is already in `site/app/layout.tsx`; data appears after the next deploy.
6. In **Settings → Git**, keep "Ignored Build Step" on its default, so commits that don't touch `site/` don't redeploy. The daily Action changes `site/public/data/`, so each day with new data deploys once.
7. Optional: add a custom domain under **Settings → Domains** (open question 3 in the brief: check the name first).

## How data reaches the site

```
Daily Action ─► data/processed/*.parquet ─► build-site-data ─► site/public/data/*.json ─► commit to main ─► Vercel build
```

Nothing on the site is fetched at runtime: the JSON is baked into the static pages at build time.

## The company sheet

The company list is the Google Sheet **Co-op Radar companies** (tab `companies`). Edit it there; the daily run copies it into `config/companies.csv` and the site updates the next morning. Decision: [ADR 0010](decisions/0010-company-sheet-and-published-descriptions.md).

| Column | What to put |
|---|---|
| `id` | Short key: lowercase letters, digits, `-` or `_`. Never change it for an existing company. |
| `name`, `sector` | Shown on the site. |
| `show` | `yes` or `no`. `no` hides the company and its postings but keeps the row. |
| `website`, `careers_url` | Optional. Must start with `https://`. |
| `board_type`, `board_token` | `greenhouse`, `lever` or `ashby` and the board's token. Leave blank if there is no job board. |
| `hq_province` | Optional. |
| `hiring_months` | Months this company usually hires students: `Sep-Oct`, `Sep to Oct`, `9,10`, `Nov-Jan`. Shown as "Researched". |
| `hiring_note`, `hiring_source` | What you found and where (a link is best). Shown with the months. |
| `notes` | Private. Never published. |

- **Add a company:** add a row. With a board token, the next run checks the board; if it doesn't answer, the company is still listed, without postings.
- **Delete a company:** delete its row. Its postings leave the site on the next run. Use `show = no` to hide without losing the row.
- **A bad edit:** if the sheet can't be read, has a typo the checks catch (duplicate `id`, unknown `board_type`, a link that isn't `https`, a month that isn't a month), or loses more than half its rows, the run keeps the last good list and the **Daily** workflow shows as failed. Open the run and read the `sync-companies` line in `data/run_log.jsonl`: it names the sheet row.
- **Where the link is set:** repository variable `COMPANY_SHEET_CSV_URL` (Settings, Secrets and variables, Actions, Variables). It is a view-only link, not a secret.

## Checking it

- Every page should show the real data date in the header ("Postings checked YYYY-MM-DD"), or "No postings collected yet".
- A yellow "Sample data" banner must **never** appear on the live site. It only shows when built with `npm run build:sample`.
- Phone check (card V1-12): load and filter in under 2 seconds on a real phone over mobile data.

## Local preview

```bash
cd site
npm install
npm run dev:sample     # fictional sample data, with a banner
npm run dev            # real data from site/public/data
```
