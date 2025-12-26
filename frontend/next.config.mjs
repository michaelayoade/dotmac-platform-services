import { fileURLToPath } from "url";

const designTokensPath = fileURLToPath(
  new URL("../packages/design-tokens/src", import.meta.url)
);

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker builds
  output: 'standalone',

  // Enable React strict mode for better development experience
  reactStrictMode: true,

  // Transpile component library packages
  transpilePackages: [
    "@dotmac/core",
    "@dotmac/forms",
    "@dotmac/data-table",
    "@dotmac/charts",
    "@dotmac/dashboards",
    "@dotmac/design-tokens",
  ],

  // Image optimization configuration
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "*.gravatar.com",
      },
      {
        protocol: "https",
        hostname: "avatars.githubusercontent.com",
      },
    ],
  },

  // Environment variables available on the client
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },

  // Redirect configuration
  async redirects() {
    return [
      {
        source: "/dashboard",
        destination: "/",
        permanent: true,
      },
    ];
  },

  // Headers for security
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
        ],
      },
    ];
  },

  // Module aliases for local packages when workspace links are unavailable
  webpack: (config) => {
    config.resolve = config.resolve || {};
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      "@dotmac/design-tokens": designTokensPath,
    };
    // Ensure TypeScript extensions are resolved before .js
    config.resolve.extensions = [
      ".tsx",
      ".ts",
      ".jsx",
      ".js",
      ".mjs",
      ".json",
    ];
    config.resolve.extensionAlias = {
      ...(config.resolve.extensionAlias || {}),
      ".js": [".tsx", ".ts", ".js"],
      ".mjs": [".mts", ".mjs"],
    };
    return config;
  },

  // Experimental features
  experimental: {
    // Enable server actions
    serverActions: {
      bodySizeLimit: "2mb",
    },
  },
};

export default nextConfig;
