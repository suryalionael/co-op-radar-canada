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
