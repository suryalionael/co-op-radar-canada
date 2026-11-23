import { MONTH_NAMES } from "@/lib/format";
import type { Company } from "@/lib/types";

/** Open now / opens soon / quiet, printed like a timetable's service notice. */
export function StatusPlate({ company: c }: { company: Company }) {
  if (c.badge === "open")
    return (
      <span className="plate-type inline-block whitespace-nowrap bg-signal px-2 py-0.5 text-[0.75rem] text-signal-fg">
        Open · <span className="figures">{c.open_count}</span>
      </span>
    );
  if (c.badge === "soon" && c.window)
    return (
      <span className="plate-type inline-block whitespace-nowrap border-[1.5px] border-fg px-2 py-0.5 text-[0.75rem]">
        Opens ~{MONTH_NAMES[c.window.start - 1]}
      </span>
    );
  return <span className="plate-type inline-block whitespace-nowrap px-2 py-0.5 text-[0.75rem] text-muted">Quiet</span>;
}
