import Link from "next/link";
import { ArrowUpRight } from "./Icons";
import { ROW_COLUMNS } from "./TimetableHead";
import {
  daysBetween,
  displayTitle,
  durationNote,
  formatAge,
  formatDay,
  formatPlate,
  REMOTE_LABELS,
  shortLocation,
} from "@/lib/format";
import type { Posting } from "@/lib/types";

/**
 * One timetable line. The title is a link to the posting's page and stretches over the whole row;
 * Apply sits above it and goes straight to the employer.
 */
export function JobRow({ posting: p, dataDate }: { posting: Posting; dataDate: string | null }) {
  const age = dataDate ? daysBetween(p.first_seen, dataDate) : null;
  const isNew = age !== null && age <= 6;
  const ambiguous = !p.terms.length && p.term_status === "ambiguous";
  const remote = REMOTE_LABELS[p.remote];
  const hasLength = p.duration_options_months.length > 0;
  const title = displayTitle(p.title, p.terms);
  const place = p.location_raw ? shortLocation(p.location_raw) : "Location not stated";

  return (
    <li className="relative border-b border-border bg-surface transition-colors hover:bg-bg">
      <article
        aria-labelledby={`t-${p.id}`}
        className={`grid grid-cols-[3.25rem_minmax(0,1fr)] gap-x-4 gap-y-1.5 px-4 py-3 md:items-center md:gap-y-0 md:px-5 md:py-2.5 ${ROW_COLUMNS}`}
      >
        <p className="row-span-2 text-right md:row-span-1">
          <span className="sr-only">Posted </span>
          <span className={`figures block text-xl font-black leading-none ${isNew ? "text-go" : ""}`}>
            {age === null ? "—" : formatAge(age)}
          </span>
          <span className="figures mt-1 block text-xs text-muted">{formatDay(p.first_seen)}</span>
        </p>

        <div className="min-w-0">
          <h3 id={`t-${p.id}`} className="font-sans text-base font-bold leading-snug break-words">
            <Link
              href={`/jobs/${p.id}/`}
              className="after:absolute after:inset-0 after:content-[''] hover:text-link hover:underline"
            >
              {title}
            </Link>
          </h3>
          <p className="truncate text-sm text-muted">
            {p.employer} · {place}
            {remote ? ` · ${remote}` : ""}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 md:contents">
          <p className="facts text-[0.9375rem]">
            <span className="sr-only">Term: </span>
            {p.terms.length ? (
              p.terms.join(" / ")
            ) : (
              <span className="font-sans text-sm font-normal italic text-muted">
                <span className="md:sr-only">term </span>
                {ambiguous ? "unclear" : "not stated"}
              </span>
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
              <span className="text-sm italic text-muted">
                <span className="md:sr-only">length </span>not stated
              </span>
            )}
          </p>

          <p className="figures font-bold">
            <span className="sr-only">Province: </span>
            <abbr title={p.province === "REMOTE_CA" ? "Remote, anywhere in Canada" : undefined} className="no-underline">
              {p.province === "REMOTE_CA" ? "Remote" : p.province === "UNKNOWN" ? "—" : p.province}
            </abbr>
          </p>

          <div className="relative z-10 flex w-full items-center justify-end md:w-auto">
            {/^https?:\/\//i.test(p.url) && (
            <a
              href={p.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex min-h-11 items-center font-display font-extrabold text-link underline decoration-2 underline-offset-4 hover:decoration-[3px]"
            >
              Apply&nbsp;
              <ArrowUpRight />
              <span className="sr-only">
                {" "}
                to {p.title} at {p.employer} (opens the employer&rsquo;s site)
              </span>
            </a>
            )}
          </div>
        </div>
      </article>
    </li>
  );
}
