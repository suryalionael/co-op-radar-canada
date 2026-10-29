import type { Metadata } from "next";
import { EvidenceQuote } from "@/components/EvidenceQuote";
import { getMeta, getPrograms } from "@/lib/data";
import { daysBetween } from "@/lib/format";

export const metadata: Metadata = {
  title: "Program watch",
  description: "Student-program pages from Canadian employers and governments, checked daily for changes.",
};

export default function ProgramsPage() {
  const { programs, changes } = getPrograms();
  const asOf = getMeta().data_as_of.programs;
  const names = Object.fromEntries(programs.map((p) => [p.program_id, p.name]));
  const recent = (date: string | null) => date !== null && asOf !== null && daysBetween(date, asOf) <= 6;

  return (
    <>
      <div className="max-w-3xl">
        <h1 className="text-3xl font-semibold">Program watch</h1>
        <p className="mt-3 text-lg text-muted">
          Banks, insurers, utilities and governments often announce student hiring on their own pages before postings
          appear. We check these pages every day and record the day each one changes. A change is a hint, not an
          opening: open the page to see what&rsquo;s new.
        </p>
      </div>

      {programs.length === 0 ? (
        <section className="mt-10 max-w-2xl rounded-md bg-surface p-6">
          <h2 className="text-xl font-semibold">No pages watched yet</h2>
          <p className="mt-2">
            Program pages are added once each address has been checked by hand. The first ones will appear here after
            the next daily run.
          </p>
        </section>
      ) : (
        <div className="mt-10 grid gap-12 lg:grid-cols-[minmax(0,1fr)_20rem]">
          <section aria-labelledby="pages-heading">
            <h2 id="pages-heading" className="border-b border-fg pb-2 text-xl font-semibold">
              <span className="tabular">{programs.length}</span> pages
            </h2>
            {programs.map((p) => (
              <article key={p.program_id} className="border-b border-border py-5">
                <h3 className="text-lg font-semibold">
                  <a href={p.url} target="_blank" rel="noopener noreferrer" className="hover:text-accent transition-colors">
                    {p.name}
                    <span aria-hidden="true" className="text-muted">
                      &nbsp;↗
                    </span>
                  </a>
                </h3>
                <p className="facts mt-2 text-base">
                  {p.last_changed ? (
                    <span className={recent(p.last_changed) ? "text-accent" : undefined}>
                      Changed {p.last_changed}
                      {recent(p.last_changed) ? " · this week" : ""}
                    </span>
                  ) : (
                    <span className="text-muted">No change since we started watching</span>
                  )}
                  {p.expected_open && <span> · Expected to open {p.expected_open}</span>}
                </p>
                {p.change_excerpt && <EvidenceQuote context={p.change_excerpt} />}
                <p className="mt-2 flex flex-wrap gap-x-3 text-sm">
                  <span className="font-mono text-muted tabular">last checked {p.last_checked ?? "never"}</span>
                  {!p.last_fetch_ok && p.last_checked && (
                    <span className="text-warning">Last check failed; showing the last good result</span>
                  )}
                  {p.expected_open_src && (
                    <a className="text-accent underline" href={p.expected_open_src} target="_blank" rel="noopener noreferrer">
                      Source for the opening date
                    </a>
                  )}
                </p>
              </article>
            ))}
          </section>

          <section aria-labelledby="log-heading">
            <h2 id="log-heading" className="border-b border-fg pb-2 text-xl font-semibold">
              Change log
            </h2>
            {changes.length === 0 ? (
              <p className="py-5 text-muted">No changes recorded yet.</p>
            ) : (
              <ol className="divide-y divide-border">
                {changes.map((c, i) => (
                  <li key={`${c.program_id}-${c.changed_on}-${i}`} className="py-4">
                    <p className="font-mono text-sm text-muted tabular">
                      {c.changed_on}
                      {c.kind === "manual_note" ? " · note" : ""}
                    </p>
                    <p className="mt-1 font-medium">{names[c.program_id] ?? c.program_id}</p>
                    <p className="mt-1 text-sm text-muted">{c.change_excerpt}</p>
                  </li>
                ))}
              </ol>
            )}
          </section>
        </div>
      )}
    </>
  );
}
