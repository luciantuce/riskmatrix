const { withSentryConfig } = require("@sentry/nextjs")

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Trust the reverse proxy in front of us (Railway edge) — needed so
  // Next.js sees the real client IP and original scheme for links/logs.
  // Newer Next.js versions pick this up from X-Forwarded-* automatically.
  poweredByHeader: false,

  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
    ]
  },
}

module.exports = withSentryConfig(nextConfig, {
  silent: true,
  // Disable source map upload (no SENTRY_AUTH_TOKEN configured)
  disableSourceMapUpload: true,
  // Suppress Sentry build-time telemetry
  telemetry: false,
})
