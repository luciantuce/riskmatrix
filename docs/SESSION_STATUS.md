# Session Status

Last updated: 2026-05-03 10:20 (Europe/Bucharest)

## Now
- Domeniul `riskmatrixai.ro` este activ prin Cloudflare + Railway custom domain.
- Restricția IP a fost eliminată din Railway (`ALLOWED_IPS` șters pe `riskmatrixai-be` și `riskmatrixai-fe`).
- Admin users are modal „thickbox” pentru grant manual pe 1+ kituri, cu auto-bundle.
- Profil client: canale comunicare extinse cu câmpuri dedicate + validări.
- Ștergere client disponibilă (soft delete) din listă și din pagina clientului.
- UX listă clienți: buton `Sterge` mutat lângă `Deschide client`.
- Validare creare client: blocat nume gol (frontend + backend).

## Last Done
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
1. Stripe Sprint 1: checkout session endpoint + mapare `price_id -> product_code`.
2. Stripe Sprint 1: webhook endpoint (`checkout.session.completed`, `subscription.updated/deleted`, `invoice.payment_*`).
3. Validare end-to-end: cumpărare test card -> grant automat acces kit.

## How To Resume (copy/paste in a new chat)
`Continuam din /docs/SESSION_STATUS.md. Domeniul riskmatrixai.ro este live, ALLOWED_IPS este scos din BE+FE, admin grants manuale sunt active; urmatorul task este implementarea Stripe checkout + webhook sync pentru subscriptions.`
