"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
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

export default function ClientDetailPage() {
  const params = useParams()
  const clientId = params.id as string
  const { getToken } = useAuth()

  const [client, setClient] = useState<Client | null>(null)
  const [profileDefinition, setProfileDefinition] = useState<ProfileDefinitionSection[]>([])
  const [profileAnswers, setProfileAnswers] = useState<Record<string, unknown>>({})
  const [kits, setKits] = useState<Kit[]>([])
  const [error, setError] = useState("")

  const load = async () => {
    try {
      const token = await getToken()
      const [clientRes, profileRes, kitsRes] = await Promise.all([
        apiGet<Client>(`/api/clients/${clientId}`, token ?? undefined),
        apiGet<{ definition: ProfileDefinitionSection[]; answers: Record<string, unknown> }>(`/api/clients/${clientId}/profile`, token ?? undefined),
        apiGet<Kit[]>("/api/kits", token ?? undefined),
      ])
      setClient(clientRes)
      setProfileDefinition(profileRes.definition)
      setProfileAnswers(profileRes.answers || {})
      setKits(kitsRes)
    } catch (e) {
      setError(String(e))
    }
  }

  useEffect(() => {
    load()
  }, [clientId])

  const profileQuestionCount = useMemo(
    () => profileDefinition.reduce((acc, section) => acc + section.questions.length, 0),
    [profileDefinition]
  )

  const saveProfile = async () => {
    const token = await getToken()
    await apiSend(`/api/clients/${clientId}/profile`, "PUT", { answers: profileAnswers }, token ?? undefined)
  }

  return (
    <main className="stack">
      <Link href="/clients" className="muted">
        ← Inapoi la clienti
      </Link>

      <div className="card">
        <h1>{client?.name || "Client"}</h1>
        <p className="muted">{client?.company_name || "Profil nou"}</p>
      </div>

      <div className="card stack">
        <div className="section-title">
          <div>
            <h2>Profil general comun</h2>
            <p className="muted">{profileQuestionCount} intrebari comune, completate o singura data.</p>
          </div>
          <button onClick={saveProfile}>Salveaza profil</button>
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
