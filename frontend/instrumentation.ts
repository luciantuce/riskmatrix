import * as Sentry from "@sentry/nextjs"

export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    Sentry.init({
      dsn: process.env.SENTRY_DSN_BACKEND || process.env.NEXT_PUBLIC_SENTRY_DSN,
      environment: process.env.NODE_ENV,
      tracesSampleRate: 0.1,
      sendDefaultPii: true,
      beforeSend(event) {
        const responseContext = (event.contexts?.response as { status_code?: number } | undefined)
        const nextContext = (event.contexts?.nextjs as { statusCode?: number } | undefined)
        const statusCode = responseContext?.status_code ?? nextContext?.statusCode

        if (typeof statusCode === "number" && statusCode < 500) {
          return null
        }
        return event
      },
    })
  }
}
