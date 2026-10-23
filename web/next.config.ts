import type { NextConfig } from "next";

// Allow Cloudflare tunnel host for dev HMR (harmless in prod where output=standalone serves directly)
const ALLOWED_DEV_ORIGINS = (process.env.ALLOWED_DEV_ORIGINS ?? "").split(",").filter(Boolean);

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  output: "standalone",
  poweredByHeader: false,
  allowedDevOrigins: ALLOWED_DEV_ORIGINS.length ? ALLOWED_DEV_ORIGINS : undefined,
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
