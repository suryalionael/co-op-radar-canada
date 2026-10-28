import { PostingsExplorer } from "@/components/PostingsExplorer";
import { getMeta, getPostings } from "@/lib/data";

export default function Home() {
  const postings = getPostings();
  const meta = getMeta();
  const c = meta.counts;

  return (
    <>
      <div className="max-w-3xl">
        <h1 className="text-3xl font-semibold">Co-op and internship postings, checked against the posting itself</h1>
        <p className="mt-3 text-lg text-muted">
          Every term and duration below links back to the words it came from. If a posting doesn&rsquo;t say how long
          it lasts, we say so instead of guessing.
        </p>
      </div>

      {postings.length === 0 ? (
        <section className="mt-10 max-w-2xl rounded-md bg-surface p-6">
          <h2 className="text-xl font-semibold">No postings yet</h2>
          <p className="mt-2">
            The daily pipeline hasn&rsquo;t published its first set of postings. Once it runs, open co-op and
            internship postings from {c.employer_boards_tracked} employer job boards will appear here.
          </p>
          <p className="mt-2 text-muted">
            Large banks, insurers and governments don&rsquo;t publish postings through a public API, so they are
            covered by <a className="text-accent underline" href="/programs/">Program watch</a> instead.
          </p>
        </section>
      ) : (
        <>
          <p className="mt-4 font-mono text-sm text-muted tabular">
            {c.open_student_postings} open · {c.duration_stated} with a stated duration · {c.duration_from_dates}{" "}
            with dates only · {c.employers_with_postings} employers
          </p>
          <div className="mt-8">
            <PostingsExplorer postings={postings} dataDate={meta.data_as_of.postings} />
          </div>
        </>
      )}
    </>
  );
}
