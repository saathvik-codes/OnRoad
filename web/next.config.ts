import type { NextConfig } from "next";

// The browser talks only to this origin; /api is proxied to the FastAPI service (same-site cookie, no CORS).
// Render passes the backend as "host:port" (no scheme); local dev uses the full URL.
const RAW_API = process.env.API_ORIGIN ?? "http://127.0.0.1:8101";
const API_ORIGIN = /^https?:\/\//.test(RAW_API) ? RAW_API : `http://${RAW_API}`;

// Allow Cloudflare tunnel host for dev HMR (harmless in prod where output=standalone serves directly)
const ALLOWED_DEV_ORIGINS = (process.env.ALLOWED_DEV_ORIGINS ?? "").split(",").filter(Boolean);

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  output: "standalone",
  poweredByHeader: false,
  allowedDevOrigins: ALLOWED_DEV_ORIGINS.length ? ALLOWED_DEV_ORIGINS : undefined,
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_ORIGIN}/api/:path*` }];
  },
  images: {
    // official manufacturer image hosts are added as brands are wired in; unknown hosts fall back to <img>
    remotePatterns: [{ protocol: "https", hostname: "**" }],
  },
  turbopack: {
    rules: {
      "*.css": { loaders: ["@tailwindcss/turbopack"], as: "*.css" },
    },
  },
};

export default nextConfig;
