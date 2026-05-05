"use client"

import * as Sentry from "@sentry/nextjs"
import { useEffect } from "react"

export function SentryInit() {
  useEffect(() => {
    const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN
    if (!dsn) return

    Sentry.init({
      dsn,
      environment: process.env.NODE_ENV,
      tracesSampleRate: 0.1,
      sendDefaultPii: true,
      beforeSend(event, hint) {
        const err = hint?.originalException
        if (err && typeof err === "object" && "status" in err) {
          const status = (err as { status?: number }).status
          if (typeof status === "number" && status < 500) return null
        }
        return event
      },
    })
  }, [])

  return null
}
