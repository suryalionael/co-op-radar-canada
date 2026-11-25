import type { Posting, RemoteMode } from "./types";

export const PROVINCES: Record<string, string> = {
  ON: "Ontario",
  QC: "Quebec",
  BC: "British Columbia",
  AB: "Alberta",
  MB: "Manitoba",
  SK: "Saskatchewan",
  NS: "Nova Scotia",
  NB: "New Brunswick",
  NL: "Newfoundland and Labrador",
  PE: "Prince Edward Island",
  YT: "Yukon",
  NT: "Northwest Territories",
  NU: "Nunavut",
  REMOTE_CA: "Remote in Canada",
};

export const TRACKS: Record<string, string> = {
  software: "Software",
  data_science: "Data science",
  data_analytics: "Data analytics",
  data_eng: "Data engineering",
  ml_ai: "ML / AI",
  business_ops: "Business and operations",
  other: "Other",
};

export const REMOTE_LABELS: Record<RemoteMode, string | null> = {
  onsite: "On-site",
  hybrid: "Hybrid",
  remote: "Remote",
  unknown: null,
};

export const SOURCES: Record<string, string> = {
  greenhouse: "Greenhouse",
  lever: "Lever",
  ashby: "Ashby",
  submission: "Submission",
};

const SEASON_ORDER: Record<string, number> = { Winter: 0, Spring: 1, Summer: 2, Fall: 3 };

/** Sort "Summer 2027", "Fall 2026"... chronologically. */
export function compareTerms(a: string, b: string): number {
  const [sa, ya] = a.split(" ");
  const [sb, yb] = b.split(" ");
  return Number(ya) - Number(yb) || (SEASON_ORDER[sa] ?? 9) - (SEASON_ORDER[sb] ?? 9);
}

/**
 * [4] -> "4 months"; [4, 8] -> "4 or 8 months"; [4, 8, 12] -> "4, 8 or 12 months".
 * A stated range keeps its two ends: [4, 16] with isRange -> "4–16 months" (anything from 4 to 16).
 */
export function formatDuration(months: number[], isRange = false): string {
  const parts = months.map((m) => (Number.isInteger(m) ? String(m) : m.toFixed(1)));
  const unit = months.length === 1 && months[0] === 1 ? "month" : "months";
  if (parts.length <= 1) return `${parts[0]} ${unit}`;
  if (isRange && parts.length === 2) return `${parts[0]}–${parts[1]} ${unit}`;
  return `${parts.slice(0, -1).join(", ")} or ${parts[parts.length - 1]} ${unit}`;
}

/** Does the posting offer this many months? A range offers every length between its ends. */
export function offersDuration(p: Posting, months: number): boolean {
  const options = p.duration_options_months;
  if (p.duration_is_range && options.length === 2) return options[0] <= months && months <= options[1];
  return options.includes(months);
}

export function durationNote(p: Posting): string {
  switch (p.duration_status) {
    case "stated":
      return "Verified from posting text";
    case "inferred_from_dates":
      return "Calculated from the dates in the posting";
    default:
      return "Duration not stated";
  }
}

/** Whole days from `from` to `to`, both ISO dates. */
export function daysBetween(from: string, to: string): number {
  return Math.round((Date.parse(to) - Date.parse(from)) / 86_400_000);
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
export const MONTH_NAMES = MONTHS;

/** "2026-11-21" -> "Nov 21". Parsed as text so the time zone can't shift the day. */
export function formatDay(iso: string): string {
  const [, m, d] = iso.split("-").map(Number);
  return `${MONTHS[m - 1]} ${d}`;
}

/** How long ago, timetable-short: "today", "3d", "2w", "3mo". */
export function formatAge(days: number): string {
  if (days <= 0) return "today";
  if (days < 7) return `${days}d`;
  if (days < 60) return `${Math.floor(days / 7)}w`;
  return `${Math.floor(days / 30)}mo`;
}

/** Duration plate text: [4] -> "4 mo", [4, 8] -> "4/8 mo", range [4, 16] -> "4–16 mo". */
export function formatPlate(months: number[], isRange = false): string {
  const parts = months.map((m) => (Number.isInteger(m) ? String(m) : m.toFixed(1)));
  return `${parts.join(isRange && parts.length === 2 ? "–" : "/")} mo`;
}

/** "ml_ai" -> "ML / AI", "fintech" -> "Fintech". */
export function formatSector(sector: string): string {
  if (sector in TRACKS) return TRACKS[sector];
  const s = sector.replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/**
 * The title as a timetable line: drop a leading "[Summer 2027 Canada]" tag and a trailing
 * " - Winter 2027" or "(Winter 2027)" that only repeats the Term column. The raw title stays in the evidence.
 */
export function displayTitle(title: string, terms: string[]): string {
  let t = title.replace(/^\s*\[[^\]]*\]\s*/, "");
  for (const term of terms) {
    const esc = term.replace(/\s+/g, "\\s+");
    t = t.replace(new RegExp(`\\s*(?:[-–—|,]\\s*${esc}|\\(\\s*${esc}\\s*\\))\\s*$`, "i"), "");
  }
  // A trailing "(Winter/January 2027, 12 Months)" only repeats the Term and Length columns.
  if (terms.length) t = t.replace(/\s*\([^)]*\b20\d\d\b[^)]*\)\s*$/, "");
  return t.trim() || title;
}

const PLACE_NOISE = /^(?:canada|remote|hybrid|on-?site|ca|headquarters|hq|office)$/i;

/** "Toronto, Ontario; Ottawa, Ontario; Greater Toronto Area" -> "Toronto, Ottawa +1". */
export function shortLocation(raw: string): string {
  const cities: string[] = [];
  for (const part of raw.split(/[;/|]|\bor\b/)) {
    const city = part
      .split(",")[0]
      .trim()
      .replace(/^[A-Z]{2}-/, "") // "CA-Toronto"
      .replace(/\b(?:headquarters|hq|office)\b/gi, "")
      .trim();
    if (city && !PLACE_NOISE.test(city) && !(city in PROVINCE_NAMES) && !cities.includes(city)) cities.push(city);
  }
  if (!cities.length) return raw.trim();
  return cities.length > 2 ? `${cities.slice(0, 2).join(", ")} +${cities.length - 2}` : cities.join(", ");
}
const PROVINCE_NAMES: Record<string, true> = Object.fromEntries(
  [...Object.values(PROVINCES), "Ontario", "Quebec", "Québec", "British Columbia", "ON", "QC", "BC", "AB"].map((n) => [n, true]),
);

/** Month flags to words: [0,0,0,0,0,0,0,0,1,1,0,0] -> "Sep–Oct"; wraps the year; gaps give "Sep, Nov". */
export function formatMonthRuns(flags: number[]): string {
  const on = flags.map((n) => n > 0);
  if (on.every(Boolean)) return "all year";
  const runs: string[] = [];
  for (let i = 0; i < 12; i++) {
    if (!on[i] || on[(i + 11) % 12]) continue; // only start at the first month of a run
    let j = i;
    while (on[(j + 1) % 12]) j++;
    runs.push(j === i ? MONTHS[i] : `${MONTHS[i]}–${MONTHS[j % 12]}`);
  }
  return runs.join(", ");
}
