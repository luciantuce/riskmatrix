"use client"

import Link from "next/link"
import { SignedIn, SignedOut, UserButton, useAuth } from "@clerk/nextjs"
import { useEffect, useState } from "react"
import { usePathname } from "next/navigation"

import { apiGet } from "@/lib/api"
import { isAdminRole } from "@/lib/roles"

type MeResponse = {
  role: string
}

export default function TopNav() {
  const { getToken } = useAuth()
  const pathname = usePathname()
  const [canSeeAdmin, setCanSeeAdmin] = useState(false)

  useEffect(() => {
    let cancelled = false

    const loadRole = async () => {
      try {
        const token = await getToken()
        if (!token) {
          if (!cancelled) setCanSeeAdmin(false)
          return
        }
        const me = await apiGet<MeResponse>("/api/me", token)
        if (!cancelled) {
          setCanSeeAdmin(isAdminRole(me.role))
        }
      } catch {
        if (!cancelled) {
          setCanSeeAdmin(false)
        }
      }
    }

    const onVisibilityOrFocus = () => {
      if (document.visibilityState === "visible") {
        loadRole()
      }
    }

    loadRole()
    window.addEventListener("focus", onVisibilityOrFocus)
    document.addEventListener("visibilitychange", onVisibilityOrFocus)

    return () => {
      cancelled = true
      window.removeEventListener("focus", onVisibilityOrFocus)
      document.removeEventListener("visibilitychange", onVisibilityOrFocus)
    }
  }, [getToken, pathname])

  return (
    <div className="nav">
      <SignedIn>
        <Link href="/">Dashboard</Link>
        <Link href="/clients">Clienti</Link>
        <Link href="/catalog">Catalog</Link>
        {canSeeAdmin && <Link href="/admin">Super Contabil</Link>}
        <UserButton afterSignOutUrl="/sign-in" />
      </SignedIn>
      <SignedOut>
        <Link href="/sign-in">Autentificare</Link>
      </SignedOut>
    </div>
  )
}
