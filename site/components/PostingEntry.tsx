import { EvidenceQuote } from "./EvidenceQuote";
import { durationNote, formatDuration, REMOTE_LABELS, SOURCES } from "@/lib/format";
import type { Posting } from "@/lib/types";

export function PostingEntry({ posting: p, isNew }: { posting: Posting; isNew: boolean }) {
  const termText = p.terms.length ? p.terms.join(" / ") : "Term not stated";
  const durationText = p.duration_options_months.length ? formatDuration(p.duration_options_months) : null;
  const remote = REMOTE_LABELS[p.remote];
  const durationSpan = p.evidence.duration?.split(" | ")[0];
  const durationContext = p.duration_status === "stated" ? p.evidence.duration_context : undefined;
  const termContext = p.evidence.term_context;
  // Skip quotes that would only repeat what is already on screen.
  const showTermQuote = termContext && termContext !== p.title;
  const datesContext =
    p.duration_status === "inferred_from_dates" && p.evidence.term_dates && !termContext?.includes(p.evidence.term_dates)
      ? p.evidence.term_dates
      : undefined;

  return (
    <article className="border-b border-border py-6 first:pt-2" aria-labelledby={`t-${p.id}`}>
      <h3 id={`t-${p.id}`} className="text-lg font-semibold">
        <a href={p.url} target="_blank" rel="noopener noreferrer" className="hover:text-accent transition-colors">
          {p.title}
        </a>
      </h3>
      <p className="mt-1 text-base">
        <span className="font-medium">{p.employer}</span>
        <span className="text-muted">
          {" · "}
          {p.location_raw || "Location not stated"}
          {remote ? ` · ${remote}` : ""}
        </span>
      </p>

      <p className="facts mt-3 text-base">
        <span>{termText}</span>
        <span aria-hidden="true" className="text-muted">
          {" · "}
        </span>
        <span className={durationText ? undefined : "text-warning"}>{durationText ?? "Duration not stated"}</span>
      </p>
      {showTermQuote && <EvidenceQuote context={termContext} span={p.evidence.term} />}
      {durationContext && <EvidenceQuote context={durationContext} span={durationSpan} />}
      {datesContext && <EvidenceQuote context={datesContext} span={datesContext} />}

      <p className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
        <span className={p.duration_status === "not_stated" ? "text-warning" : "text-success"}>
          {durationNote(p)}
        </span>
        <span className="font-mono text-muted tabular">
          first seen {p.first_seen}
          {isNew && <span className="ml-2 text-accent">new this week</span>}
        </span>
        <span className="font-mono text-muted">via {SOURCES[p.source] ?? p.source}</span>
        <a
          href={p.url}
          target="_blank"
          rel="noopener noreferrer"
          className="ml-auto inline-flex min-h-11 items-center font-medium text-accent underline"
        >
          View posting<span aria-hidden="true">&nbsp;↗</span>
          <span className="sr-only"> (opens the employer&rsquo;s site)</span>
        </a>
      </p>
    </article>
  );
}
