# Backlog — Kit Platform V3 / RiskMatrix

Defalcare pe sprint-uri pentru tranziția în B2B SaaS pentru contabili.

> Vezi `ARCHITECTURE.md` pentru context, decizii și rationale.
> Vezi `CONVENTIONS.md` pentru pattern-urile obligatorii înainte de a scrie cod.
> Ultima actualizare: 2026-05-05 (Sprint 2.1 foundations done + Sentry validat în prod)

Status legenda: `[ ]` pending, `[x]` done, `[~]` în lucru, `[!]` blocat.

---

## ✅ Sprint 0 — Deploy inițial (DONE)
## ✅ Sprint 1 — Auth foundation (DONE)

(detalii istorice în git log)

---

## 🔶 Sprint 2 — Plăți Stripe + Facturare FGO + Foundations (în curs)

**Goal:** User-ii pot cumpăra kit-uri sau bundle, plătesc în RON prin Stripe,
primesc automat factură FGO. Sentry + GDPR + CI/CD funcționale.

**Definition of Done:** Toate testele QA trec. Stripe webhook-uri tracked în
Sentry. CI rulează pe fiecare PR. Endpoint-urile GDPR funcționale.

**Branch:** `feat/sprint-2-payments`

---

### 2.1 Foundations (înainte de orice payment work)

#### 2.1.1 Unifică env vars ✅
- [x] Mutare `infra/env.example` → root `.env.example` (singurul valid)
- [x] Update `infra/env.example` cu un comentariu `# DEPRECATED: vezi ../.env.example`
  sau șterge complet și actualizează referințele
- [x] Verifică `docker-compose.yml` să citească din `.env` la root
- **Acceptance:** un singur fișier `.env.example` în repo, complet și aliniat
  cu secțiunea „Environment variables" din ARCHITECTURE.md
- **Done:** commit `a4745cf`

#### 2.1.2 Logging structurat (structlog) ✅
- [x] `pip install structlog` — adaugă în `backend/requirements.txt`
- [x] Creează `backend/app/logging.py`:
  ```python
  import structlog, logging, sys
  def configure(env: str):
      processors = [
          structlog.contextvars.merge_contextvars,
          structlog.processors.TimeStamper(fmt="iso"),
          structlog.processors.add_log_level,
      ]
      if env == "development":
          processors.append(structlog.dev.ConsoleRenderer())
      else:
          processors.append(structlog.processors.JSONRenderer())
      structlog.configure(processors=processors)
  log = structlog.get_logger()
  ```
- [x] Apel `configure(settings.ENVIRONMENT)` în `backend/app/main.py` startup
- [x] Înlocuiește toate `import logging; logger = logging.getLogger(__name__)`
  cu `from app.logging import log`
- [x] Înlocuiește `logger.info("user X did Y")` cu `log.info("event_name", **kwargs)` (vezi CONVENTIONS.md §2.4)
- **Acceptance:** Railway logs în production sunt JSON parseable. Local sunt human-readable.
- **Done:** commit `7b95b7a`

#### 2.1.3 Sentry integration ✅
- [x] Cont Sentry, project pentru backend, project pentru frontend
- [x] `pip install sentry-sdk[fastapi]` → adaugă în `backend/requirements.txt`
- [x] Init în `backend/app/main.py`:
  ```python
  if settings.ENVIRONMENT in ("staging", "production"):
      sentry_sdk.init(
          dsn=settings.SENTRY_DSN_BACKEND,
          environment=settings.ENVIRONMENT,
          traces_sample_rate=0.1,
          before_send=lambda event, hint: None if event.get("response", {}).get("status_code", 500) < 500 else event,
      )
  ```
- [x] `npm i @sentry/nextjs && npx @sentry/wizard@latest -i nextjs` în `frontend/`
- [x] Env vars: `SENTRY_DSN_BACKEND`, `NEXT_PUBLIC_SENTRY_DSN`
- [x] Throw test error pe ambele, verifică ajunge în Sentry
- **Acceptance:** un error pe `/api/me` (forțat) apare în Sentry backend cu
  user_id atașat. Un error pe `/clients` (forțat) apare în Sentry frontend.
- **Done:** commits `16aa56c`, `b8576fc`, `33581e3`, `648eef5`, `65d8aad`, `f9c2968`, `e48a7ca`
- **Note:** validat manual în prod 2026-05-05 — erori vizibile pe ambele proiecte
  Sentry. Pentru Next.js 14, init e via `components/sentry-init.tsx` (client
  component în RootLayout), nu via `instrumentation-client.ts` (Next.js 15 only).
  `NEXT_PUBLIC_SENTRY_DSN` adăugat ca build ARG în `Dockerfile.prod` (NEXT_PUBLIC
  vars sunt baked in la build time).

#### 2.1.4 CI/CD (GitHub Actions) ✅
- [x] Creează `.github/workflows/ci.yml` cu:
  ```yaml
  name: CI
  on:
    pull_request:
    push:
      branches: [main]
  jobs:
    backend:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with: { python-version: "3.12" }
        - run: pip install -r backend/requirements.txt -r backend/requirements-dev.txt
        - run: cd backend && ruff check .
        - run: cd backend && ruff format --check .
        - run: cd backend && pytest -v
    frontend:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-node@v4
          with: { node-version: "20" }
        - run: cd frontend && npm ci
        - run: cd frontend && npm run lint
        - run: cd frontend && npx tsc --noEmit
        - run: cd frontend && npm run build
  ```
- [x] Creează `backend/requirements-dev.txt` cu `pytest`, `pytest-asyncio`, `httpx`, `ruff`
- [x] Creează `backend/pyproject.toml` cu config ruff (line-length 100, target py312)
- **Acceptance:** un PR cu eroare de lint sau test eșuat e blocat la merge.
- **Done:** `.github/workflows/ci.yml`, `backend/requirements-dev.txt`, `backend/pyproject.toml`

#### 2.1.5 Test infrastructure backend ✅
- [x] Creează `backend/tests/conftest.py` cu fixture-urile din CONVENTIONS.md §2.7
- [x] Creează `backend/tests/test_smoke.py` cu un test minim:
  ```python
  def test_health(client):
      r = client.get("/health")
      assert r.status_code == 200
  ```
- [x] Creează `backend/tests/test_auth.py` cu mock JWKS și test pe `_user_has_kit_access`
  (direct kit, prin bundle, fără sub, sub expirat)
- **Acceptance:** `pytest -v` rulează 10+ teste, toate trec în CI.
- **Done:** commit `cbfe535` — 14 teste actuale (12 auth + 2 smoke)

---

### 2.2 Stripe integration

#### 2.2.1 Setup Stripe Dashboard
- [ ] Cont Stripe (test mode), activează Stripe Tax — configurează TVA RO 19%
- [ ] Creează 6 Products: Kit Internal Fiscal, Kit Digital Recurring, Kit Tax
  Residency, Kit Affiliate Compliance, Kit Affiliate Identification, Bundle Toate 5
- [ ] Creează 12 Prices în RON:
  - 5 kit-uri × monthly 99 RON + yearly 990 RON = 10
  - 1 bundle × monthly 349 RON + yearly 3490 RON = 2
- [ ] Tax behavior: **exclusive** (preț afișat fără TVA)
- [ ] Notează cele 12 Price IDs (vor fi seed-uite în DB)
- **Acceptance:** Stripe Dashboard arată 6 products + 12 prices în RON cu Tax activ.

#### 2.2.2 Migrație: seed Stripe price IDs și FGO fields
- [ ] Migration `0006_stripe_price_ids_and_fgo.py`:
  - UPDATE `products` cu `stripe_price_id_monthly` și `stripe_price_id_yearly`
    pentru cele 6 produse (folosește `op.execute(text(...))`)
  - ALTER `invoices` ADD COLUMN `fgo_invoice_number VARCHAR(50)`
  - ALTER `invoices` ADD COLUMN `fgo_invoice_link VARCHAR(500)`
  - ALTER `invoices` ADD COLUMN `fgo_emitted_at TIMESTAMPTZ`
- [ ] Test: `alembic upgrade head` local rulează fără erori
- **Acceptance:** după migrație, `SELECT * FROM products` arată price IDs reale.

#### 2.2.3 `stripe_client.py`
- [ ] `pip install stripe` → adaugă în requirements.txt
- [ ] Creează `backend/app/stripe_client.py`:
  ```python
  import stripe
  from app.config import settings
  stripe.api_key = settings.STRIPE_SECRET_KEY

  def create_checkout_session(*, user, product, billing_cycle: str, success_url: str, cancel_url: str):
      price_id = product.stripe_price_id_monthly if billing_cycle == "monthly" else product.stripe_price_id_yearly
      return stripe.checkout.Session.create(
          mode="subscription",
          line_items=[{"price": price_id, "quantity": 1}],
          customer_email=user.email,
          client_reference_id=str(user.id),
          success_url=success_url,
          cancel_url=cancel_url,
          automatic_tax={"enabled": True},
          subscription_data={"metadata": {"user_id": str(user.id), "product_code": product.code}},
      )

  def create_portal_session(*, stripe_customer_id: str, return_url: str):
      return stripe.billing_portal.Session.create(customer=stripe_customer_id, return_url=return_url)
  ```
- **Acceptance:** unit test cu Stripe Mock returnează un URL valid.

#### 2.2.4 Endpoint-uri payment
- [ ] `GET /api/products` (public, dar arată status sub. dacă auth):
  - Listează toate `Product` active cu prețuri și flag `subscribed: bool`
- [ ] `POST /api/checkout/session` (auth):
  - Body: `{product_code: str, billing_cycle: "monthly"|"yearly"}`
  - Returnează: `{url: str}` (URL Stripe Checkout)
- [ ] `POST /api/billing/portal` (auth):
  - Folosește `subscription.stripe_customer_id` din DB
  - Returnează: `{url: str}` (URL Stripe Customer Portal)
- [ ] `GET /api/me` (auth):
  - Returnează: `{user, subscriptions: [...], roles, has_admin_access}`
- **Acceptance:** apel manual cu curl + JWT real returnează 200 + URL Stripe valid.

#### 2.2.5 Webhook Stripe
- [ ] Creează `backend/app/webhooks/stripe.py` cu pattern-ul din CONVENTIONS.md §2.6
- [ ] Handlers:
  - `checkout.session.completed` → upsert Subscription cu status='active', period dates
  - `customer.subscription.updated` → update status, period_end, cancel_at_period_end
  - `customer.subscription.deleted` → status='canceled'
  - `invoice.payment_succeeded` → INSERT Invoice + apel FGO (vezi 2.3) + apel Sentry breadcrumb
  - `invoice.payment_failed` → UPDATE Subscription.status='past_due' + email user
- [ ] Înregistrare router în `backend/app/main.py`
- [ ] Configurare endpoint în Stripe Dashboard webhook (test mode)
- **Acceptance:** `stripe trigger checkout.session.completed` creează Subscription
  în DB. Replay același event nu duplică (idempotency).

#### 2.2.6 Subscription expiration enforcement
- [ ] Update `_user_has_kit_access` în `backend/app/auth.py`:
  - Adaugă filtru `Subscription.current_period_end > func.now()`
- [ ] Test: user cu sub `status='active'` dar `current_period_end < now()` → access negat (402)
- **Acceptance:** test în `test_kit_access.py` validează scenariul.

---

### 2.3 FGO integration

#### 2.3.1 Setup cont FGO API
- [ ] În FGO → Setări → Utilizatori → creează **Utilizator API**
- [ ] Notează **Cheia Privată** generată (singură dată afișată)
- [ ] Notează **Seria facturii** dorită (ex. `RM`)
- [ ] Adaugă env vars în Railway: `FGO_CUI`, `FGO_PRIVATE_KEY`, `FGO_SERIE`, `FGO_API_URL`
- **Acceptance:** test manual cu curl la `https://api-testuat.fgo.ro/v1/nomenclator/tva` returnează 200.

#### 2.3.2 `fgo_client.py`
- [ ] Creează `backend/app/fgo_client.py` conform exemplului din ARCHITECTURE.md
  („FGO API — detalii integrare")
- [ ] Funcții: `emite_factura()`, `inregistreaza_plata()`, `storneaza_factura()`
- [ ] Handle FGO errors: log la Sentry, raise custom `FGOError` cu detalii
- [ ] Retry logic: 3 încercări cu exponential backoff pentru network errors (httpx Retry)
- **Acceptance:** unit test cu `httpx.MockTransport` simulează 200 și 500 din FGO.

#### 2.3.3 Trigger FGO din webhook Stripe
- [ ] În handler `invoice.payment_succeeded`:
  1. Insert/update local `Invoice` cu date Stripe
  2. Construiește payload FGO din invoice + user data
  3. Apel `emite_factura(...)` → primești numar factură FGO
  4. Apel `inregistreaza_plata(numar, serie, suma, data)`
  5. UPDATE local `invoices` cu `fgo_invoice_number`, `fgo_invoice_link`, `fgo_emitted_at`
  6. Log success cu structlog
- [ ] Edge case: user.full_name lipsă → folosește `user.email` ca denumire client
  (logează warning)
- [ ] Edge case: FGO eșuează → marchează `webhook_events.error`, raise 500
  (Stripe va retry; după 3 retry-uri rămâne în logs pentru intervenție manuală)
- **Acceptance:** test E2E manual: `stripe trigger invoice.payment_succeeded`
  → 30 secunde mai târziu, factură vizibilă în FGO Dashboard.

---

### 2.4 GDPR foundations

#### 2.4.1 Data export
- [ ] `GET /api/me/data-export` (auth):
  - Construiește dict cu toate datele user-ului (vezi ARCHITECTURE.md secțiunea GDPR)
  - Returnează `StreamingResponse` cu `application/zip`
  - Conține: `user.json`, `clients.json`, `submissions.json`, `results.json`,
    `subscriptions.json`, `invoices.json`
- **Acceptance:** test manual: `curl -H "Authorization: Bearer ..." .../data-export -o export.zip`
  conține fișierele așteptate.

#### 2.4.2 Account deletion
- [ ] `DELETE /api/me/account` (auth):
  1. Cancel toate Subscription active în Stripe (`stripe.Subscription.delete(...)`)
  2. Soft-delete `User` (`deleted_at = now()`)
  3. Soft-delete toate `Client` ai user-ului (`deleted_at = now()`)
  4. Trimite email confirmare ștergere
- [ ] Frontend: pagină `/account` cu buton „Șterge cont" + confirmation modal
  (post Sprint 2.5)
- **Acceptance:** test manual: user creat → DELETE → user.deleted_at != NULL,
  toate subs Stripe canceled, login ulterior eșuează.

#### 2.4.3 Retention scrub
- [ ] Script `backend/scripts/scrub_pii.py`:
  - WHERE `webhook_events.received_at < now() - interval '90 days'` → `payload = '{}'`
  - WHERE `users.deleted_at < now() - interval '30 days'` → scrub email + full_name
- [ ] Configurare Railway Cron (sau alternativ: endpoint protejat + apel manual lunar)
- **Acceptance:** rulare manuală pe staging cu data fictivă confirmă scrub.

---

### 2.5 Frontend — pricing + checkout (minimal, modern în Sprint 2.5)

> În Sprint 2 punem doar funcționalitatea minimă cu CSS-ul existent. Polish-ul
> visual vine în Sprint 2.5 când migrăm la Tailwind + shadcn/ui.

- [ ] `app/pricing/page.tsx`:
  - Listează produsele din `/api/products`
  - Toggle Lunar/Anual (state local)
  - Buton „Abonează-te" → POST `/api/checkout/session` → `window.location = url`
- [ ] `app/checkout/success/page.tsx` cu polling `/api/me` pentru subscription nouă
- [ ] `app/checkout/canceled/page.tsx` simplu
- [ ] `app/account/billing/page.tsx`:
  - Listă subscriptions active (din `/api/me`)
  - Buton „Manage" → POST `/api/billing/portal` → redirect
- [ ] Update `lib/api.ts` cu suport pentru error responses noi (cod, message, detail)
- [ ] Pe pagina kit fără acces (response 402): afișează block CTA spre `/pricing`
- **Acceptance:** flow complet manual: signup → /pricing → Subscribe → Stripe →
  return → access kit → cancel din Portal → access păstrat până la period_end.

---

### Sprint 2 — QA Test Plan

- [ ] **T1**: Signup nou → `/pricing` → Subscribe Kit 1 99 RON → Stripe Checkout
  (card 4242 4242 4242 4242) → return → kit accesibil
- [ ] **T2**: Verifică în FGO Dashboard că factura a fost emisă în maxim 30s
- [ ] **T3**: Hit `GET /api/clients/X/kits/{kit_neaboned}` → 402 cu detail.code='kit_subscription_required'
- [ ] **T4**: Hit `GET /api/clients/Y` (Y aparține altui user) → 404
- [ ] **T5**: Cancel din Stripe Portal → status='cancel_at_period_end' → access păstrat
- [ ] **T6**: `stripe trigger customer.subscription.deleted` → status='canceled' → 402
- [ ] **T7**: Cumpăr bundle → toate 5 kit-uri accesibile
- [ ] **T8**: Replay `checkout.session.completed` 3× → un singur Subscription, o singură factură FGO
- [ ] **T9**: Force error în handler → ajunge în Sentry cu user_id
- [ ] **T10**: `GET /api/me/data-export` → zip valid cu toate datele
- [ ] **T11**: `DELETE /api/me/account` → toate subs Stripe canceled, user soft-deleted
- [ ] **T12**: CI rulează pe PR și blochează merge la lint/test failure
- [ ] Merge `feat/sprint-2-payments` în main, deploy Railway, smoke test production

---

## Sprint 2.5 — Frontend Modernization (NOU, ÎNAINTE DE LANDING)

**Goal:** Migrare frontend la stack modern (Tailwind + shadcn/ui + TanStack Query
+ react-hook-form + sonner). Adăugare error/loading boundaries. Token caching.

**Definition of Done:** App-ul folosește integral noul stack. Toate paginile
existente migrate. Lighthouse Accessibility > 90, Performance > 80.

**Branch:** `feat/sprint-2.5-frontend-modernization`

### 2.5.1 Setup stack modern
- [ ] `npm i tailwindcss@latest @tailwindcss/postcss postcss`
- [ ] `npx tailwindcss init`
- [ ] Configurare `tailwind.config.ts` cu paleta din logo (vezi ARCHITECTURE.md):
  - charcoal `#3D3D3D`, red `#CC2525`, blue `#2B5FC0`, green `#2E7D32`
  - bg `#F5F7FA`, white
- [ ] `npx shadcn@latest init` cu opțiuni: Default style, Slate base color, CSS vars
- [ ] Install componente: `button card dialog dropdown-menu form input label select toast badge skeleton tabs alert`
- [ ] `npm i @tanstack/react-query react-hook-form @hookform/resolvers zod sonner lucide-react`
- [ ] `npm i -D @types/node`
- **Acceptance:** `npm run build` succeed, paginile actuale încă funcționează (chiar dacă mixed CSS).

### 2.5.2 Refactor `lib/api.ts`
- [ ] Implementare `useApi()` hook cu `ApiError` class (vezi CONVENTIONS.md §3.2)
- [ ] Nu mai pasezi `token` ca parametru — vine implicit din `useAuth()`
- [ ] `cache: "no-store"` eliminat — TanStack Query gestionează caching
- **Acceptance:** o pagină refactorată folosește hook-ul nou și are typing complet.

### 2.5.3 Setup TanStack Query + Providers
- [ ] Creează `frontend/components/providers.tsx`:
  ```tsx
  "use client";
  export function Providers({ children }) {
    const [qc] = useState(() => new QueryClient({ defaultOptions: { queries: { staleTime: 30_000 }}}));
    return (
      <QueryClientProvider client={qc}>
        {children}
        <Toaster richColors />
      </QueryClientProvider>
    );
  }
  ```
- [ ] Wrap în `app/layout.tsx` între `ClerkProvider` și `children`
- **Acceptance:** ReactQueryDevtools vizibile în dev.

### 2.5.4 Hooks per resursă
- [ ] `hooks/useClients.ts`, `hooks/useClient.ts`, `hooks/useCreateClient.ts`,
  `hooks/useDeleteClient.ts`
- [ ] `hooks/useKits.ts`, `hooks/useKitSubmission.ts`, `hooks/useSaveKit.ts`
- [ ] `hooks/useProducts.ts`, `hooks/useMe.ts`, `hooks/useCheckout.ts`
- [ ] `hooks/useAdminUsers.ts`, `hooks/useAdminGrant.ts`
- **Acceptance:** toate paginile folosesc hooks, zero `useState + useEffect + apiGet`.

### 2.5.5 Error & loading boundaries
- [ ] `app/error.tsx` — global error boundary cu retry
- [ ] `app/loading.tsx` — global loading
- [ ] `app/not-found.tsx` — 404 page
- [ ] Per route: `app/clients/error.tsx`, `app/clients/loading.tsx`, etc.
- [ ] Component shared `<ErrorState error={error} onRetry={...} />`
- **Acceptance:** forțat un endpoint 500 → vede error.tsx, refresh → încarcă.

### 2.5.6 Refactor pagini
**Pentru fiecare pagină, migrare incrementală:**
- [ ] `/clients` (lista) — folosește `useClients` + skeleton
- [ ] `/clients/[id]` — folosește `useClient` + form react-hook-form pentru profil
- [ ] `/clients/[id]/kits/[kitCode]` — folosește `useKitSubmission` + form
- [ ] `/admin` și sub-paginile
- [ ] `/pricing`, `/checkout/*`, `/account/*` (din Sprint 2)
- [ ] `/onboarding`, `/sign-in`, `/sign-up` (cosmetic)
- [ ] Înlocuire toate butoanele/forme cu shadcn/ui components

### 2.5.7 Layout, navigation, theme
- [ ] Refactor `TopNav.tsx` cu shadcn/ui Sheet pentru mobile
- [ ] Logo placeholder în nav (text + culorile din logo, până avem SVG)
- [ ] Sidebar pe desktop pentru paginile complexe (kit completion)
- [ ] Sticky footer pe mobile cu CTA principal pe pricing
- **Acceptance:** Lighthouse mobile + desktop > 90 Accessibility.

### Sprint 2.5 — QA
- [ ] Toate paginile funcționează ca în Sprint 2 (zero regresii funcționale)
- [ ] Token nu se mai refetch la fiecare page navigation
- [ ] Erori afișate cu toast (success/error), nu alert browser
- [ ] Skeleton loading pe toate listările
- [ ] Mobile responsive pe iPhone 12 și Galaxy S21
- [ ] Lighthouse: Performance > 80, Accessibility > 90, Best Practices > 90
- [ ] Merge `feat/sprint-2.5-frontend-modernization`

---

## Sprint 3 — Landing site

**Goal:** `riskmatrixai.ro` are site de prezentare profesional cu pricing RON,
blog SEO, butoane login/register către `app.riskmatrixai.ro`.

**Definition of Done:** Site live, Lighthouse >90 mobile+desktop, 3 articole
blog publicate, DNS corect, monitorizare basic.

**Branch:** `feat/sprint-3-landing`

### 3.1 Setup
- [ ] Folder `landing/` în repo
- [ ] `cd landing && npm create astro@latest . -- --template minimal --typescript strict --install --no-git`
- [ ] `npx astro add tailwind react cloudflare sitemap mdx`
- [ ] Configurare `astro.config.mjs` cu integrations + site URL `https://riskmatrixai.ro`
- [ ] Branch protection: deploy preview pe Cloudflare Pages la fiecare PR

### 3.2 Identitate vizuală
- [ ] Importă logo-ul în `landing/public/logo.png` (fișierul primit de la Lucian)
- [ ] Generează variante SVG dacă posibil (sau folosim PNG cu alt-text proper)
- [ ] `landing/src/styles/global.css` cu design tokens:
  - Culori din logo: charcoal, red, blue, green, white, gray-light
- [ ] Google Fonts: Plus Jakarta Sans (heading) + Inter (body)
- [ ] Favicon multi-size din logo

### 3.3 Componente pagină principală
- [ ] `Header.astro` — logo + nav (Blog, Prețuri) + CTA Intră în cont / Creează cont
- [ ] `Hero.astro` — headline + subhead + screenshot mockup
- [ ] `Features.astro` — 3 carduri problemă→soluție
- [ ] `HowItWorks.astro` — 3 pași
- [ ] `Kits.astro` — 5 kit-uri
- [ ] `Pricing.astro` — toggle React, 6 carduri RON
- [ ] `FAQ.astro` — accordion 6 întrebări
- [ ] `CTAFinal.astro`
- [ ] `Footer.astro`

### 3.4 Blog
- [ ] Setup `landing/src/content/blog/` cu schema Astro
- [ ] `landing/src/pages/blog/index.astro` — listing
- [ ] `landing/src/pages/blog/[slug].astro` — detaliu
- [ ] 3 articole MDX inițiale (vezi titlurile din ARCHITECTURE.md)
- [ ] Sitemap auto-generat
- [ ] OG image per articol

### 3.5 Deploy
- [ ] Cloudflare Pages connect la repo, root: `landing/`
- [ ] DNS: `riskmatrixai.ro` → Pages, `app.riskmatrixai.ro` → Railway
- [ ] Update `CORS_ORIGINS` cu noile domenii
- [ ] Update `NEXT_PUBLIC_API_URL` la `https://api.riskmatrixai.ro`

### Sprint 3 — QA
- [ ] Lighthouse > 90 toate categorii
- [ ] Sitemap accesibil, indexare Google declanșată
- [ ] Toate CTA-urile către `app.riskmatrixai.ro` corect
- [ ] Mobile + desktop responsive
- [ ] Merge `feat/sprint-3-landing`

---

## Sprint 4 — Email transactional

**Goal:** Resend integrat, 5 template-uri funcționale, triggere automate.

**Branch:** `feat/sprint-4-emails`

### 4.1 Setup
- [ ] Cont Resend, verifică sending domain `riskmatrixai.ro` (SPF, DKIM, DMARC)
- [ ] Migration `0007_add_email_sends.py`: tabel `email_sends` cu dedup index
- [ ] `pip install resend`

### 4.2 Templates (React Email în `frontend/emails/`)
- [ ] `welcome.tsx` — post `user.created`, link la `/pricing`
- [ ] `subscription-started.tsx` — confirmare abonament cu data renew
- [ ] `payment-failed.tsx` — link Stripe Portal
- [ ] `subscription-canceled.tsx` — acces până la period_end
- [ ] `subscription-ended.tsx` — link reabonare

### 4.3 Triggers
- [ ] În `webhooks/clerk.py`: `user.created` → trimite welcome
- [ ] În `webhooks/stripe.py`: triggere pentru fiecare event relevant
- [ ] Idempotency prin `email_sends.dedupe_index`

### Sprint 4 — QA
- [ ] mail-tester.com score > 9/10 pe fiecare template
- [ ] Render corect în Gmail, Outlook, Apple Mail
- [ ] Merge `feat/sprint-4-emails`

---

## Sprint 5 — Launch readiness

**Branch:** `feat/sprint-5-launch`

### 5.1 Analytics
- [ ] PostHog în landing și app
- [ ] Cookie banner cu opt-in
- [ ] Funnel signup → first_client → first_kit → paid

### 5.2 Legal pages (pe landing)
- [ ] `/legal/privacy` — Privacy Policy (RO + EN)
- [ ] `/legal/terms` — Terms of Service
- [ ] `/legal/cookies` — Cookie Policy

### 5.3 Performance & Security
- [ ] Rate limiting backend (slowapi sau equivalent)
- [ ] Load test cu k6: ~100 useri concurenți pe `/api/kits`
- [ ] Security review checklist (vezi ARCHITECTURE.md)

### 5.4 Production cutover
- [ ] Stripe live mode keys (înlocuiește test în Railway)
- [ ] FGO production URL (`https://api.fgo.ro/v1`)
- [ ] Webhook endpoint Stripe production înregistrat
- [ ] Backup Postgres Daily activat
- [ ] Smoke test complet end-to-end cu card real

### Sprint 5 — QA Launch checklist
- [ ] Toate sprint-urile anterioare DoD bifat
- [ ] Sentry alerts configurate
- [ ] Monitorizare Railway cu alerte
- [ ] Documentația finală în README.md actualizată
- [ ] Merge `feat/sprint-5-launch`
- [ ] **GO LIVE**

---

## v2 Backlog (după launch + 5–10 plătitori)

### High impact
- [ ] Plan Agency multi-seat (Clerk Organizations)
- [ ] Google SSO (toggle în Clerk)
- [ ] Export CSV/Excel pentru clients și submissions
- [ ] Bulk client import (CSV upload)

### Medium impact
- [ ] PDF customization (logo, header, semnătură)
- [ ] Articole blog noi (2/lună pentru SEO)
- [ ] In-app notifications

### Low impact
- [ ] Public API + tokens
- [ ] AI-assisted kit completion

---

## Out of scope

- ❌ Real-time collaboration
- ❌ End-user kit creation
- ❌ Mobile native apps
- ❌ Marketplace third-party kits
- ❌ Mai multe limbi (rămâne RO only)

---

## Cum folosești acest backlog

1. Citește **CONVENTIONS.md** înainte de primul commit pe sprint
2. Lucrează în ordine: Sprint 2 → 2.5 → 3 → 4 → 5
3. Tick item-urile pe măsură ce le faci. Commit BACKLOG.md modificat la final de zi
4. Definition of Done e contractul. Nu marca sprint complet fără QA passed
5. Item-uri noi descoperite → adaugă la sprint curent (dacă blocant) sau v2
