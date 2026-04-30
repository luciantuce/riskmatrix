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

export default function AdminUsersPage() {
  const router = useRouter()
  const { getToken } = useAuth()
  const [token, setToken] = useState<string | null>(null)
  const [authorized, setAuthorized] = useState(false)
  const [selfRole, setSelfRole] = useState<string>("client")
  const [users, setUsers] = useState<AdminUser[]>([])
  const [error, setError] = useState("")

  const canManageRoles = selfRole === "super_admin"

  const sortedUsers = useMemo(
    () => [...users].sort((a, b) => a.email.localeCompare(b.email)),
    [users],
  )

  const loadUsers = async (jwt: string) => {
    const rows = await apiGet<AdminUser[]>("/api/admin/users", jwt)
    setUsers(rows)
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
      setError("")
      await apiSend(`/api/admin/users/${userId}/role`, "PUT", { role }, token)
      await loadUsers(token)
    } catch (e) {
      setError(String(e))
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
                <select
                  value={u.role}
                  onChange={(e) => changeRole(u.id, e.target.value as AdminUser["role"])}
                >
                  <option value="client">client</option>
                  <option value="admin">admin</option>
                  <option value="super_admin">super_admin</option>
                </select>
              )}
            </div>
          </div>
        ))}
      </div>

      {error && <p className="muted">{error}</p>}
    </main>
  )
}
