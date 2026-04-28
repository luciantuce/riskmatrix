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

## Sprint 2 — Subscriptions per produs (săpt. 2)

**Goal:** User-ii pot vedea catalogul (5 kit-uri + bundle), abona la oricare,
iar accesul la kit-uri e gate-uit prin subscription activ pe kit-ul respectiv
sau pe bundle-ul care îl include.

**Definition of Done:** Un user logged-in deschide `/pricing`, alege un kit la
€19/mo, completează Stripe Checkout cu card real (test mode), are imediat acces
la kit-ul respectiv și NU are acces la celelalte 4. Bundle-ul deblochează
automat toate 5.

### Setup Stripe
- [ ] Cont Stripe (test mode), activează Stripe Tax
- [ ] **Products** (6 total): unul per kit (5) + unul „Bundle (toate 5)"
- [ ] **Prices** (12 total): per fiecare product, monthly + yearly
  - 5 kit-uri × monthly €19 + yearly €190 = 10
  - 1 bundle × monthly €69 + yearly €690 = 2
- [ ] Setează business address (RO) și EU VAT settings
- [ ] Tax behavior: **exclusive** (recomandat — pricing afișat fără VAT,
      adăugat la checkout după țară/CIF)
- [ ] Notează cele 12 Price IDs pentru seed-ul DB
- [ ] Branch: `feat/subscriptions`

### Schema (Day 1)
- [ ] Migration `0004_add_subscription_tables.py`:
  - `CREATE TABLE products` (cu CHECK constraint pe `(type, kit_id)`)
  - `CREATE TABLE bundle_includes`
  - `CREATE TABLE subscriptions` (cu `product_id`, `billing_cycle`)
  - `CREATE TABLE invoices`
  - Index-uri conform `ARCHITECTURE.md`
  - **Seed inițial** în migrație:
    - 5 rânduri în `products` (type='kit', kit_id=...) — Price IDs din env
    - 1 rând în `products` (type='bundle')
    - 5 rânduri în `bundle_includes` legând bundle-ul de cele 5 kit-uri

### Backend (Day 2–4)
- [ ] `pip install stripe` → update requirements
- [ ] `backend/app/stripe_client.py` — wrapper (key din env, helpers)
- [ ] `backend/app/webhooks/stripe.py`:
  - `POST /api/webhooks/stripe`
  - Verifică webhook signature
  - Idempotent dedup via `webhook_events` (key: `("stripe", event.id)`)
  - Handlers pentru cele 6 events din `ARCHITECTURE.md`
        (NO trial_will_end — fără trial)
  - **Lookup product**: din `subscription.items.data[0].price.id` → match
        împotriva `products.stripe_price_id_monthly` SAU `_yearly`,
        setează `billing_cycle` corespunzător
- [ ] `backend/app/auth.py`: adaugă helper-ul `user_kit_access(db, user_id, kit_id)`
      și dependency `require_kit_access(kit_code: str)`
- [ ] Înlocuiește `current_user` cu `require_kit_access` pe endpoint-urile
      legate de un kit specific:
  - `GET /api/clients/{id}/kits/{code}`
  - `PUT /api/clients/{id}/kits/{code}`
  - `GET /api/clients/{id}/kits/{code}/pdf`
  - `GET /api/kits/{code}` — definiția kit-ului
- [ ] **Endpoint nou** `GET /api/products`:
  - Listează cele 6 produse cu prețuri (din DB) + dacă user-ul deja are
        subscription activ pe fiecare (pentru badge „Already subscribed" în UI)
- [ ] **Endpoint nou** `POST /api/checkout/session`:
  - Input: `{product_code, billing_cycle: 'monthly'|'yearly'}`
  - Lookup product → ia stripe_price_id corespunzător
  - Creează Stripe Checkout cu `mode='subscription'`, `line_items=[{price, quantity:1}]`
  - Setează `client_reference_id = user.id` (pentru idempotency în webhook)
  - Pre-fill `customer_email = user.email`
  - Return URL Checkout
- [ ] **Endpoint nou** `GET /api/me`:
  - Return user + lista subscriptions active (cu product info, period_end,
        cancel_at_period_end)
- [ ] **Endpoint nou** `POST /api/billing/portal` (mutat din Sprint 3 ca să fie
      disponibil de la primul deploy):
  - Stripe Customer Portal session pentru user-ul curent

### Frontend (Day 4–6)
- [ ] `app/pricing/page.tsx` (public, accesibil fără login dar prompt-ează la subscribe):
  - Header: titlu, subtitlu „Pay only for the kits you need"
  - Toggle Monthly/Yearly cu calculator „2 months free yearly"
  - **6 carduri**: 5 kit-uri (€19/mo each) + 1 bundle (€69/mo, evidențiat „BEST VALUE — save 27%")
  - Per card: nume, descriere scurtă, preț, buton „Subscribe" / „Already subscribed"
  - Click „Subscribe" pe kit/bundle → call `/api/checkout/session` → redirect Stripe
- [ ] `app/checkout/success/page.tsx`:
  - Polling `/api/me` la 2s interval până apare subscription nouă (max 30s)
  - Toast „Welcome! You now have access to {product.name}"
  - Redirect la dashboard sau direct la `/clients/X/kits/{code}` dacă e un singur kit cumpărat
- [ ] `app/checkout/canceled/page.tsx` — mesaj + link la pricing
- [ ] Component `<SubscriptionBanner>` în layout dashboard:
  - Dacă vreun subscription are `status='past_due'` → banner roșu „Payment failed, update card"
  - Dacă vreun subscription are `cancel_at_period_end=true` → banner galben „Access ends on {date}"
- [ ] Pe pagina kit-ului (când user n-are acces): full-page card „Subscription required"
      cu CTA spre `/pricing?focus={kit_code}`
- [ ] `app/account/billing/page.tsx`:
  - Listă subscriptions active (card per produs cu status, period_end, „Manage")
  - „Manage" → `/api/billing/portal` → redirect Stripe Portal
  - **Avertizare** dacă user are subscription la kit + bundle care îl include:
        „You're paying for both X and Bundle. Consider canceling X."

### QA (Day 6–7)
- [ ] **Test 1**: signup → onboarding → /pricing → click Subscribe pe Kit 1
      → Stripe Checkout cu 4242 4242 4242 4242 → return → subscription `active`
- [ ] **Test 2**: hit `GET /api/clients/1/kits/{code1}` cu acces → 200 OK
- [ ] **Test 3**: hit `GET /api/clients/1/kits/{code2}` fără acces (n-am cumpărat acel kit) → 402
- [ ] **Test 4**: cancel subscription din Stripe Portal → status `cancel_at_period_end=true`
      → user are acces până la `period_end`
- [ ] **Test 5**: simulez sfârșit de perioadă cu `stripe trigger customer.subscription.deleted`
      → status `canceled` → user pierde acces (gate-ul răspunde 402)
- [ ] **Test 6**: webhook idempotency — replay același event de 3 ori,
      verifică zero duplicate inserts
- [ ] **Test 7**: cumpăr bundle → verific că am acces la TOATE 5 kit-urile
- [ ] **Test 8**: am bundle ACTIV + cumpăr și kit individual → API răspunde
      cu warning în UI (nu blocant, doar avertizare)
- [ ] Verifică Stripe Tax: VAT 19% pentru RO B2C, reverse charge pentru EU B2B
      cu VAT ID valid
- [ ] Deploy pe Railway, configurează webhook endpoint în Stripe dashboard
      pointing la production (`/api/webhooks/stripe`)
- [ ] Smoke test în production cu card real (refund după)
- [ ] Merge `feat/subscriptions`

---

## Sprint 3 — Self-service billing + emails (săpt. 3)

**Goal:** User-ii își gestionează abonamentele fără să contacteze suport.
Evenimentele critice declanșează email-uri.

**Definition of Done:** User cancel-ează un subscription din Stripe Portal,
update-ează card, vede istoric facturi. Email-urile de subscription-started,
payment-failed și subscription-ended se trimit automat.

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
- [ ] Email triggers în `webhooks/stripe.py`:
  - `checkout.session.completed` → `subscription-started` email
  - `invoice.payment_failed` → `payment-failed` email immediate
  - `customer.subscription.deleted` → `subscription-ended` email
- [ ] Email trigger în `webhooks/clerk.py`:
  - `user.created` → `welcome` email
- [ ] Endpoint `POST /api/billing/portal` — gata din Sprint 2, doar verifici
- [ ] Cron pentru retry email-uri payment_failed (day 3, day 7) — opțional v1.5

### Email templates (Day 2–4) — în `frontend/emails/`
- [ ] `welcome.tsx` — bun-venit post-signup, link la /pricing
- [ ] `subscription-started.tsx` — confirmare la primul `checkout.session.completed`,
      include numele produsului cumpărat și data renew-ului
- [ ] `payment-failed.tsx` — versiune immediate / day 3 / day 7 (param)
- [ ] `subscription-canceled.tsx` — confirmare cancel, acces până la period_end
- [ ] `subscription-ended.tsx` — la `customer.subscription.deleted`, „access ended,
      resubscribe anytime"
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
- [ ] **Test 1**: cancel din portal → email `subscription-canceled` →
      la sfârșit de perioadă email `subscription-ended`
- [ ] **Test 2**: payment failed simulation → email `payment-failed` immediate
- [ ] **Test 3**: fiecare email template renderează corect în Gmail, Outlook,
      Apple Mail (folosește mail-tester.com)
- [ ] **Test 4**: deliverability — email-urile NU ajung în spam (verifică
      cu mail-tester score > 9/10)
- [ ] **Test 5**: idempotency — webhook events repetate nu generează email-uri duplicate
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
