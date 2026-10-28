// Build-time data loading. Runs only on the server during `next build`.
import { readFileSync } from "node:fs";
import path from "node:path";
import type { Meta, Posting, ProgramsData } from "./types";

// SITE_DATA_DIR=sample-data switches to the fictional development data.
const dataDir = path.join(process.cwd(), process.env.SITE_DATA_DIR ?? "public/data");

export const isSampleData = process.env.SITE_DATA_DIR === "sample-data";

function read<T>(name: string): T {
  return JSON.parse(readFileSync(path.join(dataDir, `${name}.json`), "utf-8")) as T;
}

export const getPostings = (): Posting[] => read<Posting[]>("postings");
export const getPrograms = (): ProgramsData => read<ProgramsData>("programs");
export const getMeta = (): Meta => read<Meta>("meta");
