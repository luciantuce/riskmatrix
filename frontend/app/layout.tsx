import "./globals.css"
import { ReactNode } from "react"
import { ClerkProvider } from "@clerk/nextjs"
import TopNav from "@/components/top-nav"

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
              <TopNav />
            </div>
          </div>
          {children}
        </body>
      </html>
    </ClerkProvider>
  )
}
