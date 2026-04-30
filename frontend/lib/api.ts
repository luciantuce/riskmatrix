const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8010"

export async function apiGet<T>(path: string, token?: string): Promise<T> {
  const headers: Record<string, string> = {}
  if (token) headers["Authorization"] = `Bearer ${token}`

  const res = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
    headers,
  })
  if (!res.ok) {
    throw new Error(await res.text())
  }
  return res.json()
}

export async function apiSend<T>(
  path: string,
  method: "POST" | "PUT",
  body: unknown,
  token?: string,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  }
  if (token) headers["Authorization"] = `Bearer ${token}`

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    throw new Error(await res.text())
  }
  return res.json()
}
