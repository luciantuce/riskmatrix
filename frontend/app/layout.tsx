import "./globals.css"
import Link from "next/link"
import { ReactNode } from "react"
import { ClerkProvider, SignedIn, SignedOut, UserButton } from "@clerk/nextjs"

export const metadata = {
  title: "RiskMatrix AI",
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="ro">
        <body>
          <div className="topbar">
            <div className="topbar-inner">
              <strong>RiskMatrix AI</strong>
              <div className="nav">
                <SignedIn>
                  <Link href="/">Dashboard</Link>
                  <Link href="/clients">Clienti</Link>
                  <Link href="/admin">Super Contabil</Link>
                  <UserButton afterSignOutUrl="/sign-in" />
                </SignedIn>
                <SignedOut>
                  <Link href="/sign-in">Autentificare</Link>
                </SignedOut>
              </div>
            </div>
          </div>
          {children}
        </body>
      </html>
    </ClerkProvider>
  )
}
