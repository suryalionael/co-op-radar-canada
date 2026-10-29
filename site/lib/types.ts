// Shapes of the JSON written by pipeline/build_site_data.py. Keep in sync with it.

export type DurationStatus = "stated" | "inferred_from_dates" | "not_stated";
export type RemoteMode = "onsite" | "hybrid" | "remote" | "unknown";

export interface Evidence {
  term?: string;
  term_context?: string;
  term_dates?: string;
  duration?: string;
  duration_context?: string;
}

export interface Posting {
  id: string;
  source: string;
  employer_id: string;
  employer: string;
  sector: string | null;
  title: string;
  url: string;
  location_raw: string;
  province: string;
  provinces: string[];
  remote: RemoteMode;
  term: string | null;
  terms: string[];
  term_start: string | null;
  term_end: string | null;
  duration_options_months: number[];
  duration_status: DurationStatus;
  track: string;
  first_seen: string;
  last_seen: string;
  evidence: Evidence;
}

export interface ProgramStatus {
  program_id: string;
  employer_id: string;
  name: string;
  url: string;
  last_checked: string | null;
  last_fetch_ok: boolean;
  last_changed: string | null;
  change_excerpt: string | null;
  expected_open: string | null;
  expected_open_src: string | null;
}

export interface ProgramChange {
  program_id: string;
  changed_on: string;
  change_excerpt: string;
  kind: "content_change" | "manual_note";
}

export interface ProgramsData {
  programs: ProgramStatus[];
  changes: ProgramChange[];
}

export interface Meta {
  data_as_of: { postings: string | null; programs: string | null };
  counts: {
    open_student_postings: number;
    duration_stated: number;
    duration_from_dates: number;
    employers_with_postings: number;
    employer_boards_tracked: number;
    programs_watched: number;
  };
}
