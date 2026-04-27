import Link from "next/link"

export default function HomePage() {
  return (
    <main className="stack">
      <div className="card">
        <h1>Kit Platform V2</h1>
        <p className="muted">
          Varianta noua, fara autentificare, cu profil general comun, 5 kituri separate, reguli in baza de date si zona
          de administrare pentru intrebarile si regulile contabilei.
        </p>
        <div className="row" style={{ marginTop: 16 }}>
          <Link className="button" href="/clients">
            Intra in clienti
          </Link>
          <Link className="button secondary" href="/admin">
            Deschide Super Contabil
          </Link>
        </div>
      </div>
    </main>
  )
}
