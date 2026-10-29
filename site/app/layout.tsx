import { Analytics } from "@vercel/analytics/next";
import type { Metadata, Viewport } from "next";
import Link from "next/link";
import { Nav } from "@/components/Nav";
import { getMeta, isSampleData } from "@/lib/data";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Co-op Radar Canada", template: "%s · Co-op Radar Canada" },
  description:
    "Canadian co-op and internship postings with the term, duration and province checked against the posting text, plus alerts when student programs open.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#fbfcfd" },
    { media: "(prefers-color-scheme: dark)", color: "#16181c" },
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
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:bg-bg focus:p-2"
        >
          Skip to content
        </a>
        {isSampleData && (
          <p className="bg-warning px-4 py-2 text-center text-sm font-medium text-bg">
            Sample data for local development. These postings are fictional.
          </p>
        )}
        <header className="mx-auto max-w-6xl px-4 pt-6 md:px-8">
          <div className="flex flex-wrap items-end justify-between gap-x-8 gap-y-2 border-b border-border pb-3">
            <Link href="/" className="group">
              <span className="font-display text-2xl font-semibold tracking-tight group-hover:text-accent transition-colors">
                Co-op Radar
              </span>{" "}
              <span className="facts text-base text-muted">Canada</span>
            </Link>
            <Nav />
          </div>
          <p className="mt-2 font-mono text-sm text-muted tabular">
            {asOf ? `Postings checked ${asOf}` : "No postings collected yet"} ·{" "}
            {meta.counts.employer_boards_tracked} employer boards · {meta.counts.programs_watched} program pages
          </p>
        </header>
        <main id="main" className="mx-auto max-w-6xl px-4 pb-16 pt-8 md:px-8">
          {children}
        </main>
        <footer className="mx-auto max-w-6xl px-4 text-sm text-muted md:px-8">
          <p className="border-t border-border py-6">
            An independent student project, not affiliated with any employer, school or government listed. Always
            confirm details on the original posting.{" "}
            <a className="underline hover:text-accent" href="https://github.com/suryalionael/co-op-radar-canada">
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
