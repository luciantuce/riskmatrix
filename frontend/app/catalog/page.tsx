"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { useAuth } from "@clerk/nextjs"

import { apiGet } from "@/lib/api"

type Kit = {
  code: string
  name: string
  description: string | null
  price_eur: number
  documentation_url: string | null
}

export default function CatalogPage() {
  const { getToken } = useAuth()
  const [kits, setKits] = useState<Kit[]>([])
  const [error, setError] = useState("")

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const token = await getToken()
        const rows = await apiGet<Kit[]>("/api/kits", token ?? undefined)
        if (!cancelled) setKits(rows)
      } catch (e) {
        if (!cancelled) setError(String(e))
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [getToken])

  return (
    <main className="stack">
      <div className="card stack">
        <h1>Catalog Kituri</h1>
        <p className="muted">Alege kiturile de risc potrivite pentru clientii tai.</p>
      </div>

      <div className="grid grid-2">
        {kits.map((kit) => (
          <div key={kit.code} className="card stack">
            <div className="section-title" style={{ marginBottom: 0 }}>
              <strong>{kit.name}</strong>
              <span className="pill">{kit.price_eur.toFixed(0)} EUR</span>
            </div>
            <span className="muted">{kit.description || "Fara descriere."}</span>
            <div className="row">
              {kit.documentation_url && (
                <a href={kit.documentation_url} className="button secondary" target="_blank" rel="noreferrer">
                  Vezi documentatia
                </a>
              )}
              <button disabled title="Urmeaza integrarea Stripe">
                Cumpara (curand)
              </button>
            </div>
          </div>
        ))}
      </div>

      {error && <p className="muted">{error}</p>}

      <div className="card stack">
        <p className="muted">
          Dupa integrarea subscriptions, in pagina de clienti vor fi vizibile doar kiturile cumparate.
        </p>
        <Link href="/clients" className="button">
          Inapoi la clienti
        </Link>
      </div>
    </main>
  )
}
