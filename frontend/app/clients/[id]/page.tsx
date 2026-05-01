"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { useParams } from "next/navigation"
import { useAuth } from "@clerk/nextjs"

import { apiGet, apiSend } from "@/lib/api"

type ProfileDefinitionSection = {
  id: string
  title: string
  questions: Array<{
    key: string
    label: string
    type: string
    required?: boolean
    options?: string[]
  }>
}

type Kit = {
  id: number
  code: string
  name: string
  description: string | null
  documentation_url: string | null
  pricing_type: string
  price_eur: number
}

type Client = {
  id: number
  name: string
  company_name: string | null
}

type ClientSummary = {
  completed_kits: number
  in_progress_kits: number
  not_started_kits: number
  highest_risk_level: string | null
  latest_risk_score: number | null
  latest_updated_at: string | null
}

type ClientKitSummary = {
  kit_id: number
  kit_code: string
  kit_name: string
  status: "completed" | "in_progress" | "not_started"
  risk_level: string | null
  risk_score: number | null
  tariff_adjustment_pct: number | null
  updated_at: string | null
}

export default function ClientDetailPage() {
  const params = useParams()
  const clientId = params.id as string
  const { getToken } = useAuth()

  const [client, setClient] = useState<Client | null>(null)
  const [profileDefinition, setProfileDefinition] = useState<ProfileDefinitionSection[]>([])
  const [profileAnswers, setProfileAnswers] = useState<Record<string, unknown>>({})
  const [kits, setKits] = useState<Kit[]>([])
  const [clientSummary, setClientSummary] = useState<ClientSummary | null>(null)
  const [kitSummaries, setKitSummaries] = useState<ClientKitSummary[]>([])
  const [error, setError] = useState("")
  const [isSavingProfile, setIsSavingProfile] = useState(false)
  const [saveNotice, setSaveNotice] = useState("")

  const load = async () => {
    try {
      const token = await getToken()
      const [clientRes, profileRes, kitsRes, summaryRes, kitSummaryRes] = await Promise.all([
        apiGet<Client>(`/api/clients/${clientId}`, token ?? undefined),
        apiGet<{ definition: ProfileDefinitionSection[]; answers: Record<string, unknown> }>(`/api/clients/${clientId}/profile`, token ?? undefined),
        apiGet<Kit[]>("/api/kits", token ?? undefined),
        apiGet<ClientSummary>(`/api/clients/${clientId}/summary`, token ?? undefined),
        apiGet<ClientKitSummary[]>(`/api/clients/${clientId}/kits/summary`, token ?? undefined),
      ])
      setClient(clientRes)
      setProfileDefinition(profileRes.definition)
      setProfileAnswers(profileRes.answers || {})
      setKits(kitsRes)
      setClientSummary(summaryRes)
      setKitSummaries(kitSummaryRes)
    } catch (e) {
      setError(String(e))
    }
  }

  useEffect(() => {
    load()
  }, [clientId])

  const saveProfile = async () => {
    try {
      setIsSavingProfile(true)
      setSaveNotice("")
      const token = await getToken()
      await apiSend(`/api/clients/${clientId}/profile`, "PUT", { answers: profileAnswers }, token ?? undefined)
      setSaveNotice("Profil salvat.")
      setTimeout(() => {
        setSaveNotice((current) => (current === "Profil salvat." ? "" : current))
      }, 2500)
    } catch (e) {
      setSaveNotice("Nu am putut salva profilul.")
      setError(String(e))
    } finally {
      setIsSavingProfile(false)
    }
  }

  const riskBadgeClass = (level?: string | null) => {
    if (!level) return "pill"
    if (level === "LOW") return "status-badge status-low"
    if (level === "MEDIUM") return "status-badge status-medium"
    if (level === "HIGH") return "status-badge status-high"
    return "status-badge status-critical"
  }

  const statusLabel = (status: ClientKitSummary["status"]) => {
    if (status === "completed") return "completat"
    if (status === "in_progress") return "in lucru"
    return "neinceput"
  }

  const summaryByKitCode = new Map(kitSummaries.map((row) => [row.kit_code, row]))

  return (
    <main className="stack">
      <Link href="/clients" className="muted">
        ← Inapoi la clienti
      </Link>

      <div className="card">
        <h1>{client?.name || "Client"}</h1>
        <p className="muted">{client?.company_name || "Profil nou"}</p>
        {clientSummary && (
          <div className="row" style={{ marginTop: 8 }}>
            <span className="pill">{clientSummary.completed_kits} kituri completate</span>
            <span className="pill">{clientSummary.in_progress_kits} in lucru</span>
            <span className="pill">{clientSummary.not_started_kits} neincepute</span>
            {clientSummary.highest_risk_level && (
              <span className={riskBadgeClass(clientSummary.highest_risk_level)}>
                Risc maxim: {clientSummary.highest_risk_level}
              </span>
            )}
            {clientSummary.latest_risk_score != null && (
              <span className="pill">Ultimul scor: {clientSummary.latest_risk_score}</span>
            )}
          </div>
        )}
      </div>

      <div className="card stack">
        <div className="section-title">
          <div>
            <h2>Profil general comun</h2>
            {saveNotice && <p className="muted" style={{ margin: "6px 0 0 0" }}>{saveNotice}</p>}
          </div>
          <button onClick={saveProfile} disabled={isSavingProfile}>
            {isSavingProfile ? "Salvez..." : "Salveaza profil"}
          </button>
        </div>

        {profileDefinition.map((section) => (
          <div key={section.id} className="stack">
            <strong>{section.title}</strong>
            <div className="grid grid-2">
              {section.questions.map((question) => (
                <div key={question.key}>
                  <label>{question.label}</label>
                  {question.type === "single_choice" ? (
                    <select
                      value={String(profileAnswers[question.key] || "")}
                      onChange={(e) => setProfileAnswers((prev) => ({ ...prev, [question.key]: e.target.value }))}
                    >
                      <option value="">—</option>
                      {(question.options || []).map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  ) : question.type === "multi_choice" ? (
                    <div className="stack" style={{ gap: 8 }}>
                      {(question.options || []).map((option) => {
                        const selected = Array.isArray(profileAnswers[question.key])
                          ? (profileAnswers[question.key] as string[]).includes(option)
                          : false
                        return (
                          <label key={option} style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 500, marginBottom: 0 }}>
                            <input
                              type="checkbox"
                              checked={selected}
                              onChange={(e) => {
                                const current = Array.isArray(profileAnswers[question.key])
                                  ? ([...(profileAnswers[question.key] as string[])] as string[])
                                  : []
                                const next = e.target.checked
                                  ? [...current, option]
                                  : current.filter((item) => item !== option)
                                setProfileAnswers((prev) => ({ ...prev, [question.key]: next }))
                              }}
                              style={{ width: 16, height: 16 }}
                            />
                            <span>{option}</span>
                          </label>
                        )
                      })}
                    </div>
                  ) : (
                    <input
                      value={String(profileAnswers[question.key] || "")}
                      onChange={(e) => setProfileAnswers((prev) => ({ ...prev, [question.key]: e.target.value }))}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="stack">
        <div className="section-title">
          <h2>Kiturile clientului</h2>
        </div>
        <div className="grid grid-2">
          {kits.map((kit) => (
            <div key={kit.code} className="card stack">
              {summaryByKitCode.get(kit.code) && (
                <div className="row" style={{ gap: 8 }}>
                  <span className="pill">{statusLabel(summaryByKitCode.get(kit.code)!.status)}</span>
                  {summaryByKitCode.get(kit.code)!.risk_level && (
                    <span className={riskBadgeClass(summaryByKitCode.get(kit.code)!.risk_level)}>
                      {summaryByKitCode.get(kit.code)!.risk_level}
                    </span>
                  )}
                  {summaryByKitCode.get(kit.code)!.risk_score != null && (
                    <span className="pill">Scor {summaryByKitCode.get(kit.code)!.risk_score}</span>
                  )}
                </div>
              )}
              <Link href={`/clients/${clientId}/kits/${kit.code}`} style={{ textDecoration: "none", color: "inherit" }}>
                <div className="section-title" style={{ marginBottom: 0 }}>
                  <strong>{kit.name}</strong>
                  <span className="pill">{kit.price_eur.toFixed(0)} EUR</span>
                </div>
                <span className="muted">{kit.description}</span>
              </Link>
              <div className="row" style={{ marginTop: "auto", gap: 8 }}>
                {kit.documentation_url && (
                  <a
                    href={kit.documentation_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="button secondary"
                    style={{ fontSize: 14 }}
                  >
                    Biblioteca
                  </a>
                )}
                <Link href={`/clients/${clientId}/kits/${kit.code}`} className="button" style={{ fontSize: 14 }}>
                  Deschide kit
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>

      {error && <p className="muted">{error}</p>}
    </main>
  )
}
