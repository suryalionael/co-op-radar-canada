---
name: Co-op Radar Canada
description: Canadian tech co-op and internship postings, set as a transit timetable of work terms.
colors:
  rail: "oklch(0.47 0.12 153)"
  rail-fg: "oklch(0.99 0.01 150)"
  rail-muted: "oklch(0.9 0.04 152)"
  go: "oklch(0.42 0.11 153)"
  go-fg: "oklch(0.99 0.01 150)"
  go-soft: "oklch(0.86 0.06 152)"
  link: "oklch(0.42 0.11 153)"
  signal: "oklch(0.85 0.17 86)"
  signal-fg: "oklch(0.22 0.02 155)"
  warning: "oklch(0.47 0.12 60)"
  bg: "oklch(0.973 0.007 120)"
  surface: "oklch(0.995 0.002 120)"
  fg: "oklch(0.22 0.02 155)"
  muted: "oklch(0.45 0.02 155)"
  border: "oklch(0.87 0.012 130)"
  ink-bar: "oklch(0.22 0.02 155)"
  ink-bar-fg: "oklch(0.99 0 0)"
  rail-dark: "oklch(0.33 0.08 153)"
  rail-fg-dark: "oklch(0.97 0.01 150)"
  rail-muted-dark: "oklch(0.85 0.04 152)"
  go-dark: "oklch(0.72 0.14 152)"
  go-fg-dark: "oklch(0.17 0.02 155)"
  go-soft-dark: "oklch(0.55 0.1 152)"
  link-dark: "oklch(0.8 0.13 152)"
  signal-dark: "oklch(0.85 0.16 86)"
  signal-fg-dark: "oklch(0.2 0.02 155)"
  warning-dark: "oklch(0.82 0.12 75)"
  bg-dark: "oklch(0.18 0.015 155)"
  surface-dark: "oklch(0.215 0.018 155)"
  fg-dark: "oklch(0.94 0.01 120)"
  muted-dark: "oklch(0.74 0.02 140)"
  border-dark: "oklch(0.33 0.02 155)"
  ink-bar-dark: "oklch(0.12 0.012 155)"
  ink-bar-fg-dark: "oklch(0.95 0.01 120)"
typography:
  display:
    fontFamily: "Overpass Variable, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(2.25rem, 1.4rem + 3.2vw, 3.75rem)"
    fontWeight: 900
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Overpass Variable, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 900
    lineHeight: 1.1
  title:
    fontFamily: "Atkinson Hyperlegible Next, Helvetica Neue, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 700
    lineHeight: 1.375
  body:
    fontFamily: "Atkinson Hyperlegible Next, Helvetica Neue, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  body-lead:
    fontFamily: "Atkinson Hyperlegible Next, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Overpass Variable, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 800
    letterSpacing: "0.06em"
  figures:
    fontFamily: "Overpass Variable, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 900
    lineHeight: 1
    fontFeature: "tnum"
  facts:
    fontFamily: "Overpass Variable, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 700
rounded:
  none: "0"
spacing:
  gutter-mobile: "16px"
  gutter-desktop: "40px"
  row-y: "14px"
  row-x-mobile: "16px"
  row-x-desktop: "20px"
  column-gap: "16px"
  section: "32px"
components:
  rail:
    backgroundColor: "{colors.rail}"
    textColor: "{colors.rail-fg}"
    padding: "8px 40px"
  nav-link:
    textColor: "{colors.rail-muted}"
    typography: "{typography.facts}"
    height: "44px"
    padding: "2px 6px 0"
  nav-link-current:
    textColor: "{colors.rail-fg}"
  search-bar:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.fg}"
    rounded: "{rounded.none}"
    height: "56px"
  bar-select:
    typography: "{typography.facts}"
    height: "56px"
    padding: "0 16px"
  button-ink:
    backgroundColor: "{colors.fg}"
    textColor: "{colors.bg}"
    rounded: "{rounded.none}"
    height: "48px"
    padding: "0 24px"
  button-ink-hover:
    backgroundColor: "{colors.go}"
    textColor: "{colors.go-fg}"
  button-outline:
    textColor: "{colors.fg}"
    rounded: "{rounded.none}"
    height: "48px"
  chip:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.fg}"
    rounded: "{rounded.none}"
    height: "40px"
    padding: "0 12px"
  chip-on:
    backgroundColor: "{colors.go}"
    textColor: "{colors.go-fg}"
  timetable-head:
    backgroundColor: "{colors.ink-bar}"
    textColor: "{colors.ink-bar-fg}"
    typography: "{typography.label}"
    padding: "10px 20px"
  job-row:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.fg}"
    padding: "14px 20px"
  plate-length-stated:
    backgroundColor: "{colors.go}"
    textColor: "{colors.go-fg}"
    typography: "{typography.label}"
    padding: "2px 8px"
  plate-length-inferred:
    textColor: "{colors.go}"
    typography: "{typography.label}"
    padding: "2px 8px"
  status-open:
    backgroundColor: "{colors.signal}"
    textColor: "{colors.signal-fg}"
    typography: "{typography.label}"
    padding: "2px 8px"
  status-soon:
    textColor: "{colors.fg}"
    typography: "{typography.label}"
    padding: "2px 8px"
  status-quiet:
    textColor: "{colors.muted}"
    typography: "{typography.label}"
    padding: "2px 8px"
  company-card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.none}"
    padding: "16px"
  window-strip-sm:
    height: "24px"
  window-strip-lg:
    height: "56px"
  apply-link:
    textColor: "{colors.link}"
    height: "44px"
---

# Design System: Co-op Radar Canada

## Overview

**Creative North Star: "The Work-Term Timetable"**

The site is a printed transit timetable for co-op terms. A green rail runs across the top like a line colour on a platform sign; below it, postings are departures in a ruled table: age in the first column, the role, then term, length and province as service facts, and Apply at the end. Everything is square, ruled in 1px lines, and set in a signage face for figures and labels, with a highly legible text face for everything a student actually reads.

Density is timetable-high but calm. Rows are tight (14px vertical padding), numbers are tabular and aligned like timings, and colour carries meaning rather than decoration: green is the line and the stated fact, yellow is the signal (highlight, "open now", current month, focus), black is the head bar and frame. Night mode is the same board after dark, not an inverted one; the rail deepens and the go-green lightens so plates still read.

Trust comes from showing the posting's own words. The row opens to quote the sentence a term or length was read from, with the matched phrase highlighted in timetable yellow; when a posting doesn't say, the board says "not stated" in muted italic instead of guessing.

This world replaced the earlier "evidence ledger" world (serif display, red accent), which the owner rejected. It also refuses the category default for job boards: soft rounded cards on grey with a purple accent.

**Key Characteristics:**
- A green rail header (wordmark, nav, live counts) on every page.
- Square corners everywhere (radius 0); 1px rules, 1.5px plate and chip borders, 2px frames on the search bar and empty states.
- Overpass for display, labels, plates and every number; Atkinson Hyperlegible Next for titles and running text.
- A black timetable head bar over ruled rows; length plates as solid (stated) or outlined (worked out) green.
- Timetable yellow is the one highlight colour: headline highlight, open-status plate, current-month ring, `<mark>`, selection and the focus halo.

## Colors

A transit-line palette: one deep green line colour, one signal yellow, near-black ink on a faintly green off-white ground. All tokens are OKLCH in `site/app/globals.css`; the frontmatter values are normative and the `-dark` keys are the `prefers-color-scheme: dark` set.

### Primary
- **Platform Rail Green** (`rail`): the header band only. Its text is Rail White (`rail-fg`) for the wordmark and current nav item, Rail Mist (`rail-muted`) for other nav items and the counts line.
- **Go Green** (`go`, with `go-fg`): stated facts and the "on" state. Solid length plates, the pressed shortcut chip, strong months in the service calendar, the age figure of postings new this week, the hover fill of the ink button, and the colour of input accents and carets. Go Green is darker than the rail so it holds AA on the light ground.
- **Line Green Link** (`link`): text links and the Apply link. Same value as Go Green in light mode; lifts to a pale green in dark mode.
- **Soft Go** (`go-soft`): weaker months in the service calendar (postings seen, outside the main window).

### Secondary
- **Timetable Yellow** (`signal`, with `signal-fg`): the highlight. The yellow block behind the headline's last phrase, the "Open · N" status plate, the current-month ring on the calendar, highlighted spans in evidence quotes, text selection, the skip link, the sample-data banner, the active-nav underline, the hint box border, and the outer focus halo.

### Tertiary
- **Amber Notice** (`warning`): only for evidence caveats inside an opened row ("means different months at different schools", "term had already ended").

### Neutral
- **Platform Off-White** (`bg`): page ground.
- **Card White** (`surface`): rows, cards, search bar, chips at rest.
- **Timetable Ink** (`fg`): text, the 2px frames, the ink button, the calendar frame, outlined status plates.
- **Faded Ink** (`muted`): secondary lines (employer · location), dates under ages, select labels, captions, "not stated" text.
- **Rule Grey-Green** (`border`): the 1px rules between rows, cards, calendar cells and select divisions; dashed for empty states and the opened-row divider.
- **Head-Bar Black** (`ink-bar`, with `ink-bar-fg`): the timetable head bar. Equals ink in daylight; goes darker than the ground at night.

### Named Rules
**The Two Signals Rule.** Green means a fact or an "on" state; yellow means "look here" (highlight, open now, now, focus). No third accent. Amber appears only inside opened evidence as a caveat.

**The Night Service Rule.** Dark mode is a re-tuned set, not an inversion: rail darkens, go and link lighten, yellow stays yellow. Every new token gets both values.

## Typography

**Display Font:** Overpass Variable (with Helvetica Neue, Arial)
**Body Font:** Atkinson Hyperlegible Next (with Helvetica Neue, Arial)
**Label/Figures Font:** Overpass Variable, tabular numerals

**Character:** Overpass is highway and transit signage; it sets the headline, column heads, plates and every figure. Atkinson Hyperlegible Next carries the role titles and all reading text so a student on a phone between classes can scan without effort.

### Hierarchy
- **Display** (Overpass 900, clamp 2.25rem to 3.75rem, line-height 1.1, -0.02em): one page headline, its last phrase on a yellow highlight block that clones across line breaks.
- **Headline** (Overpass 900, 1.375rem): section heads such as the result count ("128 roles"), "Service calendar", "Open roles". Counts inside them are tabular figures.
- **Title** (Atkinson 700, 1rem, snug): the role title in each row. Text face, not signage, because it is read, not scanned. (As of this writing the shipped row title renders in Overpass: the unlayered global `h1, h2, h3` font rule in `globals.css` outranks the row's `font-sans` utility. That is a cascade defect, not the rule.)
- **Body** (Atkinson 400, 1rem, 1.5): running text; quotes cap at 75ch, lead paragraphs at 46ch.
- **Body lead** (Atkinson 400, 1.125rem, muted): the one-line pitch beside the headline.
- **Label** (Overpass 800, 0.6875rem to 0.8125rem, uppercase, 0.06em tracking): column heads, length plates, status plates, evidence-quote labels.
- **Figures** (Overpass, tabular numerals): ages ("2d", 900 at 1.375rem), dates, counts, province codes, calendar letters.
- **Facts** (Overpass 700, 0.9375rem): the term cell, nav links, bar-select values, chip text (bold at 0.875rem).

### Named Rules
**The Timings Rule.** Every number on the board is Overpass with tabular numerals, so ages, counts and dates align like departure times.

**The Read vs Scan Rule.** Things you scan (labels, plates, figures, nav) are Overpass; things you read (titles, sentences, quotes) are Atkinson.

## Layout

A single centred column, max width 80rem (`max-w-7xl`), with 16px side gutters on mobile and 40px from 768px. The rail spans full width; its inner content shares the same container. Main content starts 32px under the rail; sections separate by 32 to 40px.

**The jobs page** stacks: headline left with the pitch right (1.3fr / 1fr from 768px, bottom-aligned), the full-width search bar, the shortcut chips, then the board. From 1024px the board is two columns: the timetable (fluid) and a 20rem service-calendar aside that sticks to the top while scrolling.

**The timetable grid.** From 768px the head bar and every row share one column template: Posted 4.5rem, Role fluid, Term 8rem, Length 5.5rem, Prov 4rem, Apply 4.75rem, with a 16px column gap. Under 768px the head bar hides and each row becomes a two-column grid (4rem age column spanning two rows, then the role), with term, length plate and province wrapping in a line beneath and Apply pushed to the right. Rows label their own cells for screen readers; the head bar is visual only.

**Companies** use a ruled grid of cards (1 column, 2 from 640px, 3 from 1280px) sharing borders rather than gaps. The company detail page holds a large service calendar and the role table at a 48rem reading width.

**Touch targets** are at least 44px (nav links, Apply, text buttons), 40px for chips, 56px for the search bar and its selects.

## Elevation & Depth

Flat. There are no shadows on any surface; depth is a stack of grounds and rules: off-white page, white rows and cards, a black head bar, a green rail. Separation is always a 1px rule or a frame, never a lift.

The one box-shadow in the system is the focus halo: a 3px ink outline offset 2px, with a 7px timetable-yellow ring outside it (`outline: 3px solid var(--fg); outline-offset: 2px; box-shadow: 0 0 0 7px var(--signal)`). It reads on every ground, including the green rail and the yellow plates.

### Named Rules
**The Ruled, Not Lifted Rule.** Surfaces never cast shadows. If two things need separating, draw a rule.

## Shapes

Square corners throughout (radius 0; `--radius-sm` and `--radius-md` are both 0, so legacy `rounded-*` utilities render square). Line weights carry hierarchy: 1px rules for rows, cards and cells; 1.5px for chips, outlined plates, status plates and the calendar frame; 2px for the search bar, the outline button and the dashed empty-state box; 3px for the nav's current-page underline. Dashed lines mean "empty" or "opened detail", never structure.

### Named Rules
**The Square Corner Rule.** Nothing is rounded except the radar mark's circles in the wordmark.

## Components

### Rail and navigation
A full-width green band. The wordmark is a yellow radar disc with green rings and beam beside "Co-op Radar" in Overpass 900 at 1.375rem. Nav links (Jobs, Companies, Programs, About) are Overpass 700, 44px tall, Rail Mist at rest and Rail White on hover; the current page is Rail White with a 3px yellow underline. From 1024px the right end shows live counts in figures ("128 open roles · 54 companies · updated Nov 22"); on smaller screens it hides and the nav wraps under the wordmark.

### Search bar and bar selects
One framed instrument: a 2px ink frame on Card White. A search field (56px, with an inline search icon) fills the left; Term, Province and Length selects sit to its right, each a 56px cell with a small muted label over an Overpass 700 value, divided by 1px rules. On mobile the field sits on top and the three selects form a three-column row beneath. An ink button ("More filters") closes the bar: Timetable Ink fill, Off-White text, Overpass 800, hovering to Go Green. Opening it unfolds a panel of plain bordered selects (Field, Remote, Recency) below a rule.

### Shortcut chips
Square chips, 40px tall, 1.5px border: Rule Grey-Green on Card White at rest (hover borders in ink), Go Green fill with white text when pressed (`aria-pressed`). Label in Overpass 700, count in tabular figures (muted at rest). On mobile they scroll horizontally edge to edge; on desktop they wrap. The same chip serves as the companies view filter.

### Timetable head bar and JobRow
The head bar is Head-Bar Black with small tracked Overpass capitals: Posted, Role, Term, Length, Prov. Rows are Card White, separated by 1px rules, inside a 1px side frame. Each row: age in large figures (Go Green when under a week old) over the first-seen date; role title in Atkinson 700 over a muted, truncated "employer · location · remote" line; the term in Overpass 700 (or muted italic "term not stated"); the length plate; the province code in figures; and Apply as an Overpass 800 Line Green link with a 2px underline that thickens to 3px on hover, followed by a drawn up-right arrow (inline SVG at 0.8em, stroked in the link colour; never a text glyph). A dotted-underline text button, "Show the posting's words", opens the row.

### Length plates
The length is a small rectangular plate ("4 MO") in tracked Overpass capitals. **Solid** (Go Green fill, white text) when the posting states the length; **outlined** (1.5px Go Green border, green text) when it was worked out from dates. When there is no length, muted italic "length not stated" replaces the plate. A legend above the table on desktop shows both plates and the new-this-week figure.

### Status plates
Company status in the same plate form: **Open · N** on Timetable Yellow; **Opens ~Mar** outlined in 1.5px ink; **Quiet** as muted text with no frame.

### Service calendar (WindowStrip)
Twelve month cells in a 1.5px ink frame, divided by 1px rules. Strong months (in the main hiring window or at least half the peak) fill Go Green; weaker months fill Soft Go; empty months stay blank; the current month carries a 2.5px inset yellow ring. One form at two sizes: **sm** (24px tall, single month letters) in company cards and the jobs-page aside; **lg** (56px, three-letter months plus counts) on the company page. A muted caption states the window ("Usually hires Sep–Nov") or "Not enough history yet".

### Company cards
Card White cells in a shared-border grid, 16px padding. Company name in Overpass 800 at 1.0625rem (hover to link green with underline), sector beneath in muted small text, the status plate top-right, and a small service calendar below. On the jobs page aside the same card stands alone with a 1px border.

### Evidence quote
Inside an opened row (separated by a dashed rule and indented to the role column on desktop): a muted tracked label ("TERM", "LENGTH", "DATES") in a 3.5rem column, then the posting's sentence in curly quotes, max 75ch, with the matched phrase as a `<mark>` in Timetable Yellow. Below, a muted provenance line: how the length was read, first-seen date, source.

### Empty and hint states
Empty states are a 2px dashed rule box with an Overpass 800 line and outline-button suggestions. The "more postings match if their length were stated" hint is a 1.5px yellow-bordered strip on Card White with a link-button.

### Focus and motion
Focus is the ink-plus-yellow halo described under Elevation. Colour changes on chips, nav and buttons take 150ms on `cubic-bezier(0.23, 1, 0.32, 1)`. An opened row's evidence and the More-filters panel **unfold** downward: 220ms `cubic-bezier(0.16, 1, 0.3, 1)`, clip-path from fully clipped at the bottom to open, opacity 0.4 to 1. Under `prefers-reduced-motion: reduce` all transitions and animations are off.

## Do's and Don'ts

### Do:
- **Do** set every number (ages, counts, dates, province codes, calendar letters) in Overpass with tabular numerals.
- **Do** separate rows, cards and cells with 1px Rule Grey-Green lines on Card White; keep corners at 0.
- **Do** use the solid Go Green plate only for a length the posting states, and the outlined plate for a length worked out from dates.
- **Do** say "not stated" in muted italic when the posting doesn't say, rather than leaving a cell blank or guessing.
- **Do** keep Timetable Yellow for highlight and "now": the headline phrase, open status, the current month, `<mark>`, selection and focus.
- **Do** give every new colour token both a daylight and a night-service value.
- **Do** keep tap targets at 44px or more for links and buttons, 40px for chips.

### Don't:
- **Don't** round corners, add drop shadows, or float postings as separate cards; the board is a ruled table.
- **Don't** add a third accent colour (no purple, blue or red accent); green and yellow carry all meaning.
- **Don't** set role titles or reading text in Overpass, or figures in Atkinson.
- **Don't** bring back the rejected evidence-ledger look: serif display faces, monospace labels, red accent.
- **Don't** use the soft rounded card on grey with a purple accent that job boards default to.
- **Don't** animate anything beyond the row-open unfold and short colour transitions, and never when reduced motion is requested.
