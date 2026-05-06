# Session Status

Last updated: 2026-05-06 (Europe/Bucharest)

## Now
- **Sprint 2.1 Foundations — COMPLET** ✅ (toate 5 task-uri bifate în BACKLOG.md)
- Sentry activ în prod pe ambele proiecte, validat cu erori reale din browser și backend.
- GitHub Actions CI activ: pytest + ruff (BE) + tsc + build (FE) la fiecare push pe `main`.
- 15 teste backend trec (smoke + auth + subscription gating).
- ruff format aplicat pe tot backend-ul, `pyproject.toml` + `requirements-dev.txt` adăugate.

## Last Done (Sprint 2.1)
- `3769bf3` fix(ci): Clerk publishable key real în CI build (era pk_test_ci invalid)
- `b7b3e36` feat(ci): GitHub Actions CI + ruff format întreg backend
- `e48a7ca` chore(fe): expune window.Sentry pentru debug din browser console
- `f9c2968` fix(fe): SentryInit client component în RootLayout (Next.js 14 pattern)
- `65d8aad` fix(fe): NEXT_PUBLIC_SENTRY_DSN ca build ARG în Dockerfile.prod
- `648eef5` fix(fe): sentry.client/server.config.ts pentru Next.js 14
- `33581e3` fix(be): before_send Sentry reparat + log sentry_active=true la startup
- `cbfe535` test(be): infrastructură pytest 15 teste

## Deploy Status
- Backend (`riskmatrixai-be`): online, `sentry_active=true` la startup.
- Frontend (`riskmatrixai-fe`): online pe `riskmatrixai.ro`, Sentry client SDK activ în browser.
- CI: GitHub Actions rulează la fiecare push pe `main`.

## Next Steps (Sprint 2.2 Stripe)
1. **2.2.1** Setup Stripe Dashboard — produse + prețuri în RON, obține `price_id`-urile
2. **2.2.2** Migrație Alembic: `stripe_price_id` pe `Product`, `stripe_customer_id` pe `User`
3. **2.2.3** `backend/stripe_client.py` — wrapper SDK Stripe
4. **2.2.4** `POST /api/checkout/session` + `GET /api/products`
5. **2.2.5** `POST /api/webhooks/stripe` cu idempotency (pattern din CONVENTIONS.md §2.6)

## How To Resume (copy/paste in a new chat)
`Continuam din /docs/SESSION_STATUS.md. Sprint 2.1 Foundations e complet (Sentry validat + CI/CD GitHub Actions + 15 teste). Urmatorul task este Sprint 2.2 Stripe: setup dashboard RON, migratie Alembic stripe_price_id, stripe_client.py, endpoint checkout session si webhook cu idempotency.`
