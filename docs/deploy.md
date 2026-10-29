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
