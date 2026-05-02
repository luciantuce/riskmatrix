"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useAuth } from "@clerk/nextjs"

import { apiGet, apiSend } from "@/lib/api"
import { isAdminRole } from "@/lib/roles"

type AdminUser = {
  id: number
  email: string
  full_name: string | null
  role: "client" | "admin" | "super_admin"
  created_at: string
}

type Product = {
  id: number
  code: string
  name: string
  type: "kit" | "bundle"
  kit_id: number | null
  active: boolean
  display_order: number
}

export default function AdminUsersPage() {
  const router = useRouter()
  const { getToken } = useAuth()
  const [token, setToken] = useState<string | null>(null)
  const [authorized, setAuthorized] = useState(false)
  const [selfRole, setSelfRole] = useState<string>("client")
  const [users, setUsers] = useState<AdminUser[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")
  const [busyRoleUserId, setBusyRoleUserId] = useState<number | null>(null)
  const [busyGrantUserId, setBusyGrantUserId] = useState<number | null>(null)
  const [grantUser, setGrantUser] = useState<AdminUser | null>(null)
  const [selectedProductCodes, setSelectedProductCodes] = useState<string[]>([])
  const [autoBundle, setAutoBundle] = useState(true)

  const canManageRoles = selfRole === "super_admin"

  const sortedUsers = useMemo(
    () => [...users].sort((a, b) => a.email.localeCompare(b.email)),
    [users],
  )
  const kitProducts = useMemo(() => products.filter((p) => p.type === "kit"), [products])
  const bundleProduct = useMemo(() => products.find((p) => p.type === "bundle"), [products])

  const loadUsers = async (jwt: string) => {
    const rows = await apiGet<AdminUser[]>("/api/admin/users", jwt)
    setUsers(rows)
  }

  const loadProducts = async (jwt: string) => {
    const rows = await apiGet<Product[]>("/api/products", jwt)
    setProducts(rows)
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
          setToken(jwt)
          setSelfRole(me.role)
          setAuthorized(true)
        }
        await loadUsers(jwt)
        await loadProducts(jwt)
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
  }, [getToken, router])

  const changeRole = async (userId: number, role: AdminUser["role"]) => {
    if (!token || !canManageRoles) return
    try {
      setBusyRoleUserId(userId)
      setNotice("")
      setError("")
      await apiSend(`/api/admin/users/${userId}/role`, "PUT", { role }, token)
      await loadUsers(token)
      setNotice("Rol actualizat.")
    } catch (e) {
      setError(String(e))
      setNotice("Nu am putut actualiza rolul.")
    } finally {
      setBusyRoleUserId(null)
    }
  }

  const grantProducts = async (userId: number, productCodes: string[]) => {
    if (!token || !canManageRoles) return
    if (!productCodes.length) return
    try {
      setBusyGrantUserId(userId)
      setNotice("")
      setError("")
      for (const productCode of productCodes) {
        await apiSend(
          `/api/admin/users/${userId}/subscriptions`,
          "POST",
          { product_code: productCode, billing_cycle: "monthly" },
          token,
        )
      }
      setNotice(`Acces acordat (${productCodes.length} produs${productCodes.length > 1 ? "e" : ""}).`)
    } catch (e) {
      setError(String(e))
      setNotice("Nu am putut acorda accesul.")
    } finally {
      setBusyGrantUserId(null)
    }
  }

  const openGrantModal = (user: AdminUser) => {
    setGrantUser(user)
    setSelectedProductCodes([])
    setAutoBundle(true)
  }

  const closeGrantModal = () => {
    setGrantUser(null)
    setSelectedProductCodes([])
  }

  const toggleProductCode = (code: string) => {
    setSelectedProductCodes((prev) =>
      prev.includes(code) ? prev.filter((x) => x !== code) : [...prev, code],
    )
  }

  const submitGrantModal = async () => {
    if (!grantUser) return
    const selectedSet = new Set(selectedProductCodes)
    const selectedAllKits = kitProducts.length > 0 && kitProducts.every((k) => selectedSet.has(k.code))
    const finalCodes =
      autoBundle && selectedAllKits && bundleProduct
        ? [bundleProduct.code]
        : selectedProductCodes
    await grantProducts(grantUser.id, finalCodes)
    closeGrantModal()
  }

  if (!authorized) return null

  return (
    <main className="stack">
      <Link href="/admin" className="muted">
        ← Inapoi la Super Contabil
      </Link>

      <div className="card stack">
        <h1>Management utilizatori</h1>
        <p className="muted">
          Doar rolul <strong>super_admin</strong> poate modifica drepturile.
        </p>
      </div>

      <div className="card stack">
        {sortedUsers.map((u) => (
          <div key={u.id} className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
            <div className="stack" style={{ gap: 4 }}>
              <strong>{u.full_name || u.email}</strong>
              <span className="muted">{u.email}</span>
            </div>
            <div className="row" style={{ gap: 8, alignItems: "center" }}>
              <span className="pill">{u.role}</span>
              {canManageRoles && (
                <div className="row" style={{ alignItems: "center" }}>
                  <select
                    value={u.role}
                    disabled={busyRoleUserId === u.id}
                    onChange={(e) => changeRole(u.id, e.target.value as AdminUser["role"])}
                  >
                    <option value="client">client</option>
                    <option value="admin">admin</option>
                    <option value="super_admin">super_admin</option>
                  </select>
                  <button onClick={() => openGrantModal(u)}>Acorda acces…</button>
                  {busyGrantUserId === u.id && <span className="muted">Se proceseaza...</span>}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {grantUser && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(12, 17, 29, 0.55)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
            padding: 16,
          }}
        >
          <div className="card stack" style={{ width: "min(780px, 100%)", maxHeight: "85vh", overflow: "auto" }}>
            <div className="section-title" style={{ marginBottom: 4 }}>
              <h2 style={{ margin: 0 }}>Acorda acces manual</h2>
              <button className="button secondary" onClick={closeGrantModal}>
                Inchide
              </button>
            </div>
            <p className="muted" style={{ margin: 0 }}>
              Utilizator: <strong>{grantUser.email}</strong>
            </p>
            <div className="row" style={{ alignItems: "center", gap: 10 }}>
              <input
                type="checkbox"
                checked={autoBundle}
                onChange={(e) => setAutoBundle(e.target.checked)}
                style={{ width: 16, height: 16 }}
              />
              <span>
                Activeaza automat <strong>bundle</strong> daca sunt selectate toate kiturile.
              </span>
            </div>
            <div className="stack" style={{ gap: 8 }}>
              <strong>Kiturile si produsele disponibile</strong>
              {products.map((p) => (
                <label key={p.code} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 0, fontWeight: 500 }}>
                  <input
                    type="checkbox"
                    checked={selectedProductCodes.includes(p.code)}
                    onChange={() => toggleProductCode(p.code)}
                    style={{ width: 16, height: 16 }}
                  />
                  <span>{p.name}</span>
                  <span className="pill">{p.type}</span>
                </label>
              ))}
            </div>
            <div className="row" style={{ justifyContent: "flex-end" }}>
              <button onClick={submitGrantModal} disabled={!selectedProductCodes.length || busyGrantUserId === grantUser.id}>
                {busyGrantUserId === grantUser.id ? "Se acorda..." : "Confirma acces"}
              </button>
            </div>
          </div>
        </div>
      )}

      {notice && <p className="muted">{notice}</p>}
      {error && <p className="muted">{error}</p>}
    </main>
  )
}
