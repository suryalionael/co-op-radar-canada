"use client";

import { useId, useState } from "react";
import { EvidenceQuote } from "./EvidenceQuote";
import { ROW_COLUMNS } from "./TimetableHead";
import { ArrowUpRight } from "./Icons";
import {
  daysBetween,
  displayTitle,
  durationNote,
  formatAge,
  formatDay,
  formatPlate,
  REMOTE_LABELS,
  shortLocation,
  SOURCES,
} from "@/lib/format";
import type { Posting } from "@/lib/types";

/** One timetable line: when it appeared, what it is, the term and length the posting states, and Apply. */
export function JobRow({ posting: p, dataDate }: { posting: Posting; dataDate: string | null }) {
  const [open, setOpen] = useState(false);
  const detailsId = useId();
  const age = dataDate ? daysBetween(p.first_seen, dataDate) : null;
  const isNew = age !== null && age <= 6;
  const ambiguous = !p.terms.length && p.term_status === "ambiguous" ? p.evidence.term_ambiguous : undefined;
  const remote = REMOTE_LABELS[p.remote];
  const hasLength = p.duration_options_months.length > 0;
  const durationSpan = p.evidence.duration?.split(" | ")[0];
  const durationContext = p.duration_status === "stated" ? p.evidence.duration_context : undefined;
  const termContext = p.evidence.term_context;
  const showTermQuote = termContext && termContext !== p.title;
  const datesContext =
    p.duration_status === "inferred_from_dates" && p.evidence.term_dates && !termContext?.includes(p.evidence.term_dates)
      ? p.evidence.term_dates
      : undefined;
  const title = displayTitle(p.title, p.terms);
  const place = p.location_raw ? shortLocation(p.location_raw) : "Location not stated";
  const hasEvidence = true; // the raw title and location are always there to read

  return (
    <li className="border-b border-border bg-surface">
      <article aria-labelledby={`t-${p.id}`} className={`grid grid-cols-[3.25rem_minmax(0,1fr)] gap-x-4 gap-y-1.5 px-4 py-3 md:items-center md:py-2.5 md:gap-y-0 md:px-5 ${ROW_COLUMNS}`}>
        <p className="row-span-2 text-right md:row-span-1">
          <span className="sr-only">Posted </span>
          <span className={`figures block text-xl font-black leading-none ${isNew ? "text-go" : ""}`}>
            {age === null ? "—" : formatAge(age)}
          </span>
          <span className="figures mt-1 block text-xs text-muted">{formatDay(p.first_seen)}</span>
        </p>

        <div className="min-w-0">
          <h3 id={`t-${p.id}`} className="font-sans text-base font-bold leading-snug break-words" title={title !== p.title ? p.title : undefined}>
            {title}
          </h3>
          <p className="flex min-w-0 items-baseline gap-2 text-sm text-muted">
            <span className="truncate">
              {p.employer} · {place}
              {remote ? ` · ${remote}` : ""}
            </span>
            {hasEvidence && (
              <button
                type="button"
                onClick={() => setOpen((o) => !o)}
                aria-expanded={open}
                aria-controls={detailsId}
                className="-my-1 min-h-6 shrink-0 py-1 font-bold underline decoration-dotted underline-offset-4 hover:text-fg"
              >
                {open ? "hide source" : "source"}
                <span className="sr-only"> for {title}</span>
              </button>
            )}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 md:contents">
        <p className="facts text-[0.9375rem]">
          <span className="sr-only">Term: </span>
          {p.terms.length ? (
            p.terms.join(" / ")
          ) : (
            <span className="font-sans text-sm font-normal italic text-muted"><span className="md:sr-only">term </span>{ambiguous ? "unclear" : "not stated"}</span>
          )}
        </p>

        <p>
          <span className="sr-only">Length: </span>
          {hasLength ? (
            <span
              className={`plate-type inline-block px-2 py-0.5 text-[0.8125rem] ${
                p.duration_status === "stated" ? "bg-go text-go-fg" : "border-[1.5px] border-go text-go"
              }`}
              title={durationNote(p)}
            >
              {formatPlate(p.duration_options_months, p.duration_is_range)}
            </span>
          ) : (
            <span className="text-sm italic text-muted"><span className="md:sr-only">length </span>not stated</span>
          )}
        </p>

        <p className="figures font-bold">
          <span className="sr-only">Province: </span>
          <abbr title={p.province === "REMOTE_CA" ? "Remote, anywhere in Canada" : undefined} className="no-underline">
            {p.province === "REMOTE_CA" ? "Remote" : p.province === "UNKNOWN" ? "—" : p.province}
          </abbr>
        </p>

        <div className="flex w-full items-center justify-end md:w-auto">
          <a
            href={p.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex min-h-11 items-center font-display font-extrabold text-link underline decoration-2 underline-offset-4 hover:decoration-[3px]"
          >
            Apply&nbsp;<ArrowUpRight />
            <span className="sr-only"> to {p.title} at {p.employer} (opens the employer&rsquo;s site)</span>
          </a>
        </div>
        </div>
      </article>

      {open && (
        <div id={detailsId} className="row-open border-t border-dashed border-border px-4 pb-4 pt-3 md:pl-[6.5rem] md:pr-5">
          <p className="mb-1.5 flex max-w-[75ch] gap-3 text-sm">
            <span className="plate-type w-14 shrink-0 pt-0.5 text-[0.6875rem] text-muted">Posted</span>
            <span>
              {p.title} · {p.location_raw || "location not stated"}
            </span>
          </p>
          {showTermQuote && <EvidenceQuote label="Term" context={termContext} span={p.evidence.term} />}
          {ambiguous && (
            <p className="mt-1 text-sm text-warning">
              The posting says &ldquo;{ambiguous.split(" | ")[0]}&rdquo;, which means different months at different
              schools. Check the dates with the employer.
            </p>
          )}
          {p.flag_term_in_past && (
            <p className="mt-1 text-sm text-warning">
              The term named here had already ended when this was posted. Check the dates with the employer.
            </p>
          )}
          {durationContext && <EvidenceQuote label="Length" context={durationContext} span={durationSpan} />}
          {datesContext && <EvidenceQuote label="Dates" context={datesContext} span={datesContext} />}
          <p className="mt-2 text-xs text-muted">
            {durationNote(p)} · first seen {p.first_seen} · via {SOURCES[p.source] ?? p.source}
          </p>
        </div>
      )}
    </li>
  );
}
