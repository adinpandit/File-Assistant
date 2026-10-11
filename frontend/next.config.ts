import type { NextConfig } from "next";

// The FastAPI backend has no CORS middleware, so the browser cannot call it
// directly from another origin. Requests to /api/* are proxied to the backend
// by the Next.js server instead, keeping them same-origin for the browser.
const apiBaseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/+$/, "");

const nextConfig: NextConfig = {
  output: "standalone",
  experimental: {
    // POST /api/upload parses and embeds the whole file before responding,
    // and the backend sends nothing until it finishes. On CPU a 444-page PDF
    // took ~290s, so the previous 300s limit cut such uploads off with a bare
    // 500 while the backend went on to store the document. Allow 15 minutes.
    proxyTimeout: 900_000,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiBaseUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
