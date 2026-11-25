import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { EvidenceQuote } from "@/components/EvidenceQuote";
import { ArrowLeft, ArrowUpRight } from "@/components/Icons";
import { getDescription, getPosting, getPostings } from "@/lib/data";
import { durationNote, formatDay, formatPlate, REMOTE_LABELS, SOURCES } from "@/lib/format";
import type { Posting } from "@/lib/types";

export const dynamicParams = false;

export function generateStaticParams() {
  return getPostings().map((p) => ({ id: p.id }));
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const p = getPosting((await params).id);
  return p
    ? { title: `${p.title} · ${p.employer}`, description: `${p.title} at ${p.employer}. ${p.location_raw}.` }
    : {};
}

function ApplyButton({ p, where }: { p: Posting; where: "top" | "bottom" }) {
  if (!/^https?:\/\//i.test(p.url)) return null;
  return (
    <a
      href={p.url}
      target="_blank"
      rel="noopener noreferrer"
      data-apply={where}
      className="inline-flex min-h-12 items-center gap-2 bg-go px-7 font-display text-lg font-extrabold text-go-fg transition-colors hover:bg-fg hover:text-bg"
    >
      Apply on {p.employer}&rsquo;s site
      <ArrowUpRight />
      <span className="sr-only"> (opens in a new tab)</span>
    </a>
  );
}

export default async function JobPage({ params }: { params: Promise<{ id: string }> }) {
  const p = getPosting((await params).id);
  if (!p) notFound();
  // Sanitised by pipeline/sanitize.py when it was written; see site/lib/data.ts.
  const description = getDescription(p.id);
  const remote = REMOTE_LABELS[p.remote];
  const ambiguous = !p.terms.length && p.term_status === "ambiguous" ? p.evidence.term_ambiguous : undefined;
  const hasLength = p.duration_options_months.length > 0;
  const termContext = p.evidence.term_context;
  const showTermQuote = termContext && termContext !== p.title;
  const durationSpan = p.evidence.duration?.split(" | ")[0];
  const durationContext = p.duration_status === "stated" ? p.evidence.duration_context : undefined;
  const datesContext =
    p.duration_status === "inferred_from_dates" && p.evidence.term_dates && !termContext?.includes(p.evidence.term_dates)
      ? p.evidence.term_dates
      : undefined;
  const chip = "border-[1.5px] border-border bg-surface px-2.5 py-1 text-sm font-bold";

  return (
    <article className="mx-auto max-w-[46rem]">
      <p>
        <Link href="/" className="inline-flex min-h-11 items-center font-bold text-link underline">
          <ArrowLeft />
          &nbsp;All jobs
        </Link>
      </p>

      <header className="mt-2 flex items-start gap-4">
        <div
          aria-hidden="true"
          className="grid size-14 shrink-0 place-items-center bg-ink-bar font-display text-2xl font-black text-ink-bar-fg"
        >
          {p.employer.charAt(0).toUpperCase()}
        </div>
        <div className="min-w-0">
          <h1 className="break-words text-[clamp(1.75rem,1.2rem+2vw,2.5rem)] font-black tracking-[-0.02em]">{p.title}</h1>
          <p className="mt-1 text-lg">
            <Link href={`/companies/${p.employer_id}/`} className="font-bold underline decoration-dotted underline-offset-4 hover:text-link">
              {p.employer}
            </Link>
            <span className="text-muted"> is hiring</span>
          </p>
        </div>
      </header>

      <ul className="mt-5 flex flex-wrap gap-2" aria-label="At a glance">
        <li className={chip}>{p.location_raw || "Location not stated"}</li>
        {remote && <li className={chip}>{remote}</li>}
        {p.terms.length > 0 && <li className={chip}>{p.terms.join(" / ")}</li>}
        <li
          className={`plate-type px-2.5 py-1 text-sm ${
            !hasLength
              ? "border-[1.5px] border-dashed border-border text-muted"
              : p.duration_status === "stated"
                ? "bg-go text-go-fg"
                : "border-[1.5px] border-go text-go"
          }`}
        >
          {hasLength ? formatPlate(p.duration_options_months, p.duration_is_range) : "length not stated"}
        </li>
      </ul>

      <div className="mt-6">
        <ApplyButton p={p} where="top" />
      </div>

      <section aria-labelledby="facts" className="mt-8 border-[1.5px] border-fg bg-surface p-5">
        <h2 id="facts" className="text-lg font-black">
          What the posting says
        </h2>
        <p className="mt-1 text-sm text-muted">
          We read the term and length from the posting itself. If it doesn&rsquo;t say, we don&rsquo;t guess.
        </p>
        <dl className="mt-4 space-y-4">
          <div>
            <dt className="plate-type text-xs text-muted">Term</dt>
            <dd className="mt-1 font-bold">
              {p.terms.length ? p.terms.join(" / ") : <span className="font-normal italic text-muted">{ambiguous ? "unclear" : "not stated"}</span>}
            </dd>
            {showTermQuote && <EvidenceQuote context={termContext} span={p.evidence.term} />}
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
          </div>
          <div>
            <dt className="plate-type text-xs text-muted">Length</dt>
            <dd className="mt-1 font-bold">
              {hasLength ? (
                <>
                  {formatPlate(p.duration_options_months, p.duration_is_range)}{" "}
                  <span className="text-sm font-normal text-muted">· {durationNote(p)}</span>
                </>
              ) : (
                <span className="font-normal italic text-muted">not stated</span>
              )}
            </dd>
            {durationContext && <EvidenceQuote context={durationContext} span={durationSpan} />}
            {datesContext && <EvidenceQuote context={datesContext} span={datesContext} />}
          </div>
        </dl>
      </section>

      <section aria-labelledby="about-role" className="mt-10">
        <h2 id="about-role" className="sr-only">
          About the role
        </h2>
        {description ? (
          <div className="posting-prose" dangerouslySetInnerHTML={{ __html: description }} />
        ) : (
          <p className="border-2 border-dashed border-border px-5 py-6 text-muted">
            The full text isn&rsquo;t available here. Read it on the employer&rsquo;s site.
          </p>
        )}
      </section>

      <div className="mt-10">
        <ApplyButton p={p} where="bottom" />
      </div>

      <p className="mt-8 max-w-[52ch] border-t border-border pt-4 text-sm text-muted">
        Posting text from {p.employer}&rsquo;s {SOURCES[p.source] ?? p.source} job board, first seen {formatDay(p.first_seen)}.
        Always confirm details on the employer&rsquo;s site.
      </p>
    </article>
  );
}
