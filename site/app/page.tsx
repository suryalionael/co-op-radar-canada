import Link from "next/link";
import { ArrowRight } from "@/components/Icons";
import { JobBoard } from "@/components/JobBoard";
import { StatusPlate } from "@/components/StatusPlate";
import { WindowStrip } from "@/components/WindowStrip";
import { getCompanies, getMeta, getPostings } from "@/lib/data";

export default function Home() {
  const postings = getPostings();
  const meta = getMeta();
  const c = meta.counts;
  const dataDate = meta.data_as_of.postings;
  const month = dataDate ? Number(dataDate.slice(5, 7)) : new Date().getMonth() + 1;
  const companies = getCompanies();
  const withWindow = companies.filter((co) => co.window && co.badge !== "quiet").slice(0, 3);
  const busiest = companies.filter((co) => co.open_count > 0 && !withWindow.includes(co)).slice(0, 6);

  return (
    <>
      <div className="grid items-end gap-x-12 gap-y-3 pb-6 md:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
        <h1 className="text-display font-black tracking-[-0.02em]">
          Your next work term, <span className="bg-signal px-2 text-signal-fg [box-decoration-break:clone]">on schedule.</span>
        </h1>
        <p className="max-w-[46ch] text-lg text-muted">
          Co-ops and internships from {c.companies ?? c.employer_boards_tracked} Canadian employers, checked daily.{" "}
          <span className="hidden sm:inline">
            Every term and length is quoted from the posting itself, and if a posting doesn&rsquo;t say, neither do we.
          </span>
        </p>
      </div>

      {postings.length === 0 ? (
        <section className="max-w-2xl border-2 border-dashed border-border p-6">
          <h2 className="text-xl font-black">No postings yet</h2>
          <p className="mt-2">
            The daily pipeline hasn&rsquo;t published its first set of postings. Once it runs, open co-op and internship
            postings from {c.employer_boards_tracked} employer job boards will appear here.
          </p>
          <p className="mt-2 text-muted">
            Large banks, insurers and governments don&rsquo;t publish postings through a public API, so they are covered
            by{" "}
            <Link className="text-link underline" href="/programs/">
              Program watch
            </Link>{" "}
            instead.
          </p>
        </section>
      ) : (
        <JobBoard
          postings={postings}
          dataDate={dataDate}
          aside={
            <aside aria-labelledby="calendar-heading" className="lg:sticky lg:top-6 lg:self-start lg:pt-1">
              <h2 id="calendar-heading" className="text-xl font-black">
                Hiring calendar
              </h2>
              <p className="mt-1 text-sm text-muted">The months each company&rsquo;s student postings appear.</p>
              {withWindow.length > 0 && (
                <ul className="mt-4 space-y-3">
                  {withWindow.map((co) => (
                    <li key={co.slug} className="border border-border bg-surface p-4">
                      <div className="mb-3 flex items-start justify-between gap-3">
                        <Link href={`/companies/${co.slug}/`} className="font-display text-base font-extrabold hover:text-link hover:underline">
                          {co.name}
                        </Link>
                        <StatusPlate company={co} />
                      </div>
                      <WindowStrip window={co.window} currentMonth={month} />
                    </li>
                  ))}
                </ul>
              )}
              <h3 className="mt-6 font-display text-base font-extrabold">Most roles open now</h3>
              <ul className="mt-2 border-t border-border">
                {busiest.map((co) => (
                  <li key={co.slug} className="flex items-center justify-between gap-3 border-b border-border py-2">
                    <Link href={`/companies/${co.slug}/`} className="min-h-8 font-bold hover:text-link hover:underline">
                      {co.name}
                    </Link>
                    <span className="figures text-sm font-bold">{co.open_count}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-xs text-muted">
                We started reading boards in October 2026, so most calendars fill in over the season.
              </p>
              <Link
                href="/companies/"
                className="mt-2 inline-flex min-h-11 items-center font-display font-extrabold text-link underline decoration-2 underline-offset-4"
              >
                All {c.companies ?? ""} companies&nbsp;
                <ArrowRight />
              </Link>
            </aside>
          }
        />
      )}
    </>
  );
}
