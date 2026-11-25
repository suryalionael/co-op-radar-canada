import { formatMonthRuns, MONTH_NAMES } from "@/lib/format";
import type { HiringWindow } from "@/lib/types";

/**
 * The service calendar: twelve months in a framed strip. Shaded months are when this company's
 * student postings appeared; the current month is ringed. One form, drawn at two sizes.
 */
export function WindowStrip({
  window: w,
  currentMonth,
  size = "sm",
}: {
  window: HiringWindow | null;
  currentMonth: number; // 1–12
  size?: "sm" | "lg";
}) {
  const max = w ? Math.max(...w.months) : 0;
  const inWindow = (m: number) => (w ? (w.start <= w.end ? m >= w.start && m <= w.end : m >= w.start || m <= w.end) : false);
  const researched = w?.source === "researched";
  const label = !w
    ? "Not enough history yet"
    : researched
      ? `Researched: ${formatMonthRuns(w.months)}`
      : `Usually hires ${MONTH_NAMES[w.start - 1]}${w.end !== w.start ? `–${MONTH_NAMES[w.end - 1]}` : ""}`;
  return (
    <figure className="m-0">
      <ol
        className={`grid grid-cols-12 border-[1.5px] border-fg ${size === "lg" ? "h-14" : "h-6"}`}
        aria-label={label}
      >
        {MONTH_NAMES.map((name, i) => {
          const m = i + 1;
          const n = w?.months[i] ?? 0;
          const strong = n > 0 && (researched || n >= max / 2 || inWindow(m));
          const tone = n === 0 ? "" : strong ? "bg-go text-go-fg" : "bg-go-soft text-fg";
          return (
            <li
              key={name}
              className={`figures relative grid place-items-center border-r border-border text-[0.625rem] font-bold uppercase last:border-r-0 ${tone} ${
                m === currentMonth ? "outline-[2.5px] -outline-offset-[2.5px] outline-signal" : ""
              } ${size === "lg" ? "text-xs" : ""}`}
            >
              <span aria-hidden="true">{size === "lg" ? name : name[0]}</span>
              {size === "lg" && n > 0 && !researched && <span className="text-[0.6875rem] font-semibold">{n}</span>}
              <span className="sr-only">
                {researched ? `${name}: ${n ? "hires" : "no"}` : `${name}: ${n} ${n === 1 ? "posting" : "postings"}`}
              </span>
            </li>
          );
        })}
      </ol>
      <figcaption className={`mt-1 text-xs text-muted ${size === "lg" ? "text-sm" : ""}`}>{label}</figcaption>
    </figure>
  );
}
