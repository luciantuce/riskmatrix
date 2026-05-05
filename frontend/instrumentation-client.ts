import * as Sentry from "@sentry/nextjs"

if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
    environment: process.env.NODE_ENV,
    tracesSampleRate: 0.1,
    sendDefaultPii: true,
    // Only send unhandled errors — drop 4xx client errors
    beforeSend(event, hint) {
      const err = hint?.originalException
      if (err && typeof err === "object" && "status" in err) {
        const status = (err as { status?: number }).status
        if (typeof status === "number" && status < 500) return null
      }
      return event
    },
  })
}

export const onRouterTransitionStart = Sentry.captureRouterTransitionStart
