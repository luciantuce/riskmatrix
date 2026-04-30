"use client"

import Link from "next/link"
import { useParams } from "next/navigation"
import { useEffect, useState } from "react"
import { useAuth } from "@clerk/nextjs"

import { apiGet, apiSend } from "@/lib/api"

type Question = {
  question_key: string
  label: string
  question_type: string
  required: boolean
  options: Array<{ value: string; label: string }>
  responsabil_options?: string[] | null
}

type ViewResponse = {
  definition: {
    code: string
    name: string
    description: string | null
    documentation_url: string | null
    sections: Array<{
      id: number
      title: string
      description?: string | null
      questions: Question[]
    }>
  }
  submission: Record<string, unknown>
  result: {
    risk_score: number
    risk_level: string
    risk_flags_json: string[]
    responsibility_matrix_json: Array<{ area: string; responsible_party: string }>
    engagement_level: string
    tariff_adjustment_pct?: number
    active_risks_json?: Array<{ code: string; name: string; score: number; responsible: string }>
  } | null
}

export default function KitDetailPage() {
  const params = useParams()
  const clientId = params.id as string
  const kitCode = params.kitCode as string
  const { getToken } = useAuth()

  const [data, setData] = useState<ViewResponse | null>(null)
  const [answers, setAnswers] = useState<Record<string, unknown>>({})
  const [error, setError] = useState("")

  const humanizeFlag = (flag: string) =>
    flag
      .split("_")
      .filter(Boolean)
      .map((part, index) => (index === 0 ? part.charAt(0).toUpperCase() + part.slice(1) : part))
      .join(" ")

  const riskBadgeClass = (level: string) => {
    if (level === "LOW") return "status-badge status-low"
    if (level === "MEDIUM") return "status-badge status-medium"
    if (level === "HIGH") return "status-badge status-high"
    return "status-badge status-critical"
  }

  const humanizeEngagement = (value: string) => {
    if (value === "standard") return "Standard"
    if (value === "mediu") return "Mediu"
    if (value === "ridicat") return "Ridicat"
    return value.charAt(0).toUpperCase() + value.slice(1)
  }

  const normalizeAnswer = (val: unknown): { answer: boolean; responsabil: string } | null => {
    if (val == null) return null
    if (typeof val === "object" && "answer" in (val as object)) {
      const v = val as { answer?: unknown; responsabil?: string }
      return { answer: Boolean(v.answer), responsabil: v.responsabil || "delegat" }
    }
    return { answer: Boolean(val), responsabil: "delegat" }
  }

  const load = async () => {
    try {
      const token = await getToken()
      const res = await apiGet<ViewResponse>(`/api/clients/${clientId}/kits/${kitCode}`, token ?? undefined)
      setData(res)
      setAnswers(res.submission || {})
    } catch (e) {
      setError(String(e))
    }
  }

  useEffect(() => {
    load()
  }, [clientId, kitCode])

  const save = async () => {
    try {
      const token = await getToken()
      await apiSend(`/api/clients/${clientId}/kits/${kitCode}`, "PUT", { answers }, token ?? undefined)
      await load()
    } catch (e) {
      setError(String(e))
    }
  }

  return (
    <main className="stack">
      <Link href={`/clients/${clientId}`} className="muted">
        ← Inapoi la client
      </Link>

      <div className="card stack">
        <div>
          <h1 style={{ margin: 0 }}>{data?.definition.name || kitCode}</h1>
          <p className="muted" style={{ margin: "4px 0 0 0" }}>{data?.definition.description}</p>
        </div>
      </div>

      <div className="card stack">
        {data?.definition.sections.map((section) => (
          <div key={section.id} className="stack">
            <strong>{section.title}</strong>
            {section.description && <p className="muted" style={{ margin: "0 0 8px 0", fontSize: 13 }}>{section.description}</p>}
            <div className="grid grid-2">
              {section.questions.map((question) => {
                const val = normalizeAnswer(answers[question.question_key])
                const respOpts = question.responsabil_options || question.options?.map((o) => o.value) || ["administrator", "delegat", "contabil"]
                return (
                  <div key={question.question_key} className="stack" style={{ gap: 4 }}>
                    <label>{question.label}</label>
                    {question.question_type === "risk_matrix" ? (
                      <div className="row" style={{ gap: 12, flexWrap: "wrap", alignItems: "center" }}>
                        <select
                          value={val ? (val.answer ? "true" : "false") : ""}
                          onChange={(e) => {
                            const ans = e.target.value === "" ? null : e.target.value === "true"
                            setAnswers((prev) => ({
                              ...prev,
                              [question.question_key]: ans == null ? null : { answer: ans, responsabil: normalizeAnswer(prev[question.question_key])?.responsabil || "delegat" },
                            }))
                          }}
                        >
                          <option value="">—</option>
                          <option value="true">Da</option>
                          <option value="false">Nu</option>
                        </select>
                        <select
                          value={val?.responsabil || "delegat"}
                          onChange={(e) =>
                            setAnswers((prev) => ({
                              ...prev,
                              [question.question_key]: {
                                answer: normalizeAnswer(prev[question.question_key])?.answer ?? false,
                                responsabil: e.target.value,
                              },
                            }))
                          }
                        >
                          {respOpts.map((opt) => (
                            <option key={opt} value={opt}>
                              {opt.charAt(0).toUpperCase() + opt.slice(1)}
                            </option>
                          ))}
                        </select>
                      </div>
                    ) : question.question_type === "boolean" ? (
                      <select
                        value={String(answers[question.question_key] ?? "")}
                        onChange={(e) =>
                          setAnswers((prev) => ({
                            ...prev,
                            [question.question_key]: e.target.value === "" ? "" : e.target.value === "true",
                          }))
                        }
                      >
                        <option value="">—</option>
                        <option value="true">Da</option>
                        <option value="false">Nu</option>
                      </select>
                    ) : question.question_type === "single_choice" ? (
                      <select
                        value={String(answers[question.question_key] || "")}
                        onChange={(e) => setAnswers((prev) => ({ ...prev, [question.question_key]: e.target.value }))}
                      >
                        <option value="">—</option>
                        {question.options.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        value={String(answers[question.question_key] || "")}
                        onChange={(e) => setAnswers((prev) => ({ ...prev, [question.question_key]: e.target.value }))}
                      />
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        ))}

        <div className="row" style={{ flexWrap: "wrap", gap: 12 }}>
          <button onClick={save}>Salveaza si calculeaza</button>
          <a className="button secondary" href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8010"}/api/clients/${clientId}/kits/${kitCode}/pdf`} target="_blank">
            Descarca PDF
          </a>
          <a
            href={data?.definition.documentation_url || `/docs/kit-${kitCode}.pdf`}
            target="_blank"
            rel="noopener noreferrer"
            className="button secondary"
          >
            Biblioteca
          </a>
        </div>
      </div>

      {data?.result && (
        <div className="card stack">
          <h2>Rezultat</h2>
          <div className="result-grid">
            <div className="result-card">
              <div className="result-label">Scor de risc</div>
              <div className="result-value">{data.result.risk_score}</div>
            </div>
            <div className="result-card">
              <div className="result-label">Nivel</div>
              <div>
                <span className={riskBadgeClass(data.result.risk_level)}>{data.result.risk_level}</span>
              </div>
            </div>
            <div className="result-card">
              <div className="result-label">Nivel de implicare</div>
              <div className="result-value" style={{ fontSize: 18 }}>{humanizeEngagement(data.result.engagement_level)}</div>
            </div>
            <div className="result-card">
              <div className="result-label">Ajustare onorariu</div>
              <div className="result-value" style={{ fontSize: 18 }}>
                {data.result.tariff_adjustment_pct != null ? `+${data.result.tariff_adjustment_pct}%` : "0%"}
              </div>
            </div>
            <div className="result-card">
              <div className="result-label">Riscuri active</div>
              <div className="result-value" style={{ fontSize: 18 }}>{data.result.risk_flags_json?.length ?? data.result.active_risks_json?.length ?? 0}</div>
            </div>
          </div>

          {(data.result.active_risks_json?.length ?? 0) > 0 ? (
            <div className="stack">
              <strong>Riscuri identificate</strong>
              <div className="flag-list">
                {data.result.active_risks_json?.map((r) => (
                  <span key={r.code} className="flag-badge" title={`Scor: ${r.score}, Responsabil: ${r.responsible}`}>
                    {r.name} ({r.code})
                  </span>
                ))}
              </div>
            </div>
          ) : data.result.risk_flags_json?.length ? (
            <div className="stack">
              <strong>Flag-uri</strong>
              <div className="flag-list">
                {data.result.risk_flags_json.map((flag) => (
                  <span key={flag} className="flag-badge">
                    {humanizeFlag(flag)}
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <div className="stack">
              <strong>Riscuri</strong>
              <div className="muted">Nu au fost identificate riscuri pentru acest kit.</div>
            </div>
          )}

          <div className="stack">
            <strong>Matrice responsabilitati</strong>
            <div className="matrix-list">
              {(data.result.responsibility_matrix_json || []).map((row, index) => (
                <div key={`${row.area}-${index}`} className="matrix-item">
                  <div className="matrix-area">{row.area}</div>
                  <div className="matrix-owner">{row.responsible_party}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {error && <p className="muted">{error}</p>}
    </main>
  )
}
