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
        <ul className="mt-2 grid border-l border-t border-border sm:grid-cols-2 xl:grid-cols-3">
          {shown.map((c) => (
            <li key={c.slug} className="border-b border-r border-border bg-surface p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <Link
                    href={`/companies/${c.slug}/`}
                    className="font-display text-[1.0625rem] font-extrabold leading-tight hover:text-link hover:underline"
                  >
                    {c.name}
                  </Link>
                  {c.sector && <p className="text-xs text-muted">{formatSector(c.sector)}</p>}
                </div>
                <StatusPlate company={c} />
              </div>
              {c.window ? (
                <div className="mt-3">
                  <WindowStrip window={c.window} currentMonth={currentMonth} />
                </div>
              ) : (
                <p className="mt-3 text-xs text-muted">
                  {c.open_count ? "Calendar once there’s more history" : "No student postings seen yet"}
                </p>
              )}
            </li>
          ))}
        </ul>
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
