import type { Metadata } from "next";
import { CompanyTable } from "@/components/CompanyTable";
import { getCompanies, getMeta } from "@/lib/data";

export const metadata: Metadata = {
  title: "Companies",
  description: "Every Canadian tech employer we track, who is hiring students now, and the months each one usually posts.",
};

export default function CompaniesPage() {
  const companies = getCompanies();
  const asOf = getMeta().data_as_of.postings;
  const month = asOf ? Number(asOf.slice(5, 7)) : new Date().getMonth() + 1;
  const open = companies.filter((c) => c.badge === "open").length;
  return (
    <>
      <div className="grid items-end gap-x-12 gap-y-4 pb-8 md:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
        <h1 className="text-display font-black tracking-[-0.02em]">
          Who&rsquo;s hiring, <span className="bg-signal px-2 text-signal-fg [box-decoration-break:clone]">and when.</span>
        </h1>
        <p className="max-w-[46ch] text-lg text-muted">
          {open} of {companies.length} companies have student roles open right now. The strip under each one shows the
          months its postings appeared, so you know when to look again.
        </p>
      </div>
      <CompanyTable companies={companies} currentMonth={month} />
      <p className="mt-6 max-w-[70ch] text-sm text-muted">
        We started reading job boards in October 2026, so most companies don&rsquo;t have enough history for a calendar
        yet. A company needs at least three postings before we draw one. The first day we read a board doesn&rsquo;t
        count, because everything already up looks new that day.
      </p>
    </>
  );
}
