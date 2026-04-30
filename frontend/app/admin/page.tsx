"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { useAuth } from "@clerk/nextjs"

import { apiGet } from "@/lib/api"
import { isAdminRole } from "@/lib/roles"

type Kit = {
  code: string
  name: string
  description: string | null
  price_eur: number
}

export default function AdminPage() {
  const router = useRouter()
  const { getToken } = useAuth()
  const [kits, setKits] = useState<Kit[]>([])
  const [authorized, setAuthorized] = useState(false)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const token = await getToken()
        if (!token) {
          router.replace("/")
          return
        }
        const me = await apiGet<{ role: string }>("/api/me", token)
        if (!isAdminRole(me.role)) {
          router.replace("/")
          return
        }
        const kitsData = await apiGet<Kit[]>("/api/kits", token)
        if (!cancelled) {
          setAuthorized(true)
          setKits(kitsData)
        }
      } catch {
        if (!cancelled) {
          setKits([])
          setAuthorized(false)
        }
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [getToken, router])

  if (!authorized) return null

  return (
    <main className="stack">
      <div className="card">
        <h1>Super Contabil</h1>
        <p className="muted">Editezi kituri, intrebari, reguli si template-uri PDF dintr-un singur loc.</p>
        <div className="row" style={{ marginTop: 12 }}>
          <Link className="button secondary" href="/admin/users">
            Management utilizatori
          </Link>
        </div>
      </div>

      <div className="grid grid-2">
        {kits.map((kit) => (
          <Link key={kit.code} href={`/admin/kits/${kit.code}`} className="card stack">
            <strong>{kit.name}</strong>
            <span className="muted">{kit.description}</span>
            <span className="pill">{kit.price_eur.toFixed(0)} EUR</span>
          </Link>
        ))}
      </div>
    </main>
  )
}
