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
}

export default function ClientsPage() {
  const { getToken } = useAuth()
  const [clients, setClients] = useState<Client[]>([])
  const [name, setName] = useState("")
  const [companyName, setCompanyName] = useState("")
  const [notes, setNotes] = useState("")
  const [error, setError] = useState("")

  const load = async () => {
    try {
      const token = await getToken()
      setClients(await apiGet<Client[]>("/api/clients", token ?? undefined))
    } catch (e) {
      setError(String(e))
    }
  }

  useEffect(() => {
    load()
  }, [])

  const createClient = async () => {
    try {
      setError("")
      const token = await getToken()
      await apiSend(
        "/api/clients",
        "POST",
        { name, company_name: companyName || null, notes: notes || null },
        token ?? undefined,
      )
      setName("")
      setCompanyName("")
      setNotes("")
      await load()
    } catch (e) {
      setError(String(e))
    }
  }

  return (
    <main className="stack">
      <div className="section-title">
        <h1>Clienti</h1>
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
          <button onClick={createClient}>Creeaza client</button>
        </div>
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
          </Link>
        ))}
      </div>
    </main>
  )
}
