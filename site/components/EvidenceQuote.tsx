/** The posting's own words, with the matched phrase highlighted. The site's signature element. */
export function EvidenceQuote({ context, span }: { context: string; span?: string }) {
  const at = span ? context.indexOf(span) : -1;
  return (
    <p className="mt-1 flex gap-2 text-sm text-muted">
      <span aria-hidden="true" className="font-mono text-border select-none">
        └
      </span>
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
