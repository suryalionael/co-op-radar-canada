# 0005: Host the site on Vercel's free tier

- **Status:** Accepted
- **Date:** 2026-10-28
- **Deciders:** Lionael Surya

## Context

The site is a Next.js static export: HTML, JavaScript and prebuilt JSON, with no server. It needs free hosting, and visitor counts matter, because "real students used it" is one of the project's goals and must be backed by real numbers.

## Options

1. **GitHub Pages.** Everything stays in GitHub. Needs a `basePath` for a project site, and has no built-in analytics, so a second service (GoatCounter) would be needed for visitor counts.
2. **Vercel free tier (Hobby).** Builds from the GitHub repo on every push to `main`, gives preview deployments for pull requests, and includes Vercel Web Analytics with no cookies.

## Decision

Vercel free tier, with Vercel Web Analytics.

- The Vercel project's root directory is `site/`. It runs `npm run build`, which produces a static export in `site/out`.
- The daily Action commits new site data to `main`, which triggers a Vercel deploy. No Vercel token is stored in GitHub.
- Analytics: the `@vercel/analytics` component in the site layout. It does not use cookies, so no cookie banner is needed.

## Consequences

- Visitor numbers come from Vercel's dashboard. Only numbers read from it are reported anywhere.
- The Hobby plan is for non-commercial use, which fits a free student project. If the project ever takes money, revisit this.
- The free tier's analytics event limits are well above what a student site is expected to need; if they are hit, record it and move analytics to GoatCounter.
- Moving to GitHub Pages later only requires a `basePath` and a deploy workflow, because the site is a plain static export.
