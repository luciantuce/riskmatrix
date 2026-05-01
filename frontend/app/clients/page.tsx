"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { useAuth } from "@clerk/nextjs"

import { apiGet, apiSend } from "@/lib/api"

type Client = {
  id: number
  name: string
  company_name: string | null
  notes: string | null
  summary: {
    completed_kits: number
    in_progress_kits: number
    not_started_kits: number
    highest_risk_level: string | null
    latest_risk_score: number | null
    latest_updated_at: string | null
  }
}

export default function ClientsPage() {
  const { getToken, isLoaded } = useAuth()
  const [clients, setClients] = useState<Client[]>([])
  const [name, setName] = useState("")
  const [companyName, setCompanyName] = useState("")
  const [notes, setNotes] = useState("")
  const [error, setError] = useState("")
  const [isCreating, setIsCreating] = useState(false)
  const [notice, setNotice] = useState("")
  const riskBadgeClass = (level?: string | null) => {
    if (!level) return "pill"
    if (level === "LOW") return "status-badge status-low"
    if (level === "MEDIUM") return "status-badge status-medium"
    if (level === "HIGH") return "status-badge status-high"
    return "status-badge status-critical"
  }

  const load = async () => {
    try {
      if (!isLoaded) return
      const token = await getToken()
      if (!token) {
        setError("Sesiunea nu este gata. Reincarca pagina sau reconecteaza-te.")
        return
      }
      setClients(await apiGet<Client[]>("/api/clients", token ?? undefined))
    } catch (e) {
      setError(String(e))
    }
  }

  useEffect(() => {
    if (!isLoaded) return
    load()
  }, [isLoaded])

  const createClient = async () => {
    try {
      setIsCreating(true)
      setNotice("")
      setError("")
      if (!isLoaded) {
        setError("Sesiunea nu este gata. Reincarca pagina sau reconecteaza-te.")
        return
      }
      const token = await getToken()
      if (!token) {
        setError("Nu am putut obtine token-ul de autentificare. Reincarca pagina.")
        return
      }
      await apiSend(
        "/api/clients",
        "POST",
        { name, company_name: companyName || null, notes: notes || null },
        token,
      )
      setName("")
      setCompanyName("")
      setNotes("")
      setNotice("Client creat.")
      await load()
    } catch (e) {
      setError(String(e))
      setNotice("Nu am putut crea clientul.")
    } finally {
      setIsCreating(false)
    }
  }

  return (
    <main className="stack">
      <div className="section-title">
        <h1>Clienti</h1>
        <Link className="button secondary" href="/catalog">
          Catalog kituri
        </Link>
      </div>

      <div className="card stack">
        <h2>Client nou</h2>
        <div className="grid grid-2">
          <div>
            <label>Nume</label>
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <label>Companie</label>
            <input value={companyName} onChange={(e) => setCompanyName(e.target.value)} />
          </div>
        </div>
        <div>
          <label>Note</label>
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} />
        </div>
        <div>
          <button onClick={createClient} disabled={isCreating}>
            {isCreating ? "Creez..." : "Creeaza client"}
          </button>
        </div>
        {notice && <p className="muted">{notice}</p>}
        {error && <p className="muted">{error}</p>}
      </div>

      <div className="grid grid-2">
        {clients.map((client) => (
          <Link key={client.id} href={`/clients/${client.id}`} className="card stack">
            <div className="section-title" style={{ marginBottom: 0 }}>
              <strong>{client.name}</strong>
              <span className="pill">client</span>
            </div>
            <span className="muted">{client.company_name || "Fara denumire companie"}</span>
            <div className="row" style={{ gap: 8 }}>
              <span className="pill">{client.summary.completed_kits} complete</span>
              <span className="pill">{client.summary.in_progress_kits} in lucru</span>
              <span className="pill">{client.summary.not_started_kits} neincepute</span>
              {client.summary.highest_risk_level && (
                <span className={riskBadgeClass(client.summary.highest_risk_level)}>
                  Risc max: {client.summary.highest_risk_level}
                </span>
              )}
            </div>
          </Link>
        ))}
      </div>

      {clients.length === 0 && (
        <div className="card stack">
          <strong>Inca nu ai clienti.</strong>
          <span className="muted">
            Poti incepe din Catalog Kituri pentru a vedea oferta de kituri disponibile, apoi adauga primul client.
          </span>
          <div>
            <Link className="button" href="/catalog">
              Vezi Catalog Kituri
            </Link>
          </div>
        </div>
      )}
    </main>
  )
}
