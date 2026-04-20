import type { NextConfig } from "next";

// Unified single-server model: FastAPI serves this bundle at `/` on the same
// origin as `/api/*` and `/mcp/*`. Setting NEXT_PUBLIC_API_BASE_URL to an
// empty string makes every fetch() use relative paths → same-origin.
const nextConfig: NextConfig = {
  output: "export",
  devIndicators: false,
  images: { unoptimized: true },
  env: {
    NEXT_PUBLIC_API_BASE_URL: "",
  },
};

export default nextConfig;
