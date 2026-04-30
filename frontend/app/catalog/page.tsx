"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { useAuth } from "@clerk/nextjs"

import { apiGet } from "@/lib/api"

type Product = {
  id: number
  code: string
  name: string
  type: string
  kit_id: number | null
}

export default function CatalogPage() {
  const { getToken } = useAuth()
  const [products, setProducts] = useState<Product[]>([])
  const [error, setError] = useState("")

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const token = await getToken()
        const rows = await apiGet<Product[]>("/api/products", token ?? undefined)
        if (!cancelled) setProducts(rows)
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
        {products.map((product) => (
          <div key={product.code} className="card stack">
            <div className="section-title" style={{ marginBottom: 0 }}>
              <strong>{product.name}</strong>
              <span className="pill">{product.type}</span>
            </div>
            <span className="muted">Cod produs: {product.code}</span>
            <div className="row">
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
