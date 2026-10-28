import type { NextConfig } from "next";

// Static export: the whole site is HTML, JS and JSON in `out/`, hosted on Vercel (ADR 0005).
const nextConfig: NextConfig = {
  output: "export",
  images: { unoptimized: true },
  trailingSlash: true,
};

export default nextConfig;
