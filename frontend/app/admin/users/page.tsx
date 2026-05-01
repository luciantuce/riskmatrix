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
  code: string
  name: string
}

export default function AdminUsersPage() {
  const router = useRouter()
  const { getToken } = useAuth()
  const [token, setToken] = useState<string | null>(null)
  const [authorized, setAuthorized] = useState(false)
  const [selfRole, setSelfRole] = useState<string>("client")
  const [users, setUsers] = useState<AdminUser[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [selectedProductByUser, setSelectedProductByUser] = useState<Record<number, string>>({})
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")
  const [busyRoleUserId, setBusyRoleUserId] = useState<number | null>(null)
  const [busyGrantUserId, setBusyGrantUserId] = useState<number | null>(null)

  const canManageRoles = selfRole === "super_admin"

  const sortedUsers = useMemo(
    () => [...users].sort((a, b) => a.email.localeCompare(b.email)),
    [users],
  )

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

  const grantProduct = async (userId: number) => {
    if (!token || !canManageRoles) return
    const productCode = selectedProductByUser[userId]
    if (!productCode) return
    try {
      setBusyGrantUserId(userId)
      setNotice("")
      setError("")
      await apiSend(`/api/admin/users/${userId}/subscriptions`, "POST", { product_code: productCode, billing_cycle: "monthly" }, token)
      setNotice("Acces acordat.")
    } catch (e) {
      setError(String(e))
      setNotice("Nu am putut acorda accesul.")
    } finally {
      setBusyGrantUserId(null)
    }
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
                  <select
                    value={selectedProductByUser[u.id] || ""}
                    onChange={(e) =>
                      setSelectedProductByUser((prev) => ({ ...prev, [u.id]: e.target.value }))
                    }
                  >
                    <option value="">Alege produs</option>
                    {products.map((p) => (
                      <option key={p.code} value={p.code}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                  <button onClick={() => grantProduct(u.id)}>Acorda acces</button>
                  {busyGrantUserId === u.id && <span className="muted">Se proceseaza...</span>}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {notice && <p className="muted">{notice}</p>}
      {error && <p className="muted">{error}</p>}
    </main>
  )
}
