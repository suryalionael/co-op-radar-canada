import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, ArrowUpRight } from "@/components/Icons";
import { JobRow } from "@/components/JobRow";
import { TimetableHead } from "@/components/TimetableHead";
import { StatusPlate } from "@/components/StatusPlate";
import { WindowStrip } from "@/components/WindowStrip";
import { getCompanies, getCompany, getMeta, getPostings, getPrograms } from "@/lib/data";
import { formatDay, formatSector } from "@/lib/format";

export const dynamicParams = false;

export function generateStaticParams() {
  return getCompanies().map((c) => ({ slug: c.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const c = getCompany((await params).slug);
  return c ? { title: c.name, description: `${c.name}: open co-op and internship roles and when they usually hire.` } : {};
}

export default async function CompanyPage({ params }: { params: Promise<{ slug: string }> }) {
  const company = getCompany((await params).slug);
  if (!company) notFound();
  const meta = getMeta();
  const dataDate = meta.data_as_of.postings;
  const month = dataDate ? Number(dataDate.slice(5, 7)) : new Date().getMonth() + 1;
  const ids = new Set(company.posting_ids);
  const postings = getPostings().filter((p) => ids.has(p.id));
  const { programs, changes } = getPrograms();
  const watched = programs.filter((p) => company.program_ids.includes(p.program_id));
  const programChanges = changes.filter((ch) => company.program_ids.includes(ch.program_id)).slice(0, 5);

  return (
    <>
      <p className="text-sm">
        <Link href="/companies/" className="font-bold text-link underline">
          <ArrowLeft /> All companies
        </Link>
      </p>
      <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2">
        <h1 className="text-display font-black tracking-[-0.02em] break-words">{company.name}</h1>
        <StatusPlate company={company} />
      </div>
      {company.sector && <p className="mt-1 text-muted">{formatSector(company.sector)}</p>}
      {(company.website || company.careers_url) && (
        <p className="mt-2 flex flex-wrap gap-x-6">
          {company.website && (
            <a href={company.website} target="_blank" rel="noopener noreferrer" className="inline-flex min-h-11 items-center font-bold text-link underline">
              Website&nbsp;
              <ArrowUpRight />
            </a>
          )}
          {company.careers_url && (
            <a href={company.careers_url} target="_blank" rel="noopener noreferrer" className="inline-flex min-h-11 items-center font-bold text-link underline">
              Careers page&nbsp;
              <ArrowUpRight />
            </a>
          )}
        </p>
      )}

      <section aria-labelledby="calendar" className="mt-8 max-w-3xl">
        <h2 id="calendar" className="text-xl font-black">
          Hiring calendar
        </h2>
        <div className="mt-3">
          <WindowStrip window={company.window} currentMonth={month} size="lg" />
        </div>
        {company.window?.source === "researched" ? (
          <div className="mt-2 max-w-[58ch] text-sm text-muted">
            <p>Researched by the Co-op Radar team. These are the months this company usually hires students.</p>
            {company.hiring_note && <p className="mt-1 text-fg">{company.hiring_note}</p>}
            {company.hiring_source && (
              <p className="mt-1">
                Source:{" "}
                {/^https:\/\//i.test(company.hiring_source) ? (
                  <a href={company.hiring_source} target="_blank" rel="noopener noreferrer" className="font-bold text-link underline">
                    {company.hiring_source.replace(/^https:\/\/(www\.)?/i, "").slice(0, 48)}
                    &nbsp;
                    <ArrowUpRight />
                  </a>
                ) : (
                  company.hiring_source
                )}
              </p>
            )}
          </div>
        ) : (
          <p className="mt-2 max-w-[58ch] text-sm text-muted">
            {company.basis
              ? `Built ${company.basis}, by the month each one first appeared. The first day we read their board doesn’t count: everything already up looks new that day.`
              : "No student postings recorded yet."}
          </p>
        )}
      </section>

      <section aria-labelledby="open" className="mt-10">
        <div className="mb-3 flex flex-wrap items-baseline justify-between gap-3">
          <h2 id="open" className="text-xl font-black">
            <span className="figures">{postings.length}</span> open {postings.length === 1 ? "role" : "roles"}
          </h2>
          {company.board_url && (
            <a href={company.board_url} target="_blank" rel="noopener noreferrer" className="min-h-11 font-bold text-link underline">
              Their job board&nbsp;
              <ArrowUpRight />
            </a>
          )}
        </div>
        {postings.length ? (
          <>
            <TimetableHead />
            <ul className="border-x border-t border-border md:border-t-0">
              {postings.map((p) => (
                <JobRow key={p.id} posting={p} dataDate={dataDate} />
              ))}
            </ul>
          </>
        ) : (
          <p className="border-2 border-dashed border-border px-6 py-8 text-muted">
            Nothing open right now.{" "}
            {company.badge === "soon" ? "Their usual hiring months are coming up." : "Check back when their calendar comes around."}
          </p>
        )}
      </section>

      {watched.length > 0 && (
        <section aria-labelledby="watch" className="mt-10 max-w-3xl">
          <h2 id="watch" className="text-xl font-black">
            Program watch
          </h2>
          <ul className="mt-2 space-y-1">
            {watched.map((program) => (
              <li key={program.program_id}>
                <a href={program.url} target="_blank" rel="noopener noreferrer" className="font-bold text-link underline">
                  {program.name}&nbsp;
                  <ArrowUpRight />
                </a>{" "}
                <span className="text-sm text-muted">
                  {program.last_changed ? `changed ${formatDay(program.last_changed)}` : "no change recorded yet"}
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-sm text-muted">We check these pages every day and record when they change.</p>
          {programChanges.length > 0 && (
            <ul className="mt-3 border-t border-border">
              {programChanges.map((ch) => (
                <li key={ch.program_id + ch.changed_on + ch.change_excerpt} className="grid grid-cols-[5rem_1fr] gap-4 border-b border-border py-3 text-sm">
                  <span className="figures font-bold">{formatDay(ch.changed_on)}</span>
                  <span className="text-muted">{ch.change_excerpt}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </>
  );
}
