# DESIGN.md — Co-op Radar Canada site

Single source of truth for the site's look. If the CSS in `site/app/globals.css` disagrees with this file, this file wins.

## Discovery

- **Artifact:** data tool / searchable directory, mobile-first. Secondary pages: program-watch log, About.
- **Audience:** Canadian university co-op students, mostly on phones, often between classes.
- **Primary action:** narrow to "my term, my duration, my province" and open the original posting.
- **Positioning:** a careful, independent student project. Trust comes from showing sources, not from polish.
- **Adjectives:** trustworthy, precise, plainspoken, calm, student-made.
- **Essence:** *evidence over claims.*
- **Direction chosen by Lio (Oct 28, 2026):** "Evidence ledger", over "Departure board" and "Swiss minimal".

## Aesthetic commitment

**Evidence ledger.** Editorial and quiet, like a well-kept research notebook. Postings are entries in a ledger separated by rules, not floating cards. Facts are set in small capitals; the posting's own words sit under them as a citation.

**Signature move:** the *evidence quote*. Under each fact line, a corner bracket (`└`) leads to the sentence from the posting that the fact came from, with the matched words marked like a highlighter. When a duration isn't stated, the card says so in plain words instead.

## Typography

| Role | Face | Why |
|---|---|---|
| Display (titles, wordmark) | Source Serif 4 (variable, self-hosted via Fontsource) | Editorial, credible, readable at small sizes thanks to optical sizing |
| Body and UI | Public Sans (variable, Fontsource) | Plain, public-interest sans (from the US Web Design System); not Inter |
| Data (dates, counts, ids) | IBM Plex Mono 400/500 | Tabular figures, a "recorded" feel for provenance |

Scale: base 16px, ratio 1.2 (minor third): 13.33 · 16 · 19.2 · 23.04 · 27.65 · 33.18 px. Body line height 1.55, headings 1.2. Facts use small caps with 0.04em tracking.

## Colour (OKLCH)

| Token | Light | Dark | Role |
|---|---|---|---|
| `--bg` | `oklch(0.99 0.002 260)` | `oklch(0.17 0.008 260)` | page |
| `--surface` | `oklch(0.965 0.004 260)` | `oklch(0.21 0.01 260)` | filter panel, quote blocks |
| `--fg` | `oklch(0.23 0.012 260)` | `oklch(0.93 0.004 260)` | ink |
| `--muted` | `oklch(0.48 0.012 260)` | `oklch(0.7 0.01 260)` | secondary text |
| `--border` | `oklch(0.88 0.006 260)` | `oklch(0.32 0.01 260)` | rules |
| `--accent` | `oklch(0.5 0.17 27)` | `oklch(0.72 0.13 27)` | links, focus, "changed" marks (brick red) |
| `--accent-fg` | `oklch(0.99 0 0)` | `oklch(0.17 0.008 260)` | text on accent |
| `--mark` | `oklch(0.93 0.08 95)` | `oklch(0.42 0.07 95)` | highlighter behind matched words |
| `--success` | `oklch(0.5 0.12 150)` | `oklch(0.72 0.12 150)` | "verified from posting text" |
| `--warning` | `oklch(0.5 0.12 65)` | `oklch(0.78 0.12 75)` | "duration not stated", failed checks |

Distribution: neutrals ~85%, ink ~10%, red accent and highlighter together under 5%. Status is never shown by colour alone; every state has words.

## Tokens

- Spacing base 4px: 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64. Tight inside an entry (4–8), generous between entries (24).
- Radius: `--radius-sm` 2px (inputs, chips), `--radius-md` 6px (panels). Nothing rounder.
- Elevation: none. Edges are 1px rules. No shadows anywhere.
- Motion: 150ms ease-out on colour and opacity only; nothing moves when `prefers-reduced-motion` is set.

## Craft decisions

- **Layout:** phone: header, search, collapsible filters, ledger. From 900px: a 260px sticky filter column beside the ledger (max 720px measure). About uses a single 640px reading column.
- **Entries:** title (serif, links to the original posting) · employer · location · work mode · fact line (TERM · DURATION) · evidence quotes · footer in mono (first seen, source board).
- **States:** inputs have default, hover, focus-visible (2px accent outline, 2px offset) and disabled states. Empty states explain why: no data yet, or no match for the filters, with a "Clear filters" button.
- **Filters** are mirrored in the URL (`?term=Summer+2027&duration=4&province=ON`), so a filtered view can be shared in one link.
- **Icons:** none beyond text glyphs (`└`, `↗`, `·`). The typography carries the design.
- **Imagery:** none. The data is the content.
- **Dark mode:** designed: lighter surfaces for elevation, desaturated accent, dimmed highlighter with light text.
- **Accessibility:** WCAG 2.2 AA contrast for all text tokens, real `<label>`s, 44px touch targets on phone controls, landmarks, skip link, visible focus.

## Slop audit

- No Inter/Roboto as primary; no indigo/violet; no gradients, glass, blobs or glows; no shadow-plus-border stacks; no feature-card grid; no marquee or pulsing dots; no stock imagery. Structure is a ledger with a filter rail, not hero + cards.
- **Result (Oct 28, 2026, first build, checked in screenshots at 390px and 1280px, light and dark):** no tells fired. Fixed during the audit: duplicate quote on date-derived durations, a term quote that only repeated the title, light-mode warning text below AA contrast, and a footer rule wider than the header. All three fonts load from self-hosted files; interactive targets are at least 44px except inline prose links and the visually hidden skip link.

## Changelog

- 2026-10-28: Created. Evidence ledger direction, tokens above, first site build.
- 2026-10-28: Slop and accessibility audit after first build; warning token darkened to `oklch(0.5 0.12 65)`.
