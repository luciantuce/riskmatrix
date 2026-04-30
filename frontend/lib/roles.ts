export type AppRole = "client" | "admin" | "super_admin"

export function isAdminRole(role?: string | null): boolean {
  return role === "admin" || role === "super_admin"
}
