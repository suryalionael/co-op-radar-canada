"use client";

import { useId, useState } from "react";
import { EvidenceQuote } from "./EvidenceQuote";
import { ROW_COLUMNS } from "./TimetableHead";
import { daysBetween, durationNote, formatAge, formatDay, formatPlate, REMOTE_LABELS, SOURCES } from "@/lib/format";
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
  const hasEvidence = Boolean(showTermQuote || durationContext || datesContext || ambiguous || p.flag_term_in_past);

  return (
    <li className="border-b border-border bg-surface">
      <article aria-labelledby={`t-${p.id}`} className={`grid grid-cols-[4rem_minmax(0,1fr)] gap-x-4 gap-y-2 px-4 py-3.5 md:items-center md:gap-y-0 md:px-5 ${ROW_COLUMNS}`}>
        <p className="row-span-3 md:row-span-1">
          <span className="sr-only">Posted </span>
          <span className={`figures block text-xl font-black leading-none ${isNew ? "text-go" : ""}`}>
            {age === null ? "—" : formatAge(age)}
          </span>
          <span className="figures mt-1 block text-xs text-muted">{formatDay(p.first_seen)}</span>
        </p>

        <div className="min-w-0">
          <h3 id={`t-${p.id}`} className="font-sans text-base font-bold leading-snug">
            {p.title}
          </h3>
          <p className="truncate text-sm text-muted">
            {p.employer} · {p.location_raw || "Location not stated"}
            {remote ? ` · ${remote}` : ""}
          </p>
          {hasEvidence && (
            <button
              type="button"
              onClick={() => setOpen((o) => !o)}
              aria-expanded={open}
              aria-controls={detailsId}
              className="mt-0.5 min-h-8 text-xs font-bold text-muted underline decoration-dotted underline-offset-4 hover:text-fg"
            >
              {open ? "Hide the posting's words" : "Show the posting's words"}
            </button>
          )}
        </div>

        <p className="facts text-[0.9375rem]">
          <span className="sr-only">Term: </span>
          {p.terms.length ? (
            p.terms.join(" / ")
          ) : (
            <span className="font-sans font-normal italic text-muted">{ambiguous ? "Term unclear" : "Not stated"}</span>
          )}
        </p>

        <p className="flex flex-wrap items-center gap-2 md:block">
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
            <span className="text-sm italic text-muted">not stated</span>
          )}
          <span className="figures text-sm text-muted md:hidden">
            {p.province === "REMOTE_CA" ? "Remote CA" : p.province}
          </span>
        </p>

        <p className="figures hidden font-bold md:block">
          <span className="sr-only">Province: </span>
          {p.province === "REMOTE_CA" ? "Rem." : p.province === "UNKNOWN" ? "—" : p.province}
        </p>

        <div className="col-start-2 flex items-center gap-4 md:col-start-auto md:justify-end">
          <a
            href={p.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex min-h-11 items-center font-display font-extrabold text-link underline decoration-2 underline-offset-4 hover:decoration-[3px]"
          >
            Apply<span aria-hidden="true">&nbsp;↗</span>
            <span className="sr-only"> to {p.title} at {p.employer} (opens the employer&rsquo;s site)</span>
          </a>
        </div>
      </article>

      {open && (
        <div id={detailsId} className="row-open border-t border-dashed border-border px-4 pb-4 pt-3 md:pl-[6.5rem] md:pr-5">
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
