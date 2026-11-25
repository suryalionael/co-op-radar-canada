import Link from "next/link";

export default function NotFound() {
  return (
    <div className="max-w-xl py-8">
      <h1 className="text-[clamp(1.75rem,1.2rem+2vw,2.5rem)] font-black tracking-[-0.02em]">
        That page is closed or doesn&rsquo;t exist.
      </h1>
      <p className="mt-3 text-lg text-muted">
        Postings come down when the employer closes them. Browse what&rsquo;s open now, or see who is hiring.
      </p>
      <p className="mt-6 flex flex-wrap gap-x-6">
        <Link href="/" className="inline-flex min-h-11 items-center font-display font-extrabold text-link underline decoration-2 underline-offset-4">
          All jobs
        </Link>
        <Link href="/companies/" className="inline-flex min-h-11 items-center font-display font-extrabold text-link underline decoration-2 underline-offset-4">
          Companies
        </Link>
      </p>
    </div>
  );
}
