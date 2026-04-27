# Deploy pe Railway — Kit Platform V3

Ghid pas cu pas pentru a aduce aplicația în producție pe Railway.
Estimare timp total: **~45 minute** prima dată.

---

## 0. Înainte de orice — verificare locală

Asigură-te că noul stack rulează local cu Postgres:

```bash
cd riskmatrix
docker compose up --build
```

(`docker-compose` pornește backend-ul cu `start.sh`: migrații Alembic, apoi uvicorn.)

Apoi deschide:

- frontend: <http://localhost:3010>
- backend health: <http://localhost:8010/health>
- admin (cere user/parolă din `docker-compose.yml`):
  <http://localhost:8010/api/admin/kits/affiliate_compliance>
  → user: `admin` / pass: `dev-password-change-me`

Dacă merge local, treci mai departe.

---

## 1. Push proiectul pe GitHub

Railway deploy-ează din GitHub, deci ai nevoie de un repo.

```bash
cd riskmatrix
git init
git add .
git commit -m "Initial v3 — production-ready scaffold"
# creează un repo gol pe github.com/<tu>/riskmatrix, apoi:
git remote add origin git@github.com:<tu>/riskmatrix.git
git branch -M main
git push -u origin main
```

> **Atenție**: `.gitignore` deja exclude `.env`, `data/`, `node_modules/`,
> `__pycache__/`. Verifică să nu fi commit-at vreun secret cu
> `git log --all --full-history -- .env`.

---

## 2. Creează contul Railway și un proiect nou

1. Mergi la <https://railway.app> → **Login with GitHub**.
2. Activează planul **Hobby ($5/lună include $5 credit)** sau **Pro** dacă
   vrei mai mult headroom.
3. Click **New Project** → **Deploy from GitHub repo** → alege
   `riskmatrix`.
4. Railway o să încerce să deploy-eze din rădăcină — îl oprești pentru moment;
   noi vrem să creăm 3 servicii separate manual.

---

## 3. Adaugă serviciul Postgres

În proiect:

1. Click **+ New** → **Database** → **Add PostgreSQL**.
2. Așteaptă să se provisionezeze (~30 sec).
3. Notează: Railway expune automat variabila `DATABASE_URL` care se
   referențiază din alte servicii ca `${{Postgres.DATABASE_URL}}`.

---

## 4. Configurează serviciul Backend

1. Click **+ New** → **GitHub Repo** → alege `riskmatrix` din nou.
2. În tab-ul **Settings** al serviciului:
   - **Service Name**: `backend`
   - **Root Directory**: `/backend`
   - **Watch Paths**: `/backend/**` (build doar când se schimbă backend)
3. Railway o să detecteze automat `backend/railway.json` și
   `Dockerfile.prod`.
4. În tab-ul **Variables** adaugă:

   | Variable | Valoare |
   |----------|---------|
   | `ENVIRONMENT` | `production` |
   | `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
   | `CORS_ORIGINS` | (lasă gol pentru moment, completezi după ce ai URL-ul de frontend) |
   | `ADMIN_USERNAME` | `admin` |
   | `ADMIN_PASSWORD` | (generează unul puternic — `openssl rand -base64 24`) |
   | `SEED_ON_STARTUP` | `true` (doar pentru primul deploy; după setezi `false`) |

5. În tab-ul **Settings** → **Networking** → **Generate Domain**.
   Vei primi ceva de forma `backend-production-xxxx.up.railway.app`.
   **Copiază URL-ul** — îți va trebui pentru frontend.

6. Așteaptă să termine deploy-ul (vezi **Deployments** → log-uri).
   Verifică:

   ```bash
   curl https://backend-production-xxxx.up.railway.app/health
   # ar trebui să returneze {"status":"healthy"}
   ```

---

## 5. Configurează serviciul Frontend

1. Click **+ New** → **GitHub Repo** → alege `riskmatrix`.
2. În **Settings**:
   - **Service Name**: `frontend`
   - **Root Directory**: `/frontend`
   - **Watch Paths**: `/frontend/**`
3. În **Variables**:

   | Variable | Valoare |
   |----------|---------|
   | `NEXT_PUBLIC_API_URL` | URL-ul backend de la pas 4.5 (ex: `https://backend-production-xxxx.up.railway.app`) |

   > **Important**: `NEXT_PUBLIC_*` vars sunt baked-in în build, deci după
   > ce o setezi prima dată, trigger un redeploy manual ca să fie aplicată.

4. **Settings** → **Networking** → **Generate Domain**.
   Vei primi `frontend-production-xxxx.up.railway.app`.

5. **Întoarce-te la backend** și completează `CORS_ORIGINS` cu URL-ul de
   frontend (fără slash final):

   ```
   CORS_ORIGINS=https://frontend-production-xxxx.up.railway.app
   ```

   Backend-ul se va re-deploy automat.

---

## 6. Verificare finală

1. Deschide URL-ul frontend în browser.
2. Verifică că poți crea un client și completa un kit.
3. Generează un PDF — trebuie să se descarce.
4. Pe `/admin/kits/<code>` browser-ul trebuie să-ți ceară user/parolă.

---

## 7. Domeniu propriu (opțional, dar recomandat)

În fiecare serviciu (`frontend` și/sau `backend`):

1. **Settings** → **Networking** → **Custom Domain** → `app.exemplu.ro`.
2. Railway îți dă un CNAME — îl adaugi la registrar (Namecheap/Cloudflare).
3. Așteaptă propagarea DNS (5–60 min). Railway emite SSL automat (Let's Encrypt).
4. **Important**: după ce frontend-ul are domeniu nou:
   - actualizează `NEXT_PUBLIC_API_URL` în frontend dacă și backend-ul are
     domeniu propriu;
   - actualizează `CORS_ORIGINS` în backend cu noul domeniu de frontend.

---

## 8. După primul deploy reușit — IMPORTANT

1. **Setează `SEED_ON_STARTUP=false`** pe backend.
   Altfel, la fiecare redeploy, seeder-ul s-ar putea suprapune cu editările
   tale din `/admin`.
2. **Configurează backup-uri Postgres**:
   - Settings serviciul Postgres → **Backups** → activează zilnic.
3. **Salvează parola admin** într-un password manager.
4. (Recomandat) Adaugă un **Sentry DSN** pentru error tracking — vezi
   `BACKLOG.md` pentru următorii pași.

---

## Comenzi utile

```bash
# Logs live de la backend
railway logs -s backend

# SSH în container
railway run --service backend bash

# Rulează manual o migrație
railway run --service backend alembic upgrade head

# Listare migrații
railway run --service backend alembic history
```

(necesită `npm i -g @railway/cli` și `railway login`)

---

## Costuri estimate

Pentru un MVP cu trafic mic (sub 1000 useri/lună):

| Componentă | Cost lunar estimat |
|-----------|-------------------|
| Backend (Hobby) | ~$3–5 |
| Frontend (Hobby) | ~$2–4 |
| Postgres (Hobby) | ~$2–3 |
| **Total** | **~$7–12** |

Hobby plan-ul ($5/lună fix) include $5 credit consumabil, deci de obicei
se acoperă singur la trafic mic. Dacă consumi peste, plătești diferența
ca usage-based.

---

## Troubleshooting

**Build eșuează cu "alembic: not found"** — verifică că `requirements.txt`
include `alembic==1.13.1` și că ai făcut `git push` cu modificările.

**Frontend dă "Failed to fetch"** — `NEXT_PUBLIC_API_URL` greșit sau
`CORS_ORIGINS` pe backend nu include domeniul frontend-ului. Verifică
ambele.

**Backend pornește dar `/api/admin/*` returnează 401** — corect, e
protejat cu Basic Auth. Folosește user/pass din variabilele Railway.

**`alembic upgrade head` eșuează cu "Can't locate revision"** — directorul
`alembic/versions/` n-a ajuns în imagine. Verifică `.dockerignore`-ul să
nu-l excludă.
