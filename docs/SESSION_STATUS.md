# Session Status

Last updated: 2026-05-05 15:48 (Europe/Bucharest)

## Now
- Infrastructura de teste backend (Sprint 2.1.5) a fost adaugata (`tests/conftest.py`, `tests/test_smoke.py`, `tests/test_auth.py`).
- Blocker local: Python 3.9.6 nu poate importa backend-ul (foloseste type hints 3.10+ `str | None`); rularea `pytest -v` cere Python 3.12 conform conventiilor.
- Domeniul `riskmatrixai.ro` este activ prin Cloudflare + Railway custom domain.
- Restricția IP a fost eliminată din Railway (`ALLOWED_IPS` șters pe `riskmatrixai-be` și `riskmatrixai-fe`).
- Admin users are modal „thickbox” pentru grant manual pe 1+ kituri, cu auto-bundle.
- Profil client: canale comunicare extinse cu câmpuri dedicate + validări.
- Ștergere client disponibilă (soft delete) din listă și din pagina clientului.
- UX listă clienți: buton `Sterge` mutat lângă `Deschide client`.
- Validare creare client: blocat nume gol (frontend + backend).

## Last Done
- `merge(main)` Integrat branch `feat/sprint-2/unify-env` in `main` si push (`4e2e5c9`).
- `deploy(railway)` FE + BE ruleaza in production pe commit `4e2e5c9` (Sentry FE+BE inclus).
- `feat(frontend)` Integrare Sentry Next.js (instrumentation server/client, global error handler App Router, wrapper `withSentryConfig`).
- `feat(backend)` Integrare Sentry in FastAPI (env `SENTRY_DSN_BACKEND`, init doar in staging/production, filtru before_send pentru 4xx).
- `chore(backend)` Logging structurat cu structlog: config nou in `backend/app/logging.py`, integrare startup, log events migrate pe auth/config/main/clerk webhook.
- `test(backend)` Add pytest infrastructure with smoke and auth/kit-access coverage (13 tests).
- `chore(config)` Unificat env vars: root `.env.example` complet (Backend/Frontend/Landing), `infra/env.example` marcat DEPRECATED, `docker-compose.yml` citește variabile din `.env` root.
- `ec5e4df` Validate client name and move delete action next to open button.
- `10f9401` Add soft-delete client flow in backend and frontend.
- `a6df919` Revise communication channels with validated contact detail fields.
- `e0950e0` Normalize role badge width for aligned admin user actions.
- `a9a85fa` Align admin users action column for consistent row layout.
- `fdbab76` Refresh Clerk token on admin actions to prevent expired token errors.
- `cf78b39` Improve admin grant UX feedback and error handling.
- `079af4b` Add admin multi-select grant modal with auto-bundle option.
- `d48b1dd` Show kit names in client risk summaries.
- `74938bc` Add multi-kit client summary on clients list and detail.
- `a2b0348` Bundle Noto Sans fonts for correct Romanian diacritics in PDFs.
- `c5f9e2b` Add consistent loading/success feedback for key actions.
- `8c2b13a` Add save feedback states for client profile.
- `e60be2e` Use checkbox UI for multi-choice profile fields.
- `2383b82` Fix backend runtime imports for product/subscription models.
- `d6203e0` Fix startup seed NameError by importing Product model.
- `746f941` Fix backend startup import for ProductSummaryResponse.
- `abbaa75` Refresh admin nav visibility on route/tab changes.
- `57c0aa9` Implement product subscriptions and gate kit access by purchase.
- `e465f52` Fix missing auth header race on clients page.
- `1a08a78` Add Catalog Kituri page and navigation entry.

## Deploy Status
- Backend (`riskmatrixai-be`): online, acces public fără IP allowlist.
- Frontend (`riskmatrixai-fe`): online pe `riskmatrixai.ro` și `www.riskmatrixai.ro`.

## Current Symptom
- Fără blocker major în platformă.
- În unele rețele locale poate exista cache DNS temporar după migrarea NS (rezolvat global conform DNS checker).

## Next Steps
1. Ruleaza testele backend pe Python 3.12 (local sau CI) pentru validarea completa Sprint 2.1.5.
2. Validare Sentry: trigger eroare backend (500) + eroare frontend (global error) si confirmare event in dashboard.
3. Stripe Sprint 2.2.1: setup products/prices RON in Stripe Dashboard.

## How To Resume (copy/paste in a new chat)
`Continuam din /docs/SESSION_STATUS.md. Domeniul riskmatrixai.ro este live, ALLOWED_IPS este scos din BE+FE, admin grants manuale sunt active; urmatorul task este implementarea Stripe checkout + webhook sync pentru subscriptions.`
