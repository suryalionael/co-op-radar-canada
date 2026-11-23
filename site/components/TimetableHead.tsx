/** Desktop column rhythm shared by the head bar and every JobRow. Lives outside the client module so server pages can read it. */
export const ROW_COLUMNS = "md:grid-cols-[4.5rem_minmax(0,1fr)_8rem_5.5rem_4rem_4.75rem]";

/** The black head bar over a timetable of roles. Visual only: each row labels its own cells for screen readers. */
export function TimetableHead() {
  return (
    <div aria-hidden="true" className={`plate-type hidden bg-ink-bar px-5 py-2.5 text-xs text-ink-bar-fg md:grid md:gap-x-4 ${ROW_COLUMNS}`}>
      <span>Posted</span>
      <span>Role</span>
      <span>Term</span>
      <span>Length</span>
      <span>Prov</span>
      <span />
    </div>
  );
}
