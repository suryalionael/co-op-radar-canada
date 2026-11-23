import Link from "next/link";
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
  const hiring = getCompanies()
    .filter((co) => co.badge !== "quiet")
    .slice(0, 5);

  return (
    <>
      <div className="grid items-end gap-x-12 gap-y-4 pb-8 md:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
        <h1 className="text-display font-black tracking-[-0.02em]">
          Your next work term, <span className="bg-signal px-2 text-signal-fg [box-decoration-break:clone]">on schedule.</span>
        </h1>
        <p className="max-w-[46ch] text-lg text-muted">
          Co-ops and internships from {c.employer_boards_tracked} Canadian tech employers, checked daily. Every term
          and length is quoted from the posting itself, and if a posting doesn&rsquo;t say, neither do we.
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
            <aside aria-labelledby="calendar-heading" className="lg:pt-1">
              <h2 id="calendar-heading" className="text-xl font-black">
                Hiring calendar
              </h2>
              <p className="mt-1 text-sm text-muted">Who&rsquo;s posting now, and the months they usually do.</p>
              <ul className="mt-4 space-y-3">
                {hiring.map((co) => (
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
              <Link
                href="/companies/"
                className="mt-4 inline-flex min-h-11 items-center font-display font-extrabold text-link underline decoration-2 underline-offset-4"
              >
                All {c.companies ?? ""} companies<span aria-hidden="true">&nbsp;→</span>
              </Link>
            </aside>
          }
        />
      )}
    </>
  );
}
