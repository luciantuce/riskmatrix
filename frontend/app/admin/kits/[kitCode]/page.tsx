"use client"

import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { useAuth } from "@clerk/nextjs"

import { apiGet, apiSend } from "@/lib/api"
import { isAdminRole } from "@/lib/roles"

type AdminData = {
  kit: {
    name: string
    description: string | null
    price_eur: number
    sections: unknown[]
  }
  rules: unknown[]
  template: Record<string, unknown>
}

export default function AdminKitPage() {
  const params = useParams()
  const router = useRouter()
  const { getToken } = useAuth()
  const kitCode = params.kitCode as string

  const [data, setData] = useState<AdminData | null>(null)
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [price, setPrice] = useState("0")
  const [sectionsJson, setSectionsJson] = useState("[]")
  const [rulesJson, setRulesJson] = useState("[]")
  const [templateJson, setTemplateJson] = useState("{}")
  const [error, setError] = useState("")
  const [token, setToken] = useState<string | null>(null)
  const [authorized, setAuthorized] = useState(false)

  const load = async (jwt: string) => {
    try {
      const res = await apiGet<AdminData>(`/api/admin/kits/${kitCode}`, jwt)
      setData(res)
      setName(res.kit.name)
      setDescription(res.kit.description || "")
      setPrice(String(res.kit.price_eur))
      setSectionsJson(JSON.stringify(res.kit.sections, null, 2))
      setRulesJson(JSON.stringify(res.rules, null, 2))
      setTemplateJson(JSON.stringify(res.template, null, 2))
    } catch (e) {
      setError(String(e))
    }
  }

  useEffect(() => {
    let cancelled = false
    const init = async () => {
      try {
        const jwt = await getToken()
        if (!jwt) {
          router.replace("/")
          return
        }
        const me = await apiGet<{ role: string }>("/api/me", jwt)
        if (!isAdminRole(me.role)) {
          router.replace("/")
          return
        }
        if (!cancelled) {
          setAuthorized(true)
          setToken(jwt)
        }
        await load(jwt)
      } catch (e) {
        if (!cancelled) {
          setError(String(e))
          setAuthorized(false)
        }
      }
    }
    init()
    return () => {
      cancelled = true
    }
  }, [getToken, kitCode, router])

  const save = async () => {
    try {
      if (!token) return
      setError("")
      await apiSend(`/api/admin/kits/${kitCode}`, "PUT", {
        name,
        description,
        price_eur: Number(price),
        sections: JSON.parse(sectionsJson),
        rules: JSON.parse(rulesJson),
        template: JSON.parse(templateJson),
      }, token)
      await load(token)
    } catch (e) {
      setError(String(e))
    }
  }

  if (!authorized) return null

  return (
    <main className="stack">
      <Link href="/admin" className="muted">
        ← Inapoi la Super Contabil
      </Link>

      <div className="card stack">
        <h1>Configurare kit</h1>
        <div className="grid grid-2">
          <div>
            <label>Nume</label>
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <label>Pret EUR</label>
            <input value={price} onChange={(e) => setPrice(e.target.value)} />
          </div>
        </div>
        <div>
          <label>Descriere</label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
        </div>
      </div>

      <div className="card stack">
        <label>Sectiuni si intrebari (JSON)</label>
        <textarea rows={18} value={sectionsJson} onChange={(e) => setSectionsJson(e.target.value)} />
      </div>

      <div className="card stack">
        <label>Reguli de risc (JSON)</label>
        <textarea rows={18} value={rulesJson} onChange={(e) => setRulesJson(e.target.value)} />
      </div>

      <div className="card stack">
        <label>Template PDF (JSON)</label>
        <textarea rows={10} value={templateJson} onChange={(e) => setTemplateJson(e.target.value)} />
      </div>

      <div className="row">
        <button onClick={save}>Salveaza configurarea</button>
      </div>

      {error && <p className="muted">{error}</p>}
      {data && <p className="muted">Versiunea publicata curenta este editabila direct in acest MVP V2.</p>}
    </main>
  )
}
