// This file is used by Next.js to register server-side instrumentation.
// @sentry/nextjs picks up sentry.server.config.ts automatically via withSentryConfig.
// This file intentionally left minimal — Sentry init is in sentry.server.config.ts.
export async function register() {
  // Sentry server SDK is initialized via sentry.server.config.ts (auto-injected by withSentryConfig)
}
