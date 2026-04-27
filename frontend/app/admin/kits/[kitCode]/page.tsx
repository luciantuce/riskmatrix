"use client"

import Link from "next/link"
import { useParams } from "next/navigation"
import { useEffect, useState } from "react"

import { apiGet, apiSend } from "@/lib/api"

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
  const kitCode = params.kitCode as string

  const [data, setData] = useState<AdminData | null>(null)
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [price, setPrice] = useState("0")
  const [sectionsJson, setSectionsJson] = useState("[]")
  const [rulesJson, setRulesJson] = useState("[]")
  const [templateJson, setTemplateJson] = useState("{}")
  const [error, setError] = useState("")

  const load = async () => {
    try {
      const res = await apiGet<AdminData>(`/api/admin/kits/${kitCode}`)
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
    load()
  }, [kitCode])

  const save = async () => {
    try {
      setError("")
      await apiSend(`/api/admin/kits/${kitCode}`, "PUT", {
        name,
        description,
        price_eur: Number(price),
        sections: JSON.parse(sectionsJson),
        rules: JSON.parse(rulesJson),
        template: JSON.parse(templateJson),
      })
      await load()
    } catch (e) {
      setError(String(e))
    }
  }

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
