# Architecture — Kit Platform V3

Document de decizii arhitecturale pentru tranziția platformei din „internal
admin tool" în B2B SaaS pentru contabili și consultanți fiscali.

> Ultima actualizare: 2026-04-28
> Status: planificare, înainte de Sprint 1

---

## Context

### Stare curentă (deployed)

- FastAPI backend + Next.js 14 frontend pe Railway, regiune EU West Amsterdam
- Postgres pe Railway (același cluster regional, Private Networking cu backend)
- 5 kit-uri de compliance seedate în DB cu prețuri one-time (€45–55 fiecare)
- `/admin/*` protejat cu HTTP Basic Auth (placeholder credentials)
- Fără concept de end-user; entitățile `Client` sunt gestionate direct prin UI
- Fără integrare de plată
- Fără email transactional

### Stare țintă (după 4 sprint-uri)

- B2B SaaS pentru contabili/consultanți din România (extensibil EU-wide)
- Pricing pe abonament: **Starter €29/mo** sau **Pro €69/mo** (-20% anual)
- Trial 14 zile pe Pro fără card up-front
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
  role VARCHAR NOT NULL DEFAULT 'user',     -- 'user' | 'admin'
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
plans (
  id BIGSERIAL PRIMARY KEY,
  code VARCHAR UNIQUE NOT NULL,             -- 'starter' | 'pro'
  name VARCHAR NOT NULL,
  stripe_price_id_monthly VARCHAR NOT NULL,
  stripe_price_id_yearly VARCHAR NOT NULL,
  max_clients INT,                          -- NULL = unlimited
  features_jsonb JSONB DEFAULT '{}',
  active BOOLEAN NOT NULL DEFAULT TRUE
);

subscriptions (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id),
  plan_id BIGINT NOT NULL REFERENCES plans(id),
  stripe_subscription_id VARCHAR UNIQUE NOT NULL,
  stripe_customer_id VARCHAR NOT NULL,
  status VARCHAR NOT NULL,                  -- 'trialing' | 'active' | 'past_due' | 'canceled' | 'unpaid'
  current_period_start TIMESTAMPTZ NOT NULL,
  current_period_end TIMESTAMPTZ NOT NULL,
  cancel_at_period_end BOOLEAN NOT NULL DEFAULT FALSE,
  trial_end TIMESTAMPTZ,
  canceled_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

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

| Plan    | Lunar | Anual  | Clienți | Kit-uri    | Trial   |
|---------|-------|--------|---------|------------|---------|
| Starter | €29   | €290   | 10      | unlimited  | -       |
| Pro     | €69   | €690   | unlimited | unlimited | 14 zile |

Anual = 10 luni plătite (-17% efectiv, comunicat ca „2 luni gratis").

### Flow trial → paid

1. User signup → row în `users` via Clerk webhook
2. Aterizează pe `/onboarding`, vede CTA „Start 14-day Pro trial"
3. Click → Stripe Checkout cu `subscription_data.trial_period_days=14`
   și `payment_method_collection='if_required'` (= fără card pentru trial)
4. Stripe Checkout redirect → `/checkout/success`
5. Webhook `checkout.session.completed` → INSERT subscription cu
   `status='trialing'`, `trial_end=session.subscription.trial_end`
6. User are acces Pro 14 zile, fără card on file
7. Ziua 11: email „Trial ending in 3 days, add card now"
8. Ziua 14: Stripe încearcă charge. Fără card → `status='unpaid'` → user
   blocat de la mutații (poate citi)
9. User dă click „Add card" → Stripe Customer Portal → adaugă card →
   următoarea încercare reușește → `status='active'`

### Authorization gate

```python
# app/auth.py

def current_user(authorization: str = Header(...)) -> User:
    """Verifică JWT-ul Clerk, returnează User din DB (lazy create dacă nu există)."""

def current_active_user(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> tuple[User, Subscription]:
    """Verifică JWT + subscription activ. Raise 402 dacă nu e abonat."""
    sub = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status.in_(['active', 'trialing']),
    ).first()
    if not sub:
        raise HTTPException(
            status_code=402,  # Payment Required
            detail={"code": "subscription_required", "upgrade_url": "/pricing"},
        )
    return user, sub
```

- Endpoint-uri **read** (`GET /api/clients`, `GET /api/kits`) folosesc `current_user`
- Endpoint-uri **mutație** (`POST`/`PUT`/`DELETE`/`GET .../pdf`) folosesc `current_active_user`

### Quota enforcement

```python
def enforce_client_quota(user, sub, db):
    if sub.plan.max_clients is None:
        return  # unlimited
    count = db.query(Client).filter(
        Client.user_id == user.id,
        Client.deleted_at.is_(None),
    ).count()
    if count >= sub.plan.max_clients:
        raise HTTPException(
            403,
            detail={
                "code": "client_limit_reached",
                "limit": sub.plan.max_clients,
                "current": count,
                "upgrade_url": "/account/billing",
            },
        )
```

Apelat doar în `POST /api/clients`. La downgrade (Pro → Starter), clienții
existenți rămân read-only — nu se șterge nimic. User-ul doar nu mai poate adăuga.

---

## Webhook handlers

### Stripe events tratate

| Event                                  | Acțiune                                          |
|----------------------------------------|--------------------------------------------------|
| `checkout.session.completed`           | Creează subscription dacă nu există              |
| `customer.subscription.created`        | Idempotent upsert                                |
| `customer.subscription.updated`        | Update status, periods, plan_id, cancel flag     |
| `customer.subscription.deleted`        | Marchează canceled                               |
| `invoice.payment_succeeded`            | Insert/update invoice                            |
| `invoice.payment_failed`               | `status='past_due'`, trimite email               |
| `customer.subscription.trial_will_end` | Email „trial ending in 3 days" (3 zile înainte)  |

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
- `trial-ending-soon.tsx` — 3 zile înainte de `trial_end`
- `trial-converted.tsx` — după primul charge reușit
- `payment-failed.tsx` — imediat + ziua 3 + ziua 7
- `subscription-canceled.tsx` — când user-ul cancel-ează (acces până la period_end)

### Triggers

- **Webhook-driven** (instant): `invoice.payment_failed` → email imediat
- **Cron-driven** (Railway scheduled service, o dată pe oră):
  găsește subscription-uri cu `trial_end` în 3 zile ±1h, trimite
  `trial_ending_soon` dacă nu e deja trimis (dedup în `email_sends`)

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

### 3. Trial fără card → expirare

Stripe va seta `status='unpaid'` după prima încercare eșuată de charge la
sfârșitul trialului. UI trebuie să afișeze clar acest status cu CTA pentru
adăugare card. Email-urile cu 3 zile înainte sunt critice.

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

Când user-ul cancel-ează: `cancel_at_period_end=true` până la
`current_period_end`. Are acces până atunci. Webhook
`customer.subscription.deleted` se declanșează când perioada se termină →
marchezi canceled, blochezi.

### 8. Downgrade cu over-limit

Pro 50 clienți → downgrade la Starter (limit 10): păstrezi toți clienții
read-only, blochezi crearea de clienți noi. NU ștergi date.

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
- `GET /api/me` — current user + active subscription + plan limits
- `POST /api/checkout/session` — creează Stripe Checkout session
- `POST /api/billing/portal` — creează Stripe Customer Portal session

### Modificări pe endpoint-urile existente

Toate `/api/clients/*` și `/api/clients/{id}/kits/*`:
- Acum cer `Authorization: Bearer <clerk_jwt>`
- Filtrate prin `user_id`
- Mutațiile sunt și gate-uite prin subscription activ

`/api/admin/*`: rămâne pe Basic Auth pentru ops. Migrare la Clerk
role-based în v2.

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
  models.py               # MODIFIED — User, Plan, Subscription, Invoice, WebhookEvent
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
