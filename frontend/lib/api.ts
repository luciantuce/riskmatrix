const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8010"

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" })
  if (!res.ok) {
    throw new Error(await res.text())
  }
  return res.json()
}

export async function apiSend<T>(path: string, method: "POST" | "PUT", body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    throw new Error(await res.text())
  }
  return res.json()
}
