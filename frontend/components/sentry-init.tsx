"use client"

import * as Sentry from "@sentry/nextjs"
import { useEffect } from "react"

declare global {
  interface Window {
    Sentry?: typeof Sentry
  }
}

export function SentryInit() {
  useEffect(() => {
    const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN
    if (!dsn) {
      console.warn("[sentry] NEXT_PUBLIC_SENTRY_DSN missing — SDK disabled")
      return
    }

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

    // Expose globally for manual testing from browser console
    if (typeof window !== "undefined") {
      window.Sentry = Sentry
    }

    console.info("[sentry] client SDK initialized — call window.Sentry.captureException(new Error('test')) to verify")
  }, [])

  return null
}
