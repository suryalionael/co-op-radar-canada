// Build-time data loading. Runs only on the server during `next build`.
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import type { Company, Meta, Posting, ProgramsData } from "./types";

// SITE_DATA_DIR=sample-data switches to the fictional development data.
const dataDir = path.join(process.cwd(), process.env.SITE_DATA_DIR ?? "public/data");

export const isSampleData = process.env.SITE_DATA_DIR === "sample-data";

function read<T>(name: string): T {
  return JSON.parse(readFileSync(path.join(dataDir, `${name}.json`), "utf-8")) as T;
}

export const getPostings = (): Posting[] => read<Posting[]>("postings");
export const getPrograms = (): ProgramsData => read<ProgramsData>("programs");
export const getMeta = (): Meta => read<Meta>("meta");
export const getCompanies = (): Company[] => read<Company[]>("companies");
export const getCompany = (slug: string): Company | undefined => getCompanies().find((c) => c.slug === slug);

const descriptionsDir = path.join(process.cwd(), isSampleData ? "sample-data/descriptions" : "content/descriptions");

/** The cleaned employer description for a posting, or null when none was stored. Sanitised by the pipeline. */
export function getDescription(id: string): string | null {
  if (!/^[A-Za-z0-9_-]+$/.test(id)) return null;
  const file = path.join(descriptionsDir, `${id}.html`);
  return existsSync(file) ? readFileSync(file, "utf-8") : null;
}

export const getPosting = (id: string): Posting | undefined => getPostings().find((p) => p.id === id);
