# Session Status

Last updated: 2026-05-02 16:25 (Europe/Bucharest)

## Now
- Domeniul `riskmatrixai.ro` este activ prin Cloudflare + Railway custom domain.
- Restricția IP a fost eliminată din Railway (`ALLOWED_IPS` șters pe `riskmatrixai-be` și `riskmatrixai-fe`).
- Admin users are modal „thickbox” pentru grant manual pe 1+ kituri, cu auto-bundle.

## Last Done
- `uncommitted` Admin grant modal:
  - buton `Acorda acces…` în `/admin/users`
  - selecție multi-kit / multi-produs
  - opțiune `auto-bundle` (activă implicit): dacă sunt selectate toate kiturile și există bundle activ, acordă bundle.
- `d48b1dd` Show kit names in client risk summaries.
- `74938bc` Add multi-kit client summary on clients list and detail.
- `a2b0348` Bundle Noto Sans fonts for correct Romanian diacritics in PDFs.
- `uncommitted` Add client summaries:
  - `GET /api/clients` returns per-client summary
  - `GET /api/clients/{id}/summary`
  - `GET /api/clients/{id}/kits/summary`
  - UI badges/cards updated in clients list and client detail page
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
`Continuam din /docs/SESSION_STATUS.md. Domeniul riskmatrixai.ro este live, ALLOWED_IPS este scos din BE+FE; urmatorul task este implementarea Stripe checkout + webhook sync pentru subscriptions.`
