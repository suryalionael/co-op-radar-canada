/** The posting's own words, with the matched phrase highlighted. */
export function EvidenceQuote({ context, span, label }: { context: string; span?: string; label?: string }) {
  const at = span ? context.indexOf(span) : -1;
  return (
    <p className="mt-1.5 flex max-w-[58ch] gap-3 text-sm">
      {label && <span className="plate-type w-14 shrink-0 pt-0.5 text-[0.6875rem] text-muted">{label}</span>}
      <q className="min-w-0 [quotes:'“''”']">
        {at < 0 ? (
          context
        ) : (
          <>
            {context.slice(0, at)}
            <mark>{span}</mark>
            {context.slice(at + (span?.length ?? 0))}
          </>
        )}
      </q>
    </p>
  );
}
