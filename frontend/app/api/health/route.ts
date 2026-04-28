// Lightweight healthcheck endpoint used by Railway and exempted from the
// IP allowlist middleware. Must remain trivial — no DB, no auth, no headers
// that could leak information.

export const dynamic = "force-dynamic"
export const runtime = "nodejs"

export function GET() {
  return new Response(JSON.stringify({ status: "healthy" }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  })
}
