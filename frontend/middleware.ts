import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

// IP allowlist middleware — private beta gate.
//
// Reads ALLOWED_IPS env var (comma-separated). Supports:
//   - IPv4 single address           (e.g. 82.79.162.153)
//   - IPv4 CIDR                     (e.g. 212.45.0.0/24)
//   - IPv6 single address           (e.g. 2a02:2f04:b0f:4500::1)
//   - IPv6 CIDR                     (e.g. 2a02:2f04:b0f:4500::/64)
//
// Empty / unset = fail-open (no restriction).
// /api/health is exempted so Railway's healthcheck always passes.

type V4Range = { network: number; mask: number }
type V6Range = { network: bigint; mask: bigint }

function ipv4ToInt(ip: string): number | null {
  const parts = ip.split(".")
  if (parts.length !== 4) return null
  let acc = 0
  for (const p of parts) {
    const n = Number(p)
    if (!Number.isInteger(n) || n < 0 || n > 255) return null
    acc = (acc << 8) + n
  }
  return acc >>> 0
}

function ipv6ToBigInt(ip: string): bigint | null {
  ip = ip.split("%")[0] // strip zone id if present
  if (ip.includes(".")) return null // IPv4-mapped IPv6 — out of scope
  let parts: string[]
  if (ip.includes("::")) {
    const [head, tail] = ip.split("::")
    const headParts = head ? head.split(":") : []
    const tailParts = tail ? tail.split(":") : []
    const fill = 8 - headParts.length - tailParts.length
    if (fill < 0) return null
    parts = [...headParts, ...Array(fill).fill("0"), ...tailParts]
  } else {
    parts = ip.split(":")
  }
  if (parts.length !== 8) return null
  let acc = 0n
  for (const p of parts) {
    if (!/^[0-9a-fA-F]{0,4}$/.test(p)) return null
    const n = parseInt(p || "0", 16)
    if (isNaN(n) || n < 0 || n > 0xffff) return null
    acc = (acc << 16n) | BigInt(n)
  }
  return acc
}

function v6Mask(bits: number): bigint {
  if (bits <= 0) return 0n
  if (bits >= 128) return (1n << 128n) - 1n
  return ((1n << BigInt(bits)) - 1n) << BigInt(128 - bits)
}

const v4Ranges: V4Range[] = []
const v6Ranges: V6Range[] = []

const allowedRaw = (process.env.ALLOWED_IPS || "")
  .split(",")
  .map(s => s.trim())
  .filter(Boolean)

for (const entry of allowedRaw) {
  const [addr, bitsStr] = entry.includes("/") ? entry.split("/") : [entry, null]
  const isV6 = addr.includes(":")
  if (isV6) {
    const network = ipv6ToBigInt(addr)
    if (network === null) {
      console.warn(`[middleware] ignoring invalid IPv6 entry: ${entry}`)
      continue
    }
    const bits = bitsStr === null ? 128 : Number(bitsStr)
    if (!Number.isInteger(bits) || bits < 0 || bits > 128) {
      console.warn(`[middleware] ignoring invalid IPv6 CIDR bits: ${entry}`)
      continue
    }
    const mask = v6Mask(bits)
    v6Ranges.push({ network: network & mask, mask })
  } else {
    const network = ipv4ToInt(addr)
    if (network === null) {
      console.warn(`[middleware] ignoring invalid IPv4 entry: ${entry}`)
      continue
    }
    const bits = bitsStr === null ? 32 : Number(bitsStr)
    if (!Number.isInteger(bits) || bits < 0 || bits > 32) {
      console.warn(`[middleware] ignoring invalid IPv4 CIDR bits: ${entry}`)
      continue
    }
    const mask = bits === 0 ? 0 : ((~0 << (32 - bits)) >>> 0)
    v4Ranges.push({ network: network & mask, mask })
  }
}

function isAllowed(ip: string): boolean {
  if (ip.includes(":")) {
    const ipInt = ipv6ToBigInt(ip)
    if (ipInt === null) return false
    for (const { network, mask } of v6Ranges) {
      if ((ipInt & mask) === network) return true
    }
    return false
  } else {
    const ipInt = ipv4ToInt(ip)
    if (ipInt === null) return false
    for (const { network, mask } of v4Ranges) {
      if ((ipInt & mask) === network) return true
    }
    return false
  }
}

function clientIp(request: NextRequest): string | null {
  const fwd = request.headers.get("x-forwarded-for")
  if (fwd) return fwd.split(",")[0].trim()
  const real = request.headers.get("x-real-ip")
  if (real) return real.trim()
  return null
}

export function middleware(request: NextRequest) {
  if (request.nextUrl.pathname === "/api/health") {
    return NextResponse.next()
  }
  if (allowedRaw.length === 0) {
    return NextResponse.next()
  }
  const ip = clientIp(request)
  if (!ip || !isAllowed(ip)) {
    return new NextResponse("Forbidden", { status: 403 })
  }
  return NextResponse.next()
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml).*)",
  ],
}
