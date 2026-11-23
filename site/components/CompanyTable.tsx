"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { StatusPlate } from "./StatusPlate";
import { WindowStrip } from "./WindowStrip";
import { formatSector } from "@/lib/format";
import type { Company, CompanyBadge } from "@/lib/types";

const VIEWS: { value: "" | CompanyBadge; label: string }[] = [
  { value: "", label: "All" },
  { value: "open", label: "Open now" },
  { value: "soon", label: "Opening soon" },
  { value: "quiet", label: "Quiet" },
];

const COMPANY_COLUMNS = "md:grid-cols-[minmax(0,1.2fr)_9rem_7rem_minmax(0,1fr)]";

export function CompanyTable({ companies, currentMonth }: { companies: Company[]; currentMonth: number }) {
  const [q, setQ] = useState("");
  const [view, setView] = useState<"" | CompanyBadge>("");
  const counts = useMemo(
    () => Object.fromEntries(VIEWS.map((v) => [v.value, companies.filter((c) => !v.value || c.badge === v.value).length])),
    [companies],
  );
  const needle = q.trim().toLowerCase();
  const shown = companies.filter(
    (c) => (!view || c.badge === view) && (!needle || c.name.toLowerCase().includes(needle)),
  );

  return (
    <>
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <label className="flex min-h-12 items-center gap-3 border-2 border-fg bg-surface px-4 md:w-96">
          <span className="sr-only">Search companies</span>
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search companies"
            className="h-11 w-full bg-transparent outline-none placeholder:text-muted"
          />
        </label>
        <div role="group" aria-label="Show" className="flex flex-wrap gap-2">
          {VIEWS.filter((v) => counts[v.value] > 0).map((v) => (
            <button
              key={v.label}
              type="button"
              aria-pressed={view === v.value}
              onClick={() => setView(v.value)}
              className={`inline-flex min-h-10 items-center gap-2 border-[1.5px] px-3 font-display text-sm font-bold transition-colors ${
                view === v.value ? "border-go bg-go text-go-fg" : "border-border bg-surface hover:border-fg"
              }`}
            >
              {v.label} <span className="figures font-semibold opacity-80">{counts[v.value]}</span>
            </button>
          ))}
        </div>
      </div>

      <p className="mt-6 text-sm text-muted" aria-live="polite">
        <span className="figures font-bold text-fg">{shown.length}</span> {shown.length === 1 ? "company" : "companies"}
      </p>
      {shown.length ? (
        <div className="mt-2">
          <div
            aria-hidden="true"
            className={`plate-type hidden bg-ink-bar px-5 py-2.5 text-xs text-ink-bar-fg md:grid md:gap-x-6 ${COMPANY_COLUMNS}`}
          >
            <span>Company</span>
            <span>Sector</span>
            <span>Status</span>
            <span>Hiring months</span>
          </div>
          <ul className="border-x border-t border-border md:border-t-0">
            {shown.map((c) => (
              <li
                key={c.slug}
                className={`grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-2 border-b border-border bg-surface px-4 py-3 md:gap-x-6 md:px-5 ${COMPANY_COLUMNS}`}
              >
                <Link
                  href={`/companies/${c.slug}/`}
                  className="min-w-0 break-words py-1 font-display text-base font-extrabold leading-tight hover:text-link hover:underline"
                >
                  {c.name}
                </Link>
                <span className="hidden text-sm text-muted md:block">{c.sector ? formatSector(c.sector) : "—"}</span>
                <span className="justify-self-end md:justify-self-start">
                  <StatusPlate company={c} />
                </span>
                <div className="col-span-2 md:col-span-1">
                  {c.window ? (
                    <WindowStrip window={c.window} currentMonth={currentMonth} />
                  ) : (
                    <span className="text-sm italic text-muted">{c.open_count ? "too new to tell" : "no postings seen yet"}</span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <div className="mt-2 border-2 border-dashed border-border px-6 py-10">
          <p className="font-display text-lg font-extrabold">No companies match.</p>
          <button
            type="button"
            onClick={() => {
              setQ("");
              setView("");
            }}
            className="mt-2 min-h-11 font-bold text-link underline"
          >
            Show all companies
          </button>
        </div>
      )}
    </>
  );
}
