import { Analytics } from "@vercel/analytics/next";
import type { Metadata, Viewport } from "next";
import Link from "next/link";
import { Nav } from "@/components/Nav";
import { getMeta, isSampleData } from "@/lib/data";
import { formatDay } from "@/lib/format";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Co-op Radar Canada", template: "%s · Co-op Radar Canada" },
  description:
    "Canadian tech co-op and internship postings with the term and length quoted from the posting, plus when each company usually hires.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#036d38" },
    { media: "(prefers-color-scheme: dark)", color: "#074120" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const meta = getMeta();
  const asOf = meta.data_as_of.postings;
  return (
    <html lang="en-CA">
      <body className="min-h-screen bg-bg text-fg">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-10 focus:bg-signal focus:p-2 focus:text-signal-fg"
        >
          Skip to content
        </a>
        {isSampleData && (
          <p className="bg-signal px-4 py-2 text-center text-sm font-bold text-signal-fg">
            Sample data for local development. These postings are fictional.
          </p>
        )}
        <header className="bg-rail text-rail-fg">
          <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-8 gap-y-1 px-4 py-2 md:px-10">
            <Link href="/" className="flex min-h-11 items-center gap-2.5" aria-label="Co-op Radar Canada, home">
              <RadarMark />
              <span className="font-display text-[1.375rem] font-black tracking-tight">Co-op Radar</span>
            </Link>
            <Nav />
            <p className="figures ml-auto hidden text-sm text-rail-muted lg:block">
              {asOf ? (
                <>
                  <strong className="font-bold text-rail-fg">{meta.counts.open_student_postings}</strong> open roles<span className="mx-2" aria-hidden="true">·</span>
                  <strong className="font-bold text-rail-fg">{meta.counts.employers_with_postings}</strong>{" "}
                  companies hiring<span className="mx-2" aria-hidden="true">·</span>updated {formatDay(asOf)}
                </>
              ) : (
                "No postings collected yet"
              )}
            </p>
          </div>
        </header>
        <main id="main" className="mx-auto max-w-7xl px-4 pb-20 pt-8 md:px-10">
          {children}
        </main>
        <footer className="mx-auto max-w-7xl px-4 text-sm text-muted md:px-10">
          <p className="border-t border-border py-6">
            An independent student project, not affiliated with any employer, school or government listed. Always
            confirm details on the original posting.{" "}
            <a className="text-link underline" href="https://github.com/suryalionael/co-op-radar-canada">
              Source code and data
            </a>
            .
          </p>
        </footer>
        <Analytics />
      </body>
    </html>
  );
}

/** A radar sweep drawn as signage: two rings and a beam. */
function RadarMark() {
  return (
    <svg width="30" height="30" viewBox="0 0 30 30" aria-hidden="true">
      <circle cx="15" cy="15" r="14" fill="var(--signal)" />
      <circle cx="15" cy="15" r="9" fill="none" stroke="var(--rail)" strokeWidth="2.5" />
      <circle cx="15" cy="15" r="3" fill="var(--rail)" />
      <path d="M15 15 L26 8" stroke="var(--rail)" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}
