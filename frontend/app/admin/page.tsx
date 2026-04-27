"use client"

import Link from "next/link"
import { useEffect, useState } from "react"

import { apiGet } from "@/lib/api"

type Kit = {
  code: string
  name: string
  description: string | null
  price_eur: number
}

export default function AdminPage() {
  const [kits, setKits] = useState<Kit[]>([])

  useEffect(() => {
    apiGet<Kit[]>("/api/kits").then(setKits).catch(() => setKits([]))
  }, [])

  return (
    <main className="stack">
      <div className="card">
        <h1>Super Contabil</h1>
        <p className="muted">Editezi kituri, intrebari, reguli si template-uri PDF dintr-un singur loc.</p>
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
