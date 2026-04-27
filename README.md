# Kit Platform V3

Production-ready iteration a platformei de kituri de compliance.

## Ce s-a schimbat față de V2

- **Postgres** în loc de SQLite (cu fallback la SQLite pentru dev ultra-rapid)
- **Alembic** pentru migrații versionate — fără `Base.metadata.create_all`
- **Config prin env vars** — zero secrete/valori hardcoded
- **CORS strict** pe lista de origini (nu mai e `*`)
- **Basic Auth** pe toate endpoint-urile `/api/admin/*`
- **Railway-ready**: `railway.json`-uri per serviciu, `start.sh` cu migrații
  automate pe boot, Dockerfile-uri care respectă `$PORT`
- `.dockerignore` + `.gitignore` corecte
- Security headers pe frontend

## Kit-urile (pachetele)

1. **Risc general administrativ** (`internal_fiscal_procedures`)
2. **Risc fiscal** (`digital_recurring_compliance`)
3. **Risc rezidență fiscală** (`tax_residency_nonresidents`)
4. **Risc Afiliați** (`affiliate_compliance`)
5. **Risc extins (ESG)** (`affiliate_identification`)

## Structură

```text
riskmatrix/
├── backend/
│   ├── alembic/              # migrații DB
│   ├── app/                  # config, modele, rute
│   ├── Dockerfile            # dev
│   ├── Dockerfile.prod       # Railway + self-host
│   ├── railway.json          # config Railway
│   └── start.sh              # migrations + uvicorn
├── frontend/
│   ├── app/                  # Next.js App Router
│   ├── Dockerfile.prod
│   └── railway.json
├── docker-compose.yml        # dev local (Postgres + backend + frontend)
├── docker-compose.prod.yml   # self-host (nu e pentru Railway)
├── DEPLOY.md                 # instrucțiuni Railway pas cu pas
├── .env.example
└── .gitignore
```

## Pornire rapidă — dev local cu Postgres

```bash
cd riskmatrix
cp .env.example .env          # editează dacă vrei
docker compose up --build
```

(`docker compose` rulează migrațiile prin `start.sh` înainte de seed.)

Apoi:

- frontend: <http://localhost:3010>
- backend: <http://localhost:8010>
- health: <http://localhost:8010/health>

## Dezvoltare locală fără Docker

Pornește doar Postgres cu Docker:

```bash
docker compose up -d postgres
```

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://kit:kit@localhost:5432/kit_platform
export CORS_ORIGINS=http://localhost:3010
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=dev
alembic upgrade head
uvicorn main:app --reload --port 8010
```

Frontend:

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8010 npm run dev -- -p 3010
```

## Migrații DB

Vezi `backend/alembic/README.md`. Scurt:

```bash
# după ce modifici un model:
cd backend
alembic revision --autogenerate -m "add xyz column"
# revizuiește fișierul generat în alembic/versions/
alembic upgrade head
```

## Deploy pe Railway

Vezi **[DEPLOY.md](./DEPLOY.md)** — ghid complet pas cu pas.

## Endpoint-uri principale

- `GET /health`
- `GET /api/profile/definition`
- `GET /api/clients`, `POST /api/clients`
- `GET /api/clients/{id}/profile`, `PUT /api/clients/{id}/profile`
- `GET /api/kits`
- `GET /api/clients/{id}/kits/{code}`, `PUT /api/clients/{id}/kits/{code}`
- `GET /api/clients/{id}/kits/{code}/pdf`
- `GET /api/admin/kits/{code}` 🔒 Basic Auth
- `PUT /api/admin/kits/{code}` 🔒 Basic Auth

## Ce urmează (roadmap scurt)

- Auth real (Clerk / Supabase Auth / FastAPI Users) pentru utilizatori
- Sentry pentru error tracking
- GitHub Actions CI/CD
- Teste pytest pe `risk_engine.py` și endpoint-uri critice
- PDF-uri pe Cloudflare R2 (dacă devin evidență legală)
