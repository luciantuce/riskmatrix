import "./globals.css"
import Link from "next/link"
import { ReactNode } from "react"

export const metadata = {
  title: "Kit Platform V2",
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ro">
      <body>
        <div className="topbar">
          <div className="topbar-inner">
            <strong>Kit Platform V2</strong>
            <div className="nav">
              <Link href="/">Dashboard</Link>
              <Link href="/clients">Clienti</Link>
              <Link href="/admin">Super Contabil</Link>
            </div>
          </div>
        </div>
        {children}
      </body>
    </html>
  )
}
