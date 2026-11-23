"use client";

import MiniSearch from "minisearch";
import { useEffect, useMemo, useRef, useState } from "react";
import { Cross } from "./Icons";
import { JobRow } from "./JobRow";
import { TimetableHead } from "./TimetableHead";
import { compareTerms, daysBetween, offersDuration, PROVINCES, REMOTE_LABELS, TRACKS } from "@/lib/format";
import type { Posting, RemoteMode } from "@/lib/types";

interface Filters {
  q: string;
  term: string;
  duration: string; // a number of months, "8plus", "not_stated", or ""
  province: string;
  track: string;
  remote: string;
  recent: boolean;
  sort: string; // "" (newest) or "company"
  unstated: boolean; // with a length filter on, also show postings that don't state a length
}

const EMPTY: Filters = { q: "", term: "", duration: "", province: "", track: "", remote: "", recent: false, sort: "", unstated: false };
const KEYS = ["q", "term", "duration", "province", "track", "remote", "sort"] as const;
const PAGE = 50;

function readUrl(): Filters {
  const params = new URLSearchParams(window.location.search);
  const f = { ...EMPTY };
  for (const k of KEYS) f[k] = params.get(k) ?? "";
  f.recent = params.get("new") === "1";
  f.unstated = params.get("unstated") === "1";
  return f;
}

function writeUrl(f: Filters) {
  const params = new URLSearchParams();
  for (const k of KEYS) if (f[k]) params.set(k, f[k]);
  if (f.recent) params.set("new", "1");
  if (f.unstated) params.set("unstated", "1");
  const query = params.toString();
  window.history.replaceState(null, "", query ? `?${query}` : window.location.pathname);
}

function matches(p: Posting, f: Filters, dataDate: string | null): boolean {
  if (f.term && !p.terms.includes(f.term)) return false;
  if (f.duration === "not_stated" && p.duration_options_months.length) return false;
  // Most postings don't state a length; with "unstated" on, a length filter keeps them rather than hiding them.
  if (f.unstated && f.duration && f.duration !== "not_stated" && !p.duration_options_months.length)
    return matchesRest(p, f, dataDate);
  if (f.duration === "8plus" && !p.duration_options_months.some((m) => m >= 8)) return false;
  if (/^\d+$/.test(f.duration) && !offersDuration(p, Number(f.duration))) return false;
  return matchesRest(p, f, dataDate);
}

/** Every filter except term and length. */
function matchesRest(p: Posting, f: Filters, dataDate: string | null): boolean {
  // A remote-in-Canada posting is open to students in every province.
  if (f.province && !p.provinces.includes(f.province) && !p.provinces.includes("REMOTE_CA")) return false;
  if (f.track && p.track !== f.track) return false;
  if (f.remote && p.remote !== f.remote) return false;
  if (f.recent && dataDate && daysBetween(p.first_seen, dataDate) > 6) return false;
  return true;
}

export function JobBoard({
  postings,
  dataDate,
  aside,
}: {
  postings: Posting[];
  dataDate: string | null;
  aside?: React.ReactNode;
}) {
  const [filters, setFilters] = useState<Filters>(EMPTY);
  const [more, setMore] = useState(false);
  const [limit, setLimit] = useState(PAGE);

  const searchRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement;
      if (e.key === "/" && !/^(INPUT|SELECT|TEXTAREA)$/.test(t.tagName) && !t.isContentEditable) {
        e.preventDefault();
        searchRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    const f = readUrl();
    setFilters(f);
    if (f.track || f.remote) setMore(true);
  }, []);

  const update = (patch: Partial<Filters>) => {
    const next = { ...filters, ...patch };
    if (!next.duration || next.duration === "not_stated") next.unstated = false;
    setFilters(next);
    setLimit(PAGE);
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
    // A term that ended before this year is a mis-read or stale, not something to filter for.
    const thisYear = Number((dataDate ?? new Date().toISOString()).slice(0, 4));
    const terms = [...new Set(postings.flatMap((p) => p.terms))]
      .filter((t) => Number(t.split(" ")[1]) >= thisYear)
      .sort(compareTerms);
    const durations = [...new Set(postings.flatMap((p) => p.duration_options_months))].sort((a, b) => a - b);
    const provinces = Object.keys(PROVINCES).filter((code) => postings.some((p) => p.provinces.includes(code)));
    const tracks = Object.keys(TRACKS).filter((t) => postings.some((p) => p.track === t));
    // Same rule as the shortcut chips: a remote-in-Canada posting counts for every province.
    const termCount = (term: string) => postings.filter((p) => matches(p, { ...EMPTY, term }, dataDate)).length;
    const provinceCount = (province: string) => postings.filter((p) => matches(p, { ...EMPTY, province }, dataDate)).length;
    return { terms, durations, provinces, tracks, termCount, provinceCount };
  }, [postings, dataDate]);

  // Shortcut lines, like the routes printed on a timetable's cover. Each is a preset of the same filters.
  const collections = useMemo(() => {
    const count = (f: Partial<Filters>) => postings.filter((p) => matches(p, { ...EMPTY, ...f }, dataDate)).length;
    const byTerm = options.terms
      .map((term) => ({ label: term, patch: { term } as Partial<Filters>, n: count({ term }) }))
      .sort((a, b) => b.n - a.n)
      .slice(0, 2);
    const list = [
      { label: "New this week", patch: { recent: true }, n: count({ recent: true }) },
      ...byTerm,
      { label: "8 months or more", patch: { duration: "8plus" }, n: count({ duration: "8plus" }) },
      { label: "Ontario", patch: { province: "ON" }, n: count({ province: "ON" }) },
      { label: "B.C.", patch: { province: "BC" }, n: count({ province: "BC" }) },
    ];
    return list.filter((c) => c.n > 0);
  }, [postings, options.terms, dataDate]);

  const results = useMemo(() => {
    const hits = filters.q.trim() ? new Set(search.search(filters.q).map((r) => r.id as string)) : null;
    const found = postings.filter((p) => (!hits || hits.has(p.id)) && matches(p, filters, dataDate));
    return filters.sort === "company"
      ? [...found].sort((a, b) => a.employer.localeCompare(b.employer) || b.first_seen.localeCompare(a.first_seen))
      : found;
  }, [postings, filters, search, dataDate]);

  // With a length filter on, how many more postings would match if their length were stated?
  const hiddenUnstated = useMemo(() => {
    if (!filters.duration || filters.duration === "not_stated" || filters.unstated) return 0;
    const hits = filters.q.trim() ? new Set(search.search(filters.q).map((r) => r.id as string)) : null;
    return postings.filter(
      (p) => !p.duration_options_months.length && (!hits || hits.has(p.id)) && matches(p, { ...filters, unstated: true }, dataDate),
    ).length;
  }, [postings, filters, search, dataDate]);

  const activeNames = [
    filters.q && `“${filters.q}”`,
    filters.term,
    filters.province && PROVINCES[filters.province],
    filters.duration &&
      (filters.duration === "8plus" ? "8+ months" : filters.duration === "not_stated" ? "length not stated" : `${filters.duration} months`),
    filters.track && TRACKS[filters.track],
    filters.remote && REMOTE_LABELS[filters.remote as RemoteMode],
    filters.recent && "new this week",
  ].filter(Boolean) as string[];

  const active =
    ["term", "duration", "province", "track", "remote"].filter((k) => filters[k as keyof Filters]).length +
    (filters.recent ? 1 : 0) +
    (filters.q ? 1 : 0);
  const isPreset = (patch: Partial<Filters>) =>
    Object.entries(patch).every(([k, v]) => filters[k as keyof Filters] === v);

  return (
    <>
      <form role="search" onSubmit={(e) => e.preventDefault()} className="border-2 border-fg bg-surface">
        <div className="flex flex-col md:flex-row">
          <label className="flex min-h-14 flex-1 items-center gap-3 px-4">
            <SearchIcon />
            <span className="sr-only">Search roles, companies or cities</span>
            <input
              type="search"
              ref={searchRef}
              value={filters.q}
              onChange={(e) => update({ q: e.target.value })}
              placeholder="Search roles, companies, cities"
              aria-keyshortcuts="/"
              autoComplete="off"
              className="h-14 w-full bg-transparent text-base placeholder:text-muted focus-visible:outline-offset-[-3px]"
            />
          </label>
          <div className="grid grid-cols-3 border-t border-border md:flex md:border-t-0">
            <BarSelect label="Term" value={filters.term} onChange={(term) => update({ term })}>
              <option value="">Any</option>
              {options.terms.map((t) => (
                <option key={t} value={t}>
                  {t} ({options.termCount(t)})
                </option>
              ))}
            </BarSelect>
            <BarSelect label="Province" value={filters.province} onChange={(province) => update({ province })}>
              <option value="">Any</option>
              {options.provinces.map((code) => (
                <option key={code} value={code}>
                  {PROVINCES[code]} ({options.provinceCount(code)})
                </option>
              ))}
            </BarSelect>
            <BarSelect label="Length" value={filters.duration} onChange={(duration) => update({ duration })}>
              <option value="">Any</option>
              {options.durations.map((d) => (
                <option key={d} value={String(d)}>
                  {d} months
                </option>
              ))}
              <option value="8plus">8 months or more</option>
              <option value="not_stated">Not stated</option>
            </BarSelect>
          </div>
          <button
            type="button"
            onClick={() => setMore((m) => !m)}
            aria-expanded={more}
            aria-controls="more-filters"
            className="min-h-12 bg-fg px-6 font-display text-[0.9375rem] font-extrabold text-bg hover:bg-go hover:text-go-fg transition-colors"
          >
            {more ? "Fewer filters" : "More filters"}
          </button>
        </div>
        {more && (
          <div id="more-filters" className="row-open grid gap-4 border-t border-border px-4 py-4 sm:grid-cols-3">
            <PanelSelect label="Field" value={filters.track} onChange={(track) => update({ track })}>
              <option value="">Any field</option>
              {options.tracks.map((t) => (
                <option key={t} value={t}>
                  {TRACKS[t]}
                </option>
              ))}
            </PanelSelect>
            <PanelSelect label="Work mode" value={filters.remote} onChange={(remote) => update({ remote })}>
              <option value="">Any</option>
              {(["onsite", "hybrid", "remote"] as RemoteMode[]).map((m) => (
                <option key={m} value={m}>
                  {REMOTE_LABELS[m]}
                </option>
              ))}
            </PanelSelect>
            <PanelSelect label="Order" value={filters.sort} onChange={(sort) => update({ sort })}>
              <option value="">Newest first</option>
              <option value="company">Company A–Z</option>
            </PanelSelect>
          </div>
        )}
      </form>

      {collections.length > 0 && (
        <ul aria-label="Shortcuts" className="-mx-4 mt-4 flex gap-2 overflow-x-auto px-4 pb-1 md:mx-0 md:flex-wrap md:overflow-visible md:px-0">
          {collections.map((c) => {
            const on = isPreset(c.patch);
            return (
              <li key={c.label}>
                <button
                  type="button"
                  aria-pressed={on}
                  onClick={() => update(on ? Object.fromEntries(Object.keys(c.patch).map((k) => [k, EMPTY[k as keyof Filters]])) : c.patch)}
                  className={`inline-flex min-h-10 items-center gap-2 whitespace-nowrap border-[1.5px] px-3 font-display text-sm font-bold transition-colors ${
                    on ? "border-go bg-go text-go-fg" : "border-border bg-surface hover:border-fg"
                  }`}
                >
                  {c.label}
                  <span className={`figures font-semibold ${on ? "" : "text-muted"}`}>{c.n}</span>
                </button>
              </li>
            );
          })}
        </ul>
      )}

      <div className="mt-6 grid gap-10 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <section aria-labelledby="results-heading" className="min-w-0">
          <div className="mb-2 flex flex-wrap items-baseline justify-between gap-3">
            <h2 id="results-heading" className="text-lg font-black" aria-live="polite">
              <span className="figures">{results.length}</span> {results.length === 1 ? "role" : "roles"}
              {active > 0 ? " match" : " open now"}
            </h2>
            {active > 0 && (
              <button type="button" onClick={() => update(EMPTY)} className="min-h-11 text-sm font-bold text-link underline">
                Clear filters
              </button>
            )}
          </div>
          {hiddenUnstated > 0 && (
            <p className="mb-3 flex flex-wrap items-center gap-x-3 border-[1.5px] border-signal bg-surface px-4 py-2.5 text-sm">
              <span>
                <strong className="figures">{hiddenUnstated}</strong> more {hiddenUnstated === 1 ? "posting matches" : "postings match"}{" "}
                but {hiddenUnstated === 1 ? "doesn’t" : "don’t"} say how long the term is.
              </span>
              <button type="button" onClick={() => update({ unstated: true })} className="min-h-11 font-bold text-link underline">
                Show them too
              </button>
            </p>
          )}
          {filters.unstated && filters.duration && filters.duration !== "not_stated" && (
            <p className="mb-3 text-sm text-muted">
              Including postings that don&rsquo;t state a length.{" "}
              <button type="button" onClick={() => update({ unstated: false })} className="min-h-11 font-bold text-link underline">
                Only stated lengths
              </button>
            </p>
          )}

          {results.length > 0 ? (
            <>
              <TimetableHead />
              <ul className="border-x border-t border-border md:border-t-0">
                {results.slice(0, limit).map((p) => (
                  <JobRow key={p.id} posting={p} dataDate={dataDate} />
                ))}
              </ul>
              <p className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted">
                <span>
                  <span className="plate-type mr-1.5 bg-go px-1.5 py-px text-[0.6875rem] text-go-fg">4 mo</span>length quoted from the posting
                </span>
                <span>
                  <span className="plate-type mr-1.5 border border-go px-1.5 text-[0.6875rem] text-go">4 mo</span>worked out from its dates
                </span>
                <span>
                  <span className="figures mr-1 font-black text-go">2d</span>new this week
                </span>
              </p>
              {results.length > limit && (
                <button
                  type="button"
                  onClick={() => setLimit((l) => l + PAGE)}
                  className="mt-4 min-h-12 w-full border-2 border-fg font-display font-extrabold hover:bg-fg hover:text-bg transition-colors"
                >
                  Show {Math.min(PAGE, results.length - limit)} more{" "}
                  <span className="figures font-semibold">({results.length - limit} left)</span>
                </button>
              )}
            </>
          ) : (
            <div className="border-2 border-dashed border-border px-6 py-10">
              <p className="font-display text-lg font-extrabold">No roles match {activeNames.join(" + ")}.</p>
              <p className="mt-1 text-muted">
                Remove one filter at a time below, or check{" "}
                <a href="/programs/" className="text-link underline">
                  Program watch
                </a>{" "}
                for programs that haven&rsquo;t posted yet.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {(["q", "term", "province", "duration", "track", "remote", "recent"] as const)
                  .filter((k) => filters[k])
                  .map((k) => (
                    <button
                      key={k}
                      type="button"
                      onClick={() => update({ [k]: EMPTY[k] })}
                      className="min-h-10 border-[1.5px] border-fg px-3 font-display text-sm font-bold hover:bg-fg hover:text-bg transition-colors"
                    >
                      Remove {k === "q" ? "search" : k === "duration" ? "length" : k === "recent" ? "new this week" : k === "track" ? "field" : k === "remote" ? "work mode" : k}
                      <Cross />
                    </button>
                  ))}
                <button type="button" onClick={() => update(EMPTY)} className="min-h-10 px-2 font-bold text-link underline">
                  Clear all
                </button>
              </div>
            </div>
          )}
        </section>
        {aside}
      </div>
    </>
  );
}

function BarSelect({
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
  return (
    <label className="flex min-h-14 flex-col justify-center border-r border-border px-3 last:border-r-0 md:min-w-44 md:border-l md:border-r-0 md:px-4">
      <span className="text-xs text-muted">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="-ml-1 min-h-7 w-full bg-transparent font-display text-[0.9375rem] font-bold outline-offset-4"
      >
        {children}
      </select>
    </label>
  );
}

function PanelSelect({
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
  return (
    <label className="block">
      <span className="block text-sm font-bold">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 block min-h-11 w-full border-[1.5px] border-border bg-surface px-2 text-base hover:border-fg transition-colors"
      >
        {children}
      </select>
    </label>
  );
}

function SearchIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true" className="shrink-0 text-muted">
      <circle cx="8.5" cy="8.5" r="6" fill="none" stroke="currentColor" strokeWidth="2" />
      <path d="M13 13l5 5" stroke="currentColor" strokeWidth="2" strokeLinecap="square" />
    </svg>
  );
}
