# Website — evening first-pass owner review

Module: `website`

Status: `FIRST_PASS_OWNER_DIRECTION_RECORDED / SYNTHETIC_MICROSTEPS_PENDING_SECOND_PASS`

## AGREED_WITH_OWNER

Website should increasingly be a thin, strong storefront/presentation channel rather than a second
implementation of ForPrint business logic. It presents products/design/SEO/catalog content and routes the
customer into canonical services for calculation, identity, payment/order and status.

The existing site already runs and must not be destructively rewritten during transition.

## Working boundary

Website owns presentation/storefront UX, SEO and channel analytics. It does not own canonical prices,
materials, order truth, accounting truth or credentials.

Existing cabinet/cart/order/login functions remain usable legacy behavior until controlled replacements are ready.

## Synthetic roadmap expansion for pass 2

Everything below is `SYNTHETIC_CANDIDATE` unless explicitly described as owner direction.

### WEB-R0 — Inventory current production site
- cabinet/cart/order/login behavior
- hosting/local-test workflow
- SEO/catalog/content/analytics
- valuable legacy vs duplicate business logic
### WEB-R1 — Thin storefront boundary
- catalog/presentation/landing ownership
- backend service boundaries
- no price/material/order formulas in frontend
- clear backend-unavailable behavior
### WEB-R2 — Shared Identity integration
- replace local auth only after shared Identity works
- preserve current login during migration
- account/recovery entry points
- local integration test before hosting
### WEB-R3 — Calculator/configurator integration
- product -> configuration/quote flow
- constructor/editor integrations
- reconstructible configurations where safe
- no duplicate formulas
### WEB-R4 — Checkout/payment/order shell
- initiate canonical order/payment
- display owning-module confirmations/status
- explicit customer confirmation
- no frontend-only business truth
### WEB-R5 — Design migration
- current visual design remains production baseline
- second shared-Design-System variant only after explicit approval
- local-server testing first
- separate hosting publication + rollback
### WEB-R6 — SEO/performance/conversion
- fast accessible product discovery
- privacy-aware analytics
- conversion/error observability
- mobile/responsive performance

## Dependencies

Identity & Access, Library, Calculator, Accounting/payment, Logistics, Prepress/files, CRM/order status,
ForPrint Design System.

## Open questions for pass 2

Legacy feature retirement order; constructor frontend stack; payment boundary; account/history depth;
SEO/catalog source integration.

## Target milestone

A fast reliable storefront launches the correct canonical ForPrint capabilities without duplicating business truth.

## Steady state

Continue measured improvement after the target milestone; the module is not considered permanently finished.
