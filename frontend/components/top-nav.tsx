"use client"

import Link from "next/link"
import { SignedIn, SignedOut, UserButton, useAuth } from "@clerk/nextjs"
import { useEffect, useState } from "react"

import { apiGet } from "@/lib/api"
import { isAdminRole } from "@/lib/roles"

type MeResponse = {
  role: string
}

export default function TopNav() {
  const { getToken } = useAuth()
  const [canSeeAdmin, setCanSeeAdmin] = useState(false)

  useEffect(() => {
    let cancelled = false

    const loadRole = async () => {
      try {
        const token = await getToken()
        if (!token) return
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

    loadRole()
    return () => {
      cancelled = true
    }
  }, [getToken])

  return (
    <div className="nav">
      <SignedIn>
        <Link href="/">Dashboard</Link>
        <Link href="/clients">Clienti</Link>
        {canSeeAdmin && <Link href="/admin">Super Contabil</Link>}
        <UserButton afterSignOutUrl="/sign-in" />
      </SignedIn>
      <SignedOut>
        <Link href="/sign-in">Autentificare</Link>
      </SignedOut>
    </div>
  )
}
