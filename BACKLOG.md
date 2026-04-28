# Backlog — Kit Platform V3

Defalcare pe sprint-uri pentru tranziția în B2B SaaS pentru contabili.

> Vezi `ARCHITECTURE.md` pentru context, decizii și rationale.

Status legenda: `[ ]` pending, `[x]` done, `[~]` în lucru, `[!]` blocat.

---

## ✅ Sprint 0 — Deploy initial (DONE)

> Stack-ul live pe Railway în EU Amsterdam, înainte de adăugarea de auth.

- [x] Backend FastAPI deployat cu Dockerfile.prod
- [x] Frontend Next.js deployat cu Dockerfile.prod
- [x] Postgres provisionat și migrat în EU West Amsterdam
- [x] CORS_ORIGINS cross-linked frontend ↔ backend
- [x] Health check `/health` răspunde, `/api/kits` returnează cele 5 kit-uri
- [ ] **Hardening post-deploy** (în paralel cu Sprint 1):
  - [ ] Schimbă `ADMIN_PASSWORD` din placeholder (`openssl rand -base64 24`)
  - [ ] Pune `SEED_ON_STARTUP=false` (DB-ul e deja seedat)
  - [ ] Activează **Backups → Daily** pe Postgres
  - [ ] Test end-to-end ca user real: creează client, completează kit, generează PDF
  - [ ] (Optional) redenumește serviciile: `riskmatrix` → `backend`,
        `ideal-generosity` → `frontend`

---

## Sprint 1 — Auth foundation (săpt. 1)

**Goal:** Fiecare request e autentificat, fiecare resursă e user-scoped, signup-ul
funcționează end-to-end.

**Definition of Done:** Un user nou se înregistrează prin Clerk, vede dashboard-ul
gol, creează un client. Nu poate vedea clienții altui user. Toate cele 4 testele
QA de mai jos trec.

### Setup
- [ ] Cont Clerk (free tier), nume app: „Kit Platform"
- [ ] Configurare Clerk: email/password, email verification required, redirect URLs
- [ ] Adaugă Clerk env vars în Railway (backend + frontend) — vezi `ARCHITECTURE.md`
- [ ] Branch: `git checkout -b feat/auth-foundation`

### Schema (Day 1–2)
- [ ] Migration `0002_add_users_table.py`:
  - `CREATE TABLE users` (id, clerk_user_id UNIQUE, email, full_name, role, created_at, deleted_at)
  - `ALTER TABLE clients ADD COLUMN user_id NULLABLE` + FK
  - `ALTER TABLE clients ADD COLUMN deleted_at`
  - `ALTER TABLE kit_submissions ADD COLUMN user_id NULLABLE`
  - `ALTER TABLE kit_results ADD COLUMN user_id NULLABLE`
  - Index pe `user_id` pe toate trei
- [ ] `CREATE TABLE webhook_events` (în aceeași migrație)
- [ ] Backfill: dacă există clienți reali, creezi user „founder" cu placeholder
      `clerk_user_id`, atribui-i tot. Dacă DB e fresh (zero clienți), skip.
- [ ] Migration `0003_user_id_not_null.py`: `SET NOT NULL` pe user_id pe toate trei
- [ ] Rulează local cu `alembic upgrade head`, verifică

### Backend (Day 2–4)
- [ ] `pip install pyjwt[crypto] httpx svix` → update `backend/requirements.txt`
- [ ] `backend/app/auth.py`:
  - `_jwks_cache` cu TTL 1h
  - `verify_clerk_jwt(token: str) -> dict` (signature check + claims)
  - `current_user(authorization: str = Header(...)) -> User` (dependency,
    cu lazy create dacă lipsește din DB)
  - `_lazy_create_user_from_jwt(payload, db) -> User`
- [ ] `backend/app/webhooks/__init__.py` (router parent)
- [ ] `backend/app/webhooks/clerk.py`:
  - `POST /api/webhooks/clerk`
  - Verifică Svix signature folosind `CLERK_WEBHOOK_SECRET`
  - Dedup prin `webhook_events` (key: `("clerk", event.id)`)
  - Handlers: `user.created`, `user.updated`, `user.deleted`
- [ ] Update `backend/main.py` să includă webhook router
- [ ] Refactor pe toate `/api/clients/*` și `/api/clients/{id}/kits/*`:
  - Adaugă `user: User = Depends(current_user)` în signature
  - Filtre `Client.user_id == user.id` în query-uri
  - Setează `user_id=user.id` la creation
  - 404 (nu 403) pentru resurse ce aparțin altui user
- [ ] `_get_client` devine `_get_user_client(db, user_id, client_id)`
- [ ] `_get_kit` rămâne global (kit-urile sunt shared)
- [ ] Test local cu un JWT manual generat (Clerk dev tools)

### Frontend (Day 3–6)
- [ ] `cd frontend && npm i @clerk/nextjs @clerk/themes`
- [ ] `frontend/middleware.ts`:
  - `authMiddleware` cu publicRoutes: `["/", "/pricing", "/api/webhooks/(.*)"]`
- [ ] Wrap `app/layout.tsx` cu `<ClerkProvider>`
- [ ] Create `app/sign-in/[[...sign-in]]/page.tsx` cu `<SignIn />`
- [ ] Create `app/sign-up/[[...sign-up]]/page.tsx` cu `<SignUp />`
- [ ] Update `frontend/lib/api.ts` să atașeze `Authorization: Bearer ${token}`
      din `useAuth().getToken()` (client) sau `auth().getToken()` (server)
- [ ] Adaugă `<UserButton />` în header
- [ ] Create `app/onboarding/page.tsx` (post-signup landing)
- [ ] Update `app/page.tsx` (currently empty/redirect): landing public la `/`
- [ ] Update `app/clients/page.tsx`: empty state pentru first-time users cu
      CTA mare „Adaugă primul tău client"
- [ ] După create client → toast „Acum completează un kit pentru el" cu
      highlight pe primul rând

### QA (Day 6–7)
- [ ] **Test 1**: signup → email verification → logged in → empty dashboard ✓
- [ ] **Test 2**: user A creează client X, log out, signup ca user B,
      verifică că B nu vede clientul X în listă ✓
- [ ] **Test 3**: hit `GET /api/clients` fără Authorization header → 401 ✓
- [ ] **Test 4**: hit `GET /api/clients/X` cu JWT user B (X aparține user A) → 404 ✓
- [ ] Webhook test: șterge user din Clerk dashboard → soft-delete propagă în DB
- [ ] Deploy pe Railway, smoke tests pe URL-urile production
- [ ] Update `frontend/.env.example` și `backend/.env.example`
- [ ] Merge `feat/auth-foundation` → `main`

---

## Sprint 2 — Subscriptions (săpt. 2)

**Goal:** User-ii pot alege un plan, pornesc trial, sunt charge-uiți, iar accesul
e gate-uit prin subscription activ.

**Definition of Done:** Un user signup, alege Pro, completează Stripe Checkout
(fără card pentru trial), folosește app-ul. După trial, cu card adăugat, e
charge-uit €69 cu success.

### Setup
- [ ] Cont Stripe (test mode), activează Stripe Tax
- [ ] Stripe Products: „Kit Platform Starter", „Kit Platform Pro"
- [ ] Stripe Prices: 4 (Starter monthly €29, Starter yearly €290, Pro
      monthly €69, Pro yearly €690)
- [ ] Setează business address (RO) și EU VAT settings
- [ ] Tax behavior: exclusive (recomandat — pricing afișat fără VAT)
- [ ] Salvează Price IDs pentru env vars
- [ ] Branch: `feat/subscriptions`

### Schema (Day 1)
- [ ] Migration `0004_add_subscription_tables.py`:
  - `CREATE TABLE plans` cu seed inițial pentru starter și pro
        (cu stripe_price_ids din env)
  - `CREATE TABLE subscriptions`
  - `CREATE TABLE invoices`
  - Index-uri conform `ARCHITECTURE.md`

### Backend (Day 2–4)
- [ ] `pip install stripe` → update requirements
- [ ] `backend/app/stripe_client.py` wrapper (key from env, helper functions)
- [ ] `backend/app/webhooks/stripe.py`:
  - `POST /api/webhooks/stripe`
  - Verifică webhook signature
  - Idempotent dedup via `webhook_events` (key: `("stripe", event.id)`)
  - Handlers pentru cele 7 events din `ARCHITECTURE.md`
- [ ] `backend/app/auth.py`: adaugă `current_active_user`
- [ ] Înlocuiește `current_user` cu `current_active_user` pe endpoint-urile
      de mutație (`POST`/`PUT`/`DELETE`/`GET .../pdf`)
- [ ] `enforce_client_quota(user, sub, db)` helper
- [ ] Apel `enforce_client_quota` în `POST /api/clients`
- [ ] Endpoint nou `POST /api/checkout/session`:
  - Input: `{plan_code, billing_cycle: 'monthly'|'yearly'}`
  - Creează Stripe Checkout cu `subscription_data.trial_period_days=14`
        și `payment_method_collection='if_required'`
  - Return URL Checkout
- [ ] Endpoint nou `GET /api/me`:
  - Return user + active subscription + plan info + quota usage

### Frontend (Day 4–6)
- [ ] `app/pricing/page.tsx` (public):
  - Comparare side-by-side Starter vs Pro
  - Toggle Monthly/Yearly cu calculator de „save 17%"
  - CTA „Start free trial" → call `/api/checkout/session` → redirect Stripe
  - CTA pentru Starter: „Subscribe" (fără trial)
- [ ] `app/checkout/success/page.tsx`:
  - Polling `/api/me` la 2s interval până apare subscription (max 30s)
  - Apoi redirect la `/dashboard` cu toast „Welcome to Pro!"
- [ ] `app/checkout/canceled/page.tsx`:
  - Mesaj încurajator + link înapoi la pricing
- [ ] Component `<SubscriptionBanner>` în layout dashboard:
  - Afișare condiționată pentru `status='past_due'` sau `trial_end - now < 3d`
  - CTA pentru add card / upgrade
- [ ] Block UI pentru `status NOT IN ('active', 'trialing')`:
  - Endpoint-urile întorc 402 → frontend afișează full-page „Subscription required"

### QA (Day 6–7)
- [ ] **Test 1**: signup → onboarding → pricing → Stripe Checkout cu
      4242 4242 4242 4242 → return → subscription `trialing` ✓
- [ ] **Test 2**: Stripe test card 4000 0000 0000 0341 (decline pe charge)
      → după trial → status `past_due` ✓
- [ ] **Test 3**: hit `POST /api/clients` fără subscription → 402 ✓
- [ ] **Test 4**: webhook idempotency — replay același event de 3 ori,
      verifică zero duplicate inserts ✓
- [ ] **Test 5**: starter plan cu 10 clienți → 11th create → 403 cu mesaj
      de upgrade ✓
- [ ] Verifică Stripe Tax: VAT 19% pentru RO B2C, reverse charge pentru EU B2B
      cu VAT ID valid
- [ ] Deploy pe Railway, configurează webhook endpoint în Stripe dashboard
      pointing la production
- [ ] Smoke test în production cu card real (refund după)
- [ ] Merge `feat/subscriptions`

---

## Sprint 3 — Self-service billing + emails (săpt. 3)

**Goal:** User-ii își gestionează abonamentul fără să contacteze suport.
Evenimentele critice declanșează email-uri.

**Definition of Done:** User cancel-ează din app, schimbă plan, update card,
vede facturi. Email-urile trial-ending și payment-failed se trimit automat.

### Setup
- [ ] Cont Resend (free tier), verifică sending domain
- [ ] DNS records (SPF, DKIM, DMARC) pentru sending domain
- [ ] Branch: `feat/billing-portal`

### Schema (Day 1)
- [ ] Migration `0005_add_email_sends.py`:
  - `CREATE TABLE email_sends` conform `ARCHITECTURE.md`

### Backend (Day 1–3)
- [ ] `pip install resend` → update requirements
- [ ] `backend/app/email/client.py` — Resend wrapper cu rendering HTML
- [ ] `backend/app/email/templates.py` — mapping template_code → React Email render
- [ ] Endpoint `POST /api/billing/portal`:
  - Creează Stripe Customer Portal session pentru user-ul curent
  - Return portal URL
- [ ] Email triggers în `webhooks/stripe.py`:
  - `invoice.payment_failed` → email immediate
  - `customer.subscription.trial_will_end` → email
  - `customer.subscription.deleted` → email „canceled"
- [ ] Email trigger în `webhooks/clerk.py`:
  - `user.created` → welcome email
- [ ] Cron job (Railway scheduled service) — `cron/check_trials.py`:
  - Rulează la fiecare oră
  - Găsește subscription-uri cu `trial_end` în 3 zile ±1h
  - Trimite `trial_ending_soon` dacă nu e deja trimis (dedup în `email_sends`)

### Email templates (Day 2–4) — în `frontend/emails/`
- [ ] `welcome.tsx` — bun-venit, link la onboarding
- [ ] `trial-ending-soon.tsx` — 3 zile rămase, CTA add card
- [ ] `trial-converted.tsx` — first charge succeeded, thank you
- [ ] `payment-failed.tsx` — versiune immediate / day 3 / day 7 (param)
- [ ] `subscription-canceled.tsx` — confirmare cancel, acces până la period_end
- [ ] Toate cu logo, branding consistent, plain text fallback

### Frontend (Day 3–5)
- [ ] `app/account/page.tsx`:
  - Clerk `<UserProfile />` (handles email change, password, MFA, delete account)
- [ ] `app/account/billing/page.tsx`:
  - Card cu plan curent, status, next charge date, trial end (dacă aplicabil)
  - Lista facturilor (din `/api/me` extins, sau endpoint separat)
  - Buton „Manage subscription" → POST `/api/billing/portal` → redirect
- [ ] Polish global: loading states, error toasts (sonner), empty states

### QA (Day 5–7)
- [ ] **Test 1**: cancel din portal → status `cancel_at_period_end=true` →
      user păstrează acces până la `period_end` ✓
- [ ] **Test 2**: change plan din portal → proration calculat corect ✓
- [ ] **Test 3**: fiecare email template renderează corect în Gmail, Outlook,
      Apple Mail (folosește mail-tester.com)
- [ ] **Test 4**: trial-ending-soon se trimite EXACT o dată per subscription
      (chiar dacă cron rulează de 24x în 24h)
- [ ] **Test 5**: deliverability — email-urile NU ajung în spam (verifică
      cu mail-tester score > 9/10)
- [ ] Merge `feat/billing-portal`

---

## Sprint 4 — Polish + launch readiness (săpt. 4)

**Goal:** App-ul e production-ready: monitorizat, analyzed, performant, are
pagini de marketing.

**Definition of Done:** Toate item-urile pre-launch checklist sunt bifate.

### Observability
- [ ] Cont Sentry + project pentru backend
- [ ] Cont Sentry + project pentru frontend
- [ ] `pip install sentry-sdk[fastapi]` → init în `backend/main.py`
- [ ] `npm i @sentry/nextjs` → wizard `npx @sentry/wizard@latest -i nextjs`
- [ ] Throw test error pe ambele, verifică că ajunge în Sentry
- [ ] Configurare alerte Sentry (email pe new error, slack opțional)
- [ ] Source maps upload în CI pentru frontend

### Analytics
- [ ] Cont PostHog (cloud free tier)
- [ ] `npm i posthog-js` în frontend, init în `app/layout.tsx`
- [ ] Track events: `signup`, `plan_view`, `checkout_start`, `checkout_complete`,
      `client_created`, `kit_completed`, `pdf_generated`
- [ ] Configurare funnel în PostHog: signup → first_client → first_kit →
      trial_started → paid

### CI/CD
- [ ] `.github/workflows/ci.yml`:
  - On PR: backend `pytest`, frontend `npm run build`, type check `tsc`
  - On merge `main`: trigger Railway deploy (already auto, smoke test după)
- [ ] Pre-commit hooks (`.pre-commit-config.yaml`):
  - `ruff` pentru Python
  - `prettier` pentru TS/TSX

### Marketing
- [ ] `app/page.tsx` (landing) cu:
  - Hero: titlu, subtitlu, CTA „Start free trial"
  - Features: 3-4 carduri cu beneficii cheie
  - Screenshots din app (kit completion, PDF output)
  - Pricing CTA
  - FAQ scurt
  - Footer cu links Privacy / Terms
- [ ] Domain real înregistrat (`<numefirma>.ro` sau `.app`)
- [ ] Custom domain configurat în Railway:
  - `app.<domain>` → frontend
  - `api.<domain>` → backend
- [ ] DNS CNAME-uri la Cloudflare/Namecheap
- [ ] Update `NEXT_PUBLIC_API_URL` și `CORS_ORIGINS` la noile domenii
- [ ] SSL automat (Railway gestionează)

### Compliance
- [ ] `app/legal/privacy/page.tsx` — Privacy Policy (template adaptat,
      menționează Clerk, Stripe, Resend, PostHog ca processors)
- [ ] `app/legal/terms/page.tsx` — Terms of Service
- [ ] `app/legal/cookies/page.tsx` — Cookie Policy (PostHog setează cookies)
- [ ] Cookie banner (PostHog `posthog.opt_in_capturing()` cu user consent)
- [ ] GDPR: endpoint `GET /api/me/data-export` (zip cu toate datele user-ului)
- [ ] GDPR: account deletion (Clerk gestionează automat user.deleted webhook)

### Pre-launch checklist
- [ ] Stripe **live mode** keys (înlocuiește test keys în Railway)
- [ ] Verifică webhook endpoints în Stripe production (live mode separat de test)
- [ ] Resend domain warmed up (trimite ~10 emails test în zilele dinaintea launch-ului)
- [ ] Backup tested: restore Postgres backup pe staging
- [ ] Monitoring: Sentry alerts configurate, Railway alerts on service failures
- [ ] Load test: ~100 concurrent users pe `/api/kits` (k6 sau artillery)
- [ ] Security review:
  - SQL injection (SQLAlchemy parameterized — OK)
  - XSS (React escapes — OK; verifică `dangerouslySetInnerHTML`)
  - CSRF (Clerk session cookie — verifică SameSite)
  - Rate limiting pe endpoint-urile publice (`/api/webhooks/*` exempted)
- [ ] Smoke test entire flow în production cu card real

---

## v2 Backlog (după launch + 5–10 plătitori)

> Sortat după impact estimat. **NU începe v2 până nu ai validat market fit
> cu MVP-ul.**

### High impact
- [ ] **Factură fiscală RO** via SmartBill API
  - Webhook `invoice.payment_succeeded` → creează factură SmartBill
  - Email factură PDF ca atașament
  - Estimate: 3–5 zile
- [ ] **Plan Agency multi-seat**
  - Clerk Organizations integration
  - Plan tier cu seat limit (3 incluse, +€20/seat extra)
  - Invite flow prin email
  - Per-seat role (admin/member)
  - Estimate: 1 săptămână
- [ ] **Google SSO** — toggle în Clerk dashboard, test, ship. Estimate: 1 zi.

### Medium impact
- [ ] **Export CSV/Excel** pentru clients și submissions. 2 zile.
- [ ] **Bulk client import** (CSV upload cu column mapping). 3 zile.
- [ ] **Client tagging / segmentation** (filtre dashboard). 2 zile.
- [ ] **PDF customization**: logo, header text, signature line per user. 3 zile.

### Lower impact
- [ ] In-app notifications (trial ending, etc.). 2 zile.
- [ ] Help docs cu screenshots. Ongoing.
- [ ] Public API + tokens pentru integrare CRM-uri contabili. 1 săptămână.

---

## v3 Backlog (când product traction justifică)

- [ ] PDF storage pe Cloudflare R2 cu retention policy (audit trail legal)
- [ ] Audit log pentru acțiuni `/admin`
- [ ] Outbound webhook API pentru integrare CRM-uri
- [ ] AI-assisted kit completion (sugerează răspunsuri pe baza profilului firmei)
- [ ] Mobile native apps (DOAR dacă user research indică nevoia clar)

---

## Out of scope — NU construim

Considerate explicit și amânate indefinit. Reevaluare doar dacă user research
schimbă imaginea.

- ❌ Real-time collaboration pe kit fills
- ❌ End-user kit creation (kit-urile rămân admin-managed)
- ❌ Mobile native apps (web e suficient pentru contabili)
- ❌ Marketplace third-party kits

---

## Cum folosești acest backlog

1. **Lucrează în ordine sprint-urilor.** Nu sări la Sprint 3 înainte să
   termini Sprint 1.
2. **Tick item-urile pe măsură ce le faci.** `[ ]` → `[~]` (în lucru) →
   `[x]` (done). Commit acest fișier la fiecare sfârșit de zi.
3. **Definition of Done e contractul.** Nu marca un sprint complet dacă
   nu trec toate testele QA.
4. **Item-uri noi descoperite** se adaugă la sprint-ul curent dacă sunt
   blocante, sau la v2 dacă pot aștepta.
5. **Time estimates sunt orientative.** Sprint 1 poate dura 5–10 zile în
   funcție de cât de mult time alocat. Nu te grăbi să rupi calitatea.
