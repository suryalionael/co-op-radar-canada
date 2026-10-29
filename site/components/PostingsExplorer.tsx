"use client";

import MiniSearch from "minisearch";
import { useEffect, useMemo, useState } from "react";
import { PostingEntry } from "./PostingEntry";
import { compareTerms, daysBetween, PROVINCES, REMOTE_LABELS, TRACKS } from "@/lib/format";
import type { Posting, RemoteMode } from "@/lib/types";

interface Filters {
  q: string;
  term: string;
  duration: string; // a number of months, "not_stated", or ""
  province: string;
  track: string;
  remote: string;
  recent: boolean;
}

const EMPTY: Filters = { q: "", term: "", duration: "", province: "", track: "", remote: "", recent: false };
const KEYS = ["q", "term", "duration", "province", "track", "remote"] as const;

function readUrl(): Filters {
  const params = new URLSearchParams(window.location.search);
  const f = { ...EMPTY };
  for (const k of KEYS) f[k] = params.get(k) ?? "";
  f.recent = params.get("new") === "1";
  return f;
}

function writeUrl(f: Filters) {
  const params = new URLSearchParams();
  for (const k of KEYS) if (f[k]) params.set(k, f[k]);
  if (f.recent) params.set("new", "1");
  const query = params.toString();
  window.history.replaceState(null, "", query ? `?${query}` : window.location.pathname);
}

function matches(p: Posting, f: Filters, dataDate: string | null): boolean {
  if (f.term && !p.terms.includes(f.term)) return false;
  if (f.duration === "not_stated" && p.duration_options_months.length) return false;
  if (f.duration && f.duration !== "not_stated" && !p.duration_options_months.includes(Number(f.duration)))
    return false;
  // A remote-in-Canada posting is open to students in every province.
  if (f.province && !p.provinces.includes(f.province) && !p.provinces.includes("REMOTE_CA")) return false;
  if (f.track && p.track !== f.track) return false;
  if (f.remote && p.remote !== f.remote) return false;
  if (f.recent && dataDate && daysBetween(p.first_seen, dataDate) > 6) return false;
  return true;
}

export function PostingsExplorer({ postings, dataDate }: { postings: Posting[]; dataDate: string | null }) {
  const [filters, setFilters] = useState<Filters>(EMPTY);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => setFilters(readUrl()), []);

  const update = (patch: Partial<Filters>) => {
    const next = { ...filters, ...patch };
    setFilters(next);
    writeUrl(next);
  };

  const search = useMemo(() => {
    const index = new MiniSearch<Posting>({
      fields: ["title", "employer", "location_raw"],
      storeFields: ["id"],
      searchOptions: { prefix: true, fuzzy: 0.15, boost: { title: 2, employer: 2 }, combineWith: "AND" },
    });
    index.addAll(postings);
    return index;
  }, [postings]);

  const options = useMemo(() => {
    const terms = [...new Set(postings.flatMap((p) => p.terms))].sort(compareTerms);
    const durations = [...new Set(postings.flatMap((p) => p.duration_options_months))].sort((a, b) => a - b);
    const provinces = Object.keys(PROVINCES).filter((code) => postings.some((p) => p.provinces.includes(code)));
    const tracks = Object.keys(TRACKS).filter((t) => postings.some((p) => p.track === t));
    return { terms, durations, provinces, tracks };
  }, [postings]);

  const results = useMemo(() => {
    const hits = filters.q.trim() ? new Set(search.search(filters.q).map((r) => r.id as string)) : null;
    return postings.filter((p) => (!hits || hits.has(p.id)) && matches(p, filters, dataDate));
  }, [postings, filters, search, dataDate]);

  const active = KEYS.filter((k) => k !== "q" && filters[k]).length + (filters.recent ? 1 : 0);

  return (
    <div className="md:grid md:grid-cols-[15rem_minmax(0,45rem)] md:gap-12">
      <div className="md:sticky md:top-6 md:self-start">
        <label htmlFor="q" className="block text-sm font-medium">
          Search title, employer or city
        </label>
        <input
          id="q"
          type="search"
          value={filters.q}
          onChange={(e) => update({ q: e.target.value })}
          className="mt-1 block min-h-11 w-full rounded-sm border border-border bg-bg px-3 text-base hover:border-muted transition-colors"
          autoComplete="off"
        />

        <button
          type="button"
          onClick={() => setShowFilters((s) => !s)}
          aria-expanded={showFilters}
          aria-controls="filters"
          className="mt-3 min-h-11 w-full rounded-sm border border-border px-3 text-left text-base font-medium md:hidden"
        >
          Filters{active ? ` (${active} on)` : ""} <span aria-hidden="true">{showFilters ? "▴" : "▾"}</span>
        </button>

        <fieldset
          id="filters"
          className={`${showFilters ? "block" : "hidden"} mt-3 space-y-4 rounded-md bg-surface p-4 md:block md:bg-transparent md:p-0`}
        >
          <legend className="sr-only">Filters</legend>
          <Select label="Term" value={filters.term} onChange={(term) => update({ term })}>
            <option value="">Any term</option>
            {options.terms.map((t) => (
              <option key={t}>{t}</option>
            ))}
          </Select>
          <Select label="Duration" value={filters.duration} onChange={(duration) => update({ duration })}>
            <option value="">Any duration</option>
            {options.durations.map((d) => (
              <option key={d} value={String(d)}>
                {d} months
              </option>
            ))}
            <option value="not_stated">Not stated</option>
          </Select>
          <Select label="Province" value={filters.province} onChange={(province) => update({ province })}>
            <option value="">Anywhere in Canada</option>
            {options.provinces.map((code) => (
              <option key={code} value={code}>
                {PROVINCES[code]}
              </option>
            ))}
          </Select>
          <Select label="Field" value={filters.track} onChange={(track) => update({ track })}>
            <option value="">Any field</option>
            {options.tracks.map((t) => (
              <option key={t} value={t}>
                {TRACKS[t]}
              </option>
            ))}
          </Select>
          <Select label="Work mode" value={filters.remote} onChange={(remote) => update({ remote })}>
            <option value="">Any</option>
            {(["onsite", "hybrid", "remote"] as RemoteMode[]).map((m) => (
              <option key={m} value={m}>
                {REMOTE_LABELS[m]}
              </option>
            ))}
          </Select>
          <label className="flex min-h-11 items-center gap-2 text-base">
            <input
              type="checkbox"
              checked={filters.recent}
              onChange={(e) => update({ recent: e.target.checked })}
              className="size-5 accent-[var(--accent)]"
            />
            New this week
          </label>
          {filters.province && (
            <p className="text-sm text-muted">Includes postings that are remote anywhere in Canada.</p>
          )}
        </fieldset>
      </div>

      <section aria-labelledby="results-heading" className="mt-8 md:mt-0">
        <div className="flex items-baseline justify-between gap-4 border-b border-fg pb-2">
          <h2 id="results-heading" className="text-xl font-semibold" aria-live="polite">
            <span className="tabular">{results.length}</span> {results.length === 1 ? "posting" : "postings"}
          </h2>
          {(active > 0 || filters.q) && (
            <button
              type="button"
              onClick={() => update(EMPTY)}
              className="min-h-11 text-sm font-medium text-accent underline"
            >
              Clear filters
            </button>
          )}
        </div>

        {results.length > 0 ? (
          results.map((p) => (
            <PostingEntry
              key={p.id}
              posting={p}
              isNew={dataDate !== null && daysBetween(p.first_seen, dataDate) <= 6}
            />
          ))
        ) : (
          <div className="py-10 text-base">
            <p className="font-medium">No postings match these filters.</p>
            <p className="mt-1 text-muted">
              Try another term or duration, or check Program watch for programs that haven&rsquo;t posted yet.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}

function Select({
  label,
  value,
  onChange,
  children,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  children: React.ReactNode;
}) {
  const id = `f-${label.toLowerCase().replace(/\W+/g, "-")}`;
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium">
        {label}
      </label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 block min-h-11 w-full rounded-sm border border-border bg-bg px-2 text-base hover:border-muted transition-colors"
      >
        {children}
      </select>
    </div>
  );
}
