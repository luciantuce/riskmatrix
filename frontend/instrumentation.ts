import * as Sentry from "@sentry/nextjs"

export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN
    if (!dsn) {
      console.warn("[sentry] NEXT_PUBLIC_SENTRY_DSN not set — Sentry disabled on server")
      return
    }
    Sentry.init({
      dsn,
      environment: process.env.NODE_ENV,
      tracesSampleRate: 0.1,
      sendDefaultPii: true,
      // Only send unhandled errors and 5xx — drop 4xx client errors
      beforeSend(event, hint) {
        const err = hint?.originalException
        if (err && typeof err === "object" && "status" in err) {
          const status = (err as { status?: number }).status
          if (typeof status === "number" && status < 500) return null
        }
        return event
      },
    })
    console.info("[sentry] initialized", { environment: process.env.NODE_ENV })
  }
}
