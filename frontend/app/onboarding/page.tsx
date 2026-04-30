"use client"

import { useUser } from "@clerk/nextjs"
import { useRouter } from "next/navigation"
import { useEffect } from "react"

export default function OnboardingPage() {
  const { user, isLoaded } = useUser()
  const router = useRouter()

  useEffect(() => {
    if (isLoaded) {
      router.replace("/clients")
    }
  }, [isLoaded, router])

  return (
    <main className="stack">
      <div className="card">
        <h1>Bun venit{user?.firstName ? `, ${user.firstName}` : ""}!</h1>
        <p className="muted">Se pregateste contul tau...</p>
      </div>
    </main>
  )
}
