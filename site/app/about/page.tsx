import type { Metadata } from "next";
import { getMeta } from "@/lib/data";

export const metadata: Metadata = {
  title: "About",
  description: "How Co-op Radar Canada collects and checks postings, and what it does not cover.",
};

const REPO = "https://github.com/suryalionael/co-op-radar-canada";

export default function AboutPage() {
  const c = getMeta().counts;
  return (
    <article className="max-w-2xl space-y-8 text-lg">
      <header>
        <h1 className="text-3xl font-semibold">About</h1>
        <p className="mt-3 text-muted">
          Co-op Radar Canada is a free tracker for Canadian co-op and internship postings, built by students for
          students.
        </p>
      </header>

      <section>
        <h2 className="text-2xl font-semibold">Why it exists</h2>
        <p className="mt-2">
          Schools approve only specific work terms, so a co-op student needs to know two things about every posting:
          which term it is for, and how long it lasts. Most postings bury this in the description, and most
          internship trackers don&rsquo;t record it at all.
        </p>
      </section>

      <section>
        <h2 className="text-2xl font-semibold">How it works</h2>
        <ol className="mt-2 list-decimal space-y-2 pl-6">
          <li>
            Once a day, we read the public job boards (Greenhouse, Lever and Ashby) of {c.employer_boards_tracked}{" "}
            employers and keep postings in Canada.
          </li>
          <li>
            Simple, published rules find the term, duration and province in each posting, and keep the exact words
            they came from. You can see those words under every posting.
          </li>
          <li>
            If a posting doesn&rsquo;t state its duration, we show <strong>duration not stated</strong>. We never
            guess from what an employer usually offers.
          </li>
          <li>
            Program watch checks {c.programs_watched} student-program pages daily and records the day each one
            changes.
          </li>
        </ol>
      </section>

      <section className="rounded-md bg-surface p-6">
        <h2 className="text-2xl font-semibold">What it does not cover</h2>
        <p className="mt-2">
          This site does not list every co-op in Canada. Most large Canadian banks, insurers, pension funds and
          governments post jobs on systems with no public posting API, such as Workday. Their postings{" "}
          <strong>do not appear here automatically</strong>. We cover them through Program watch and link to their own
          career pages instead.
        </p>
        <p className="mt-2">
          We never collect anything from LinkedIn, Indeed, Glassdoor or Reddit; their terms don&rsquo;t allow it.
        </p>
      </section>

      <section>
        <h2 className="text-2xl font-semibold">How accurate is it?</h2>
        <p className="mt-2">
          We check the extraction rules against postings labelled by hand and publish the results, with counts and
          confidence intervals, in the{" "}
          <a className="text-accent underline" href={`${REPO}/blob/main/docs/evaluation.md`}>
            evaluation report
          </a>
          . A wrong duration is treated as worse than &ldquo;not stated&rdquo;.
        </p>
      </section>

      <section>
        <h2 className="text-2xl font-semibold">Who made it</h2>
        <p className="mt-2">
          Lionael Surya (Lio) and Ei Htoo, Seneca Polytechnic, Toronto. The code, rules and data are open on{" "}
          <a className="text-accent underline" href={REPO}>
            GitHub
          </a>
          . Suggestions for employers or program pages to track are welcome as{" "}
          <a className="text-accent underline" href={`${REPO}/issues`}>
            issues
          </a>
          .
        </p>
      </section>

      <section className="text-base text-muted">
        <h2 className="text-xl font-semibold text-fg">Disclaimer</h2>
        <p className="mt-2">
          Co-op Radar Canada is an independent student project. It is not affiliated with, endorsed by, or sponsored
          by any employer, job board, school or government listed on the site. Always confirm details on the original
          posting before applying. Visits are counted with Vercel Web Analytics, which uses no cookies.
        </p>
      </section>
    </article>
  );
}
