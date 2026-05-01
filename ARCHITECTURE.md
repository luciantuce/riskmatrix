# Architecture — Kit Platform V3

Document de decizii arhitecturale pentru tranziția platformei din „internal
admin tool" în B2B SaaS pentru contabili și consultanți fiscali.

> Ultima actualizare: 2026-04-30
> Status: implementare incrementală (RBAC live, subscriptions gating pending)

---

## Context

### Stare curentă (deployed)

- FastAPI backend + Next.js 14 frontend pe Railway, regiune EU West Amsterdam
- Postgres pe Railway (același cluster regional, Private Networking cu backend)
- 5 kit-uri de compliance seedate în DB cu prețuri one-time (€45–55 fiecare)
- `/admin/*` protejat prin RBAC (`admin` / `super_admin`) pe JWT Clerk
- Fără concept de end-user; entitățile `Client` sunt gestionate direct prin UI
- Fără integrare de plată
- Fără email transactional

### Stare țintă (după 4 sprint-uri)

- B2B SaaS pentru contabili/consultanți din România (extensibil EU-wide)
- **Pricing per produs**: fiecare kit are abonament individual (€19/mo sau €190/an
  cu „2 luni free"), iar bundle-ul (toate 5) are abonament la €69/mo sau €690/an.
  User-ul poate combina: e.g. abonament la 2 kit-uri individuale, sau bundle, sau
  3 kit-uri + un bundle (deși bundle-ul include automat tot).
- **Cancel anytime**, fără commitment minim. Dacă contabilul vrea o lună, plătește
  o lună și gata. Pierde acces la sfârșit de perioadă.
- Fără trial — modelul cancel-anytime pe €19 e oricum „un fel de trial plătit"
  cu friction minimă. Simplifică schema (fără trial_end, fără cron pentru
  „trial_will_end", fără edge-case `unpaid` after trial).
- Fiecare user își deține portofoliul de `Client`-uri și submissions
- Auth via Clerk, payment via Stripe, email via Resend
- Factura fiscală RO (SmartBill) și plan Agency multi-seat: **lăsate pentru v2**

---

## Decizii de stack tehnologic

### Identitate & Auth: Clerk

- Drop-in pentru Next.js cu `@clerk/nextjs`
- Acoperă: signup, login, email verification, password reset, sessions, MFA,
  Organizations (pentru Agency în v2)
- Free tier: 10.000 MAU, apoi ~$0.02/MAU
- **Trade-off**: dependență de un vendor extern. Migrarea la self-hosted
  (Auth.js + FastAPI Users) e amânată până când factura Clerk depășește
  ~$50/lună sau apare un feature pe care nu-l acoperă.

### Plăți & abonamente: Stripe

- **Stripe Checkout** (hosted) pentru subscription signup
- **Stripe Customer Portal** pentru self-service (cancel, change plan,
  update card, view invoices)
- **Stripe Tax** pentru calcul automat VAT EU (B2B reverse charge cu
  VAT ID valid prin VIES)
- **Trade-off**: Stripe nu generează facturi fiscale conforme cu
  legislația RO. Integrarea SmartBill e amânată pentru v2.

### Database: Postgres (Railway-managed)

- Deja configurat în `europe-west4-drams3a`
- Alembic pentru migrații versionate
- Adăugiri de schemă pentru users, subscriptions, invoices, webhook_events

### Email transactional: Resend

- DX mai bun decât SES, cost mai mic decât Postmark la volum mic
- Free tier: 3.000 emails/lună, apoi $20/mo pentru 50k
- React Email pentru templates (TSX-based, share design tokens cu frontend)

### Hosting: Railway (neschimbat)

- Backend, Frontend, Postgres în `europe-west4-drams3a`
- Auto-deploy din branch-ul `main`
- Plan Hobby + usage-based billing

### Observability: Sentry (Sprint 4)

- Free tier suficient pentru early stage
- Integrare backend (`sentry-sdk[fastapi]`) și frontend (`@sentry/nextjs`)

### Analytics: PostHog (Sprint 4)

- Free tier 1M events/lună
- Funnel critic: signup → first_client → first_kit → trial_started → paid

---

## Domain model

### Existing (neschimbat ca structură, dar primește `user_id`)

- `Kit` — produs de compliance (5 seedate)
- `KitVersion`, `KitSection`, `KitQuestion`, `KitQuestionOption`, `KitRule` —
  arborele de definiție al unui kit
- `KitDocumentTemplate` — template PDF per kit version
  - Decizie implementată (2026-05-01): randarea PDF folosește fonturi Unicode
    (fallback DejaVuSans/Arial) pentru diacritice RO și wrap automat pe rânduri
    lungi, ca să evităm caractere corupte și overflow vizual.
- `Client` — o firmă evaluată (devine user-scoped)
- `ClientProfile` — date generale de firmă
- `KitSubmission` — răspunsuri pentru o pereche `(client, kit)`
- `KitResult` — output calculat al unui submission

### Nou (Sprint 1 + 2)

```sql
-- Sprint 1
users (
  id BIGSERIAL PRIMARY KEY,
  clerk_user_id VARCHAR UNIQUE NOT NULL,
  email VARCHAR NOT NULL,
  full_name VARCHAR,
  role VARCHAR NOT NULL DEFAULT 'client',   -- 'client' | 'admin' | 'super_admin'
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ
);

webhook_events (
  id BIGSERIAL PRIMARY KEY,
  source VARCHAR NOT NULL,                  -- 'clerk' | 'stripe'
  external_id VARCHAR NOT NULL,             -- evt_xxx
  event_type VARCHAR NOT NULL,
  payload JSONB NOT NULL,
  processed_at TIMESTAMPTZ,
  error TEXT,
  received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX idx_webhook_events_external
  ON webhook_events(source, external_id);

-- Sprint 2
products (
  id BIGSERIAL PRIMARY KEY,
  code VARCHAR UNIQUE NOT NULL,             -- 'kit_internal_fiscal' | 'bundle_all' | etc.
  name VARCHAR NOT NULL,
  type VARCHAR NOT NULL,                    -- 'kit' | 'bundle'
  kit_id BIGINT REFERENCES kits(id),        -- non-NULL only when type='kit'
  stripe_price_id_monthly VARCHAR NOT NULL,
  stripe_price_id_yearly VARCHAR NOT NULL,
  display_order INT NOT NULL DEFAULT 100,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT product_kit_consistency CHECK (
    (type = 'kit' AND kit_id IS NOT NULL) OR
    (type = 'bundle' AND kit_id IS NULL)
  )
);
CREATE UNIQUE INDEX idx_products_kit_id ON products(kit_id) WHERE kit_id IS NOT NULL;

bundle_includes (
  bundle_product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  kit_id BIGINT NOT NULL REFERENCES kits(id) ON DELETE CASCADE,
  PRIMARY KEY (bundle_product_id, kit_id)
);
-- Pentru launch, un singur bundle (toate 5). Schema permite multiple bundle-uri
-- în viitor (e.g. „Bundle Fiscal" cu 2 kit-uri, „Bundle Avansat" cu 4 etc.).

subscriptions (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id),
  product_id BIGINT NOT NULL REFERENCES products(id),
  stripe_subscription_id VARCHAR UNIQUE NOT NULL,
  stripe_customer_id VARCHAR NOT NULL,
  status VARCHAR NOT NULL,                  -- 'active' | 'past_due' | 'canceled' | 'unpaid'
  billing_cycle VARCHAR NOT NULL,           -- 'monthly' | 'yearly'
  current_period_start TIMESTAMPTZ NOT NULL,
  current_period_end TIMESTAMPTZ NOT NULL,
  cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
  canceled_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
-- Un user poate avea N subscriptions simultan (un row per produs cumpărat).
-- Dacă cumpără bundle peste kit-uri individuale, e responsabilitatea
-- frontendului să-i sugereze să cancel-eze duplicatele.

invoices (
  id BIGSERIAL PRIMARY KEY,
  subscription_id BIGINT REFERENCES subscriptions(id),
  user_id BIGINT NOT NULL REFERENCES users(id),
  stripe_invoice_id VARCHAR UNIQUE NOT NULL,
  amount_cents INT NOT NULL,
  currency CHAR(3) NOT NULL DEFAULT 'EUR',
  status VARCHAR NOT NULL,                  -- 'paid' | 'open' | 'void' | 'uncollectible'
  hosted_invoice_url VARCHAR,
  pdf_url VARCHAR,
  paid_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Sprint 3
email_sends (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id),
  template_code VARCHAR NOT NULL,           -- 'trial_ending_soon' | etc.
  context_jsonb JSONB,                      -- payload pentru template
  resend_message_id VARCHAR,
  status VARCHAR NOT NULL,                  -- 'queued' | 'sent' | 'failed'
  sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX idx_email_sends_dedupe
  ON email_sends(user_id, template_code, (context_jsonb->>'subscription_id'));
```

### Modificări pe tabelele existente (Sprint 1)

```sql
ALTER TABLE clients
  ADD COLUMN user_id BIGINT REFERENCES users(id),
  ADD COLUMN deleted_at TIMESTAMPTZ;
CREATE INDEX idx_clients_user_id ON clients(user_id);

ALTER TABLE kit_submissions
  ADD COLUMN user_id BIGINT REFERENCES users(id);
CREATE INDEX idx_kit_submissions_user_id ON kit_submissions(user_id);

ALTER TABLE kit_results
  ADD COLUMN user_id BIGINT REFERENCES users(id);
CREATE INDEX idx_kit_results_user_id ON kit_results(user_id);
```

Migration sequence: NULLABLE → backfill → SET NOT NULL (în două migrații
separate, ca să fie sigur).

---

## Auth flow

### Frontend (Next.js)

1. User accesează `/sign-up` (componentă Clerk)
2. Email + password → Clerk trimite email de verificare
3. User dă click pe link → revine la `/sign-up/verify-email`
4. Logged in, JWT emis, salvat în cookie `__session`
5. Redirect la `/onboarding`

### Backend — verificare JWT

1. Frontend trimite cu `Authorization: Bearer <jwt>` (din `getToken()` Clerk)
2. Middleware FastAPI extrage JWT, fetch JWKS Clerk (cache 1h), verifică
   semnătura (RS256)
3. Payload `sub` = `clerk_user_id`. Lookup în tabela `users`.
4. Dacă lipsește (lag webhook), creare lazy din claims-urile JWT. Log warning.
5. Inject `User` în request, continuă.

### RBAC (implementat 2026-04-30)

- `client`: acces la flow-ul propriu (clients/profile/kits pentru user-ul lui)
- `admin`: acces la zona `Super Contabil` (editare kituri)
- `super_admin`: tot ce are `admin` + poate acorda/revoca roluri

Enforcement:

- Frontend:
  - link-ul `Super Contabil` este vizibil doar pentru `admin` și `super_admin`
  - paginile `/admin/*` verifică rolul și fac redirect pentru userii non-admin
- Backend:
  - endpoint-urile `/api/admin/kits/*` cer rol `admin` sau `super_admin`
  - endpoint-ul `PUT /api/admin/users/{user_id}/role` cere `super_admin`
  - safeguard: ultimul `super_admin` nu poate fi demovat

Endpoint-uri admin relevante:

- `GET /api/me` — returnează rolul userului curent
- `GET /api/admin/users` — listă useri pentru ecranul de management
- `PUT /api/admin/users/{user_id}/role` — schimbare rol (`super_admin` only)

### Sync utilizatori prin Clerk webhook

- Endpoint: `POST /api/webhooks/clerk`
- Verifică semnătura Svix folosind `CLERK_WEBHOOK_SECRET`
- Idempotent: dedup prin `webhook_events.external_id`
- Handlers:
  - `user.created` → INSERT user
  - `user.updated` → UPDATE email, full_name
  - `user.deleted` → soft-delete user, cancel subscription Stripe (dacă există)

---

## Subscription flow

### Pricing (launch)

| Produs               | Lunar | Anual (-2 luni) |
|----------------------|-------|-----------------|
| Kit individual (×5)  | €19   | €190            |
| Bundle (toate 5)     | €69   | €690            |

Logica:
- Toate 5 kit-uri individuale = €95/mo. Bundle €69/mo = save €26/mo (-27%).
  Bundle devine atractiv pentru cine folosește 4+ kit-uri.
- Anual = 10× lunar (efectiv -17%, comunicat ca „2 luni gratis").
- În Stripe avem **12 prices total**: 5 kit-uri × 2 (monthly/yearly) +
  1 bundle × 2 = 12.

### Flow signup → cumpărare

1. User signup → Clerk → email verification → logged in
2. Webhook Clerk `user.created` → INSERT `users`
3. Aterizează pe `/dashboard`. Are 0 abonamente → vede empty state cu CTA
   „Vezi catalog → /pricing"
4. Pe `/pricing`: 6 carduri (5 kit-uri + bundle), toggle Monthly/Yearly,
   buton „Subscribe" pe fiecare
5. Click „Subscribe" pe kit X → POST `/api/checkout/session` cu
   `{product_code: 'kit_internal_fiscal', billing_cycle: 'monthly'}` →
   răspuns cu URL Stripe Checkout → redirect
6. Stripe Checkout: card → success → redirect la `/checkout/success?session_id=...`
7. Frontend polling `/api/me` până apare nouă subscription (max 30s)
8. Webhook `checkout.session.completed` (în paralel) → INSERT subscription cu
   `status='active'`, `current_period_end = now() + 1 month` (sau 1 year)
9. User are acces la kit-ul cumpărat. Poate cumpăra mai multe (al doilea, etc.)
   sau poate face upgrade la bundle prin Stripe Customer Portal.

### Cancel flow

1. User în `/account/billing` → click „Manage" pe un abonament → Stripe Customer
   Portal
2. Click „Cancel subscription" → Stripe marchează `cancel_at_period_end=true`
3. Webhook `customer.subscription.updated` → UPDATE local `cancel_at_period_end=true`
4. User păstrează acces până la `current_period_end`
5. La final de perioadă, Stripe trimite `customer.subscription.deleted` →
   UPDATE `status='canceled'` → user pierde acces la kit-ul respectiv

### Authorization gate (target design for subscriptions)

```python
# app/auth.py

def current_user(authorization: str = Header(...)) -> User:
    """Verifică JWT-ul Clerk, returnează User din DB (lazy create dacă nu există)."""


def user_kit_access(db: Session, user_id: int, kit_id: int) -> Subscription | None:
    """
    Returnează subscription-ul activ care îi dă user-ului acces la kit-ul X.
    Acces direct (subscription pe kit) sau prin bundle.
    """
    return db.query(Subscription).join(Product).filter(
        Subscription.user_id == user_id,
        Subscription.status == 'active',
        # fie e subscription pe kit-ul direct...
        ((Product.type == 'kit') & (Product.kit_id == kit_id)) |
        # ...fie e bundle care include kit-ul
        ((Product.type == 'bundle') & Product.id.in_(
            db.query(BundleInclude.bundle_product_id)
              .filter(BundleInclude.kit_id == kit_id)
        )),
    ).first()


def require_kit_access(
    kit_code: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> tuple[User, Kit, Subscription]:
    """Dependency pentru endpoint-uri care manipulează un kit specific."""
    kit = db.query(Kit).filter(Kit.code == kit_code).first()
    if not kit:
        raise HTTPException(404, "Kit not found")
    sub = user_kit_access(db, user.id, kit.id)
    if not sub:
        raise HTTPException(
            status_code=402,  # Payment Required
            detail={
                "code": "kit_subscription_required",
                "kit_code": kit_code,
                "upgrade_url": f"/pricing?focus={kit_code}",
            },
        )
    return user, kit, sub
```

Reguli (target):
- Endpoint-uri **read** publice (`GET /api/kits` listing) folosesc doar `current_user`
- Endpoint-uri pe **un kit specific** (`GET /api/clients/{id}/kits/{code}`,
  `PUT`, `GET .../pdf`) folosesc `require_kit_access` — verifică user owns kit
- `POST /api/clients` folosește doar `current_user` (orice user logged-in poate
  crea Client; ce kit-uri folosește pentru el e gate-uit separat)

### Status implementare (2026-04-30)

Implementat:
- Auth Clerk + user scoping pe `/api/clients/*`
- RBAC admin (`client` / `admin` / `super_admin`) pe `/api/admin/*`
- UI admin ascuns pentru non-admin + management roluri

Neimplementat încă (subscriptions gating):
- Tabelele `products`, `bundle_includes`, `subscriptions`, `invoices`
- Webhook-urile Stripe (`/api/webhooks/stripe`)
- Filtrarea `/api/kits` la kituri cumpărate
- Guard `require_kit_access` pe endpoint-urile de kit

Plan agreat pentru implementare:
1. Migrații Alembic pentru `products`, `bundle_includes`, `subscriptions`, `invoices`
2. Seed catalog produse (5 kituri + 1 bundle)
3. Funcție backend `user_kit_access(user_id, kit_id)` (direct kit sau bundle)
4. Filtrare `GET /api/kits` după accesul userului
5. Guard pe `GET/PUT /api/clients/{id}/kits/{kit_code}` + `result/pdf`
6. Integrare Stripe webhook pentru sincronizare subscriptions
7. UI: afișare doar kituri cumpărate (sau lock + CTA upgrade)

### Fără quota

În modelul vechi (Starter/Pro tiers) aveam `max_clients`. În modelul
per-kit-subscription nu mai e nevoie: toate planurile sunt unlimited pe clienți.
Diferența e ce KIT-URI poate folosi user-ul, nu CÂȚI clienți poate avea.

Asta simplifică: nu mai e nevoie de `enforce_client_quota`, downgrade-handling,
read-only fallback, etc.

---

## Webhook handlers

### Stripe events tratate

| Event                                  | Acțiune                                          |
|----------------------------------------|--------------------------------------------------|
| `checkout.session.completed`           | Creează subscription dacă nu există              |
| `customer.subscription.created`        | Idempotent upsert                                |
| `customer.subscription.updated`        | Update status, periods, cancel_at_period_end     |
| `customer.subscription.deleted`        | Marchează `status='canceled'`                    |
| `invoice.payment_succeeded`            | Insert/update invoice                            |
| `invoice.payment_failed`               | `status='past_due'`, trimite email               |

(Eliminat `customer.subscription.trial_will_end` — nu mai avem trial.)

**Identificare produs din webhook**: la `checkout.session.completed`, payload-ul
conține `subscription.items.data[0].price.id`. Folosim `stripe_price_id` ca să
găsim produsul în DB (matchuim împotriva `products.stripe_price_id_monthly` SAU
`stripe_price_id_yearly`). Setăm `billing_cycle` în consecință.

### Idempotency

Toate handler-ele verifică `webhook_events.external_id`. Dacă event deja
procesat, return 200 fără re-procesare.

### Order independence

`checkout.session.completed` și `customer.subscription.created` pot ajunge
în orice ordine. Ambele declanșează un upsert pe `stripe_subscription_id`.
Handler-ul cu mai multe date câștigă (sau merge).

### Failure handling

Dacă handler raise → return 500 → Stripe retry cu exponential backoff timp
de 3 zile. Eroarea logată în `webhook_events.error` pentru inspectare manuală.

---

## Email transactional (Resend)

### Templates (React Email, în `frontend/emails/`)

- `welcome.tsx` — după `user.created` Clerk
- `subscription-started.tsx` — la primul `checkout.session.completed`
  (cu numele kit-ului/bundle-ului cumpărat)
- `payment-failed.tsx` — imediat + ziua 3 + ziua 7
- `subscription-canceled.tsx` — când user-ul cancel-ează (acces până la period_end)
- `subscription-ended.tsx` — când perioada se termină și user-ul pierde acces

### Triggers

- **Webhook-driven** (instant):
  - `checkout.session.completed` → email „subscription started"
  - `invoice.payment_failed` → email „payment failed"
  - `customer.subscription.deleted` → email „access ended"
- **Cron-driven**: niciunul în launch (fără trial = fără email-uri scheduled).
  Adaugi „renewal coming up" email în v2 dacă conversia anuală cere

---

## Riscuri & gotcha-uri

### 1. Webhook race conditions

`checkout.session.completed` și `customer.subscription.created` pot ajunge
în orice ordine. Handler-ele tale TREBUIE să fie idempotent, cu upsert pe
`stripe_subscription_id`. Test: rulează `stripe trigger checkout.session.completed`
și verifică că nu sunt duplicate inserts.

### 2. Clerk JWT înainte de webhook sync

Primul request după signup poate ajunge înainte ca webhook-ul `user.created`
să fie procesat. Soluție: lazy-create User în `current_user` dacă nu există în
DB. Log warning pentru a monitoriza frecvența — dacă crește, înseamnă că
webhook-urile au lag mare.

### 3. User cu subscriptions duplicate (kit + bundle)

Cazul: user-ul are abonament la 3 kit-uri individuale (€57/mo total), apoi
cumpără și bundle-ul (€69/mo) crezând că face upgrade. Acum plătește €126/mo
pentru ce putea avea cu €69. Nu e bug funcțional (accesul lui la kit-urile
respective rămâne valid), dar e overcharge.

Mitigare în launch:
- Pe `/pricing`, dacă user-ul are deja subscription pe un kit individual,
  butonul „Subscribe to bundle" arată un warning: „Ai deja kit X — cancel-ează
  înainte ca să eviți plata dublă."
- Pe `/account/billing`, sortez subscription-urile și marchez vizibil
  duplicate-le (kit individual + bundle care îl include).
- v2: buton „Upgrade to bundle" care face automat cancel + create cu proration.

### 4. Migrarea schemei pe DB cu date

În acest moment DB-ul are doar kit-urile seedate (zero clienți reali).
Migration-ul e safe. Dacă până la Sprint 1 apar date dummy: creezi user
„founder" cu `clerk_user_id` placeholder, asignezi totul lui, înlocuiești
când îți creezi cont real.

### 5. VAT EU

Activează **Stripe Tax** din dashboard. Sediu business: România → VAT default
19% RO. EU B2B cu VAT ID valid în VIES → reverse charge automat (no VAT). Peste
€10k vânzări EU/an → trebuie facturat VAT-ul țării destinație (Stripe gestionează
automat). Configurare: ~10 minute în Stripe dashboard.

### 6. Factura fiscală RO

Facturile generate de Stripe NU sunt conforme cu legislația RO (lipsesc serie,
CIF, etc.). Pentru clienți B2B care cer factură cu CIF: gestionezi manual până
la integrarea SmartBill din v2.

### 7. Cancellation grace period

Când user-ul cancel-ează un abonament: `cancel_at_period_end=true` până la
`current_period_end`. Are acces până atunci. Webhook
`customer.subscription.deleted` se declanșează când perioada se termină →
marchezi `status='canceled'`, blochezi accesul la kit-ul respectiv.

Dacă user-ul cancel-ează bundle-ul dar are și kit-uri individuale active,
păstrează acces doar la cele individuale. Dependența între produse e gestionată
automat de helper-ul `user_kit_access` care verifică active subs.

### 8. Failed payment recovery

Stripe încearcă automat să recupereze plata pe parcursul a 3 săptămâni
(retry policy configurabil în Stripe Dashboard). Pe parcurs:
- Status devine `past_due` → user-ul pierde acces imediat (gate-ul e strict)
- 3 email-uri de la noi (zilele 0, 3, 7)
- Dacă user-ul update-ează card-ul → următoarea încercare reușește → `active`
- După ~3 săpt fără succes → Stripe trimite `customer.subscription.deleted`
  → `status='canceled'`, sfârșit

Politica „pierde acces imediat la past_due" e mai strictă decât industria;
multe SaaS dau grace period 3-7 zile pe `past_due` ca să nu enerveze user-ii.
Pentru launch e ok strict (mai puțin cod), îmbunătățești în v2 dacă apar
plângeri.

---

## Future expansion

### v2 (după launch + 5–10 plătitori)

- **Plan Agency** multi-seat: Clerk Organizations + plan cu seat limit
- **Factură fiscală RO**: SmartBill API în webhook `invoice.payment_succeeded`
- **Google SSO**: toggle în Clerk dashboard
- **Export CSV/Excel** pentru clients și submissions

### v3 (când product traction justifică)

- **PDF storage pe Cloudflare R2** cu retention policy (audit trail legal)
- **Audit log** pentru acțiuni `/admin`
- **Public API + tokens** pentru integrare CRM-uri contabili
- **AI-assisted kit completion**: sugerează răspunsuri pe baza profilului firmei

### Out of scope — nu construim

Considerate explicit și amânate. Reevaluare doar dacă user research schimbă imaginea.

- Real-time collaboration pe kit fills
- End-user kit creation (kit-urile rămân admin-managed)
- Mobile native apps (web suficient pentru contabili)
- Marketplace pentru kit-uri third-party

---

## Environment variables

### Backend (`/backend`)

```bash
# Deja configurat (Railway)
ENVIRONMENT=production
DATABASE_URL=${{Postgres.DATABASE_URL}}
PORT=8010
CORS_ORIGINS=https://ideal-generosity-production-b637.up.railway.app
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<rotated, schimbat din placeholder>
SEED_ON_STARTUP=false

# De adăugat (Sprint 1)
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_WEBHOOK_SECRET=whsec_...
CLERK_JWKS_URL=https://<your-app>.clerk.accounts.dev/.well-known/jwks.json

# De adăugat (Sprint 2)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# De adăugat (Sprint 3)
RESEND_API_KEY=re_...
EMAIL_FROM="Kit Platform <noreply@yourdomain.com>"
APP_URL=https://app.yourdomain.com
```

### Frontend (`/frontend`)

```bash
# Deja configurat
NEXT_PUBLIC_API_URL=https://riskmatrix-production.up.railway.app
PORT=3010

# De adăugat (Sprint 1)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/onboarding

# De adăugat (Sprint 2)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

---

## API contract

### Endpoint-uri noi

#### Sprint 1
- `POST /api/webhooks/clerk` — receiver webhook Clerk

#### Sprint 2
- `POST /api/webhooks/stripe` — receiver webhook Stripe
- `GET /api/me` — current user + lista produselor cumpărate (cu status, period_end)
- `GET /api/products` — catalog public: 5 kit-uri + bundle, cu prețuri
- `POST /api/checkout/session` — creează Stripe Checkout session pentru un product_code + billing_cycle
- `POST /api/billing/portal` — creează Stripe Customer Portal session

### Modificări pe endpoint-urile existente

Toate `/api/clients/*` și `/api/clients/{id}/kits/*`:
- Acum cer `Authorization: Bearer <clerk_jwt>`
- Filtrate prin `user_id`
- Gating pe subscription activ: **pending** (vezi planul de mai sus)

`/api/admin/*`: deja pe Clerk role-based (`admin`/`super_admin`), Basic Auth eliminat.

---

## Structura fișierelor (după Sprint 1–3)

```
backend/app/
  auth.py                 # NOU — Clerk JWT verification, dependencies
  webhooks/
    __init__.py
    clerk.py              # NOU (Sprint 1) — Clerk event handlers
    stripe.py             # NOU (Sprint 2) — Stripe event handlers
  email/
    __init__.py
    client.py             # NOU (Sprint 3) — Resend wrapper
  models.py               # MODIFIED — User, Product, BundleInclude, Subscription, Invoice, WebhookEvent
  config.py               # MODIFIED — Clerk + Stripe + Resend env vars
  schemas.py              # MODIFIED — UserResponse, SubscriptionResponse, etc.
main.py                   # MODIFIED — register webhook routers, dependencies pe rutele existente

frontend/
  middleware.ts           # NOU (Sprint 1) — Clerk authMiddleware
  app/
    sign-in/[[...sign-in]]/page.tsx   # NOU (Sprint 1)
    sign-up/[[...sign-up]]/page.tsx   # NOU (Sprint 1)
    onboarding/page.tsx               # NOU (Sprint 1) — post-signup
    pricing/page.tsx                  # NOU (Sprint 2) — comparare planuri
    checkout/success/page.tsx         # NOU (Sprint 2)
    checkout/canceled/page.tsx        # NOU (Sprint 2)
    account/
      page.tsx                        # NOU (Sprint 3) — Clerk UserProfile
      billing/page.tsx                # NOU (Sprint 3) — Stripe Portal embed
  emails/
    welcome.tsx                       # NOU (Sprint 3)
    trial-ending-soon.tsx             # NOU (Sprint 3)
    trial-converted.tsx               # NOU (Sprint 3)
    payment-failed.tsx                # NOU (Sprint 3)
    subscription-canceled.tsx         # NOU (Sprint 3)
  lib/
    api.ts                # MODIFIED — atașează Clerk JWT pe toate fetch-urile
    clerk.ts              # NOU (Sprint 1)
    stripe.ts             # NOU (Sprint 2)
```

---

## Branch & deploy strategy

- Fiecare sprint pe branch separat: `feat/auth-foundation`, `feat/subscriptions`,
  `feat/billing-portal`, `feat/launch-polish`
- Merge în `main` doar după ce toate item-urile din DoD sunt bifate
- Railway auto-deploy din `main`. Pentru staging environment separat: creezi
  un environment Railway nou („staging") pe branch-ul de feature, testezi
  acolo înainte să merge

---

## Referințe

- Clerk docs: https://clerk.com/docs
- Stripe Subscription docs: https://docs.stripe.com/billing/subscriptions/overview
- Stripe Tax: https://docs.stripe.com/tax
- Resend docs: https://resend.com/docs
- React Email: https://react.email
- Railway docs: https://docs.railway.com
