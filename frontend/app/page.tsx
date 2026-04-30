 "use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { useAuth } from "@clerk/nextjs"

import { apiGet } from "@/lib/api"
import { isAdminRole } from "@/lib/roles"

export default function HomePage() {
  const { getToken } = useAuth()
  const [canSeeAdmin, setCanSeeAdmin] = useState(false)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const token = await getToken()
        if (!token) return
        const me = await apiGet<{ role: string }>("/api/me", token)
        if (!cancelled) setCanSeeAdmin(isAdminRole(me.role))
      } catch {
        if (!cancelled) setCanSeeAdmin(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [getToken])

  return (
    <main className="stack">
      <div className="card">
        <h1>Kit Platform V2</h1>
        <p className="muted">
          Varianta noua, fara autentificare, cu profil general comun, 5 kituri separate, reguli in baza de date si zona
          de administrare pentru intrebarile si regulile contabilei.
        </p>
        <div className="row" style={{ marginTop: 16 }}>
          <Link className="button" href="/clients">
            Intra in clienti
          </Link>
          {canSeeAdmin && (
            <Link className="button secondary" href="/admin">
              Deschide Super Contabil
            </Link>
          )}
        </div>
      </div>
    </main>
  )
}
