# Logistics Service — evening first-pass owner review

Module: `logistics_service`

Status: `FIRST_PASS_OWNER_DIRECTION_RECORDED / SYNTHETIC_MICROSTEPS_PENDING_SECOND_PASS`

## AGREED_WITH_OWNER

Logistics owns physical transport workflows: moving goods/materials/orders between ForPrint,
customers, contractors and suppliers. It chooses/validates feasible delivery mode, evaluates timing,
buffers and cost, creates the shipment/ride, monitors it live and raises exceptions.

Telegram is a major communication interface, but Logistics owns transport-state logic.

## Working boundary

Logistics consumes customer delivery preferences, order/product context, Calculator estimates,
Library references and historical evidence. It must distinguish confirmed package facts from estimates
and must not become CRM, Accounting or Calculator truth.

## Synthetic roadmap expansion for pass 2

Everything below is `SYNTHETIC_CANDIDATE` unless explicitly described as owner direction.

### LOG-R0 — Transport domain + provider inventory
- inventory Nova Poshta/Ukrposhta/taxi adapters and tracking fields
- define shipment/pickup/leg/quote/event/exception identities
- separate estimated vs confirmed weight/dimensions
### LOG-R1 — Typed delivery request + deadline buffers
- required/optional fields
- pickup/send/customer promise model
- clarification when facts are missing
- buffer policy by delivery class
### LOG-R2 — Package fact resolution
- prefer confirmed measured facts
- otherwise request Calculator estimate by order/job ID
- use Library/reference evidence when appropriate
- use historical comparables only as explicitly estimated
### LOG-R3 — Provider capability/quote adapters
- normalize quote/ETA/limits/tracking
- compare price/ETA/reliability where APIs allow
- fallback provider priority when pre-quote unavailable
### LOG-R4 — Policy selection + approval
- choose by compatibility, deadline, price and reliability
- detect surge price vs baseline
- request approval above threshold
- bind approval to exact route/price/time
### LOG-R5 — Execution + monitoring
- idempotent create
- driver arrival/paid waiting/pickup/in-transit/arrival/storage/completion
- ETA changes and route deviations
- typed exception escalation
### LOG-R6 — Delivery-point resolution
- consume approved prioritized destinations
- validate provider/package constraints
- fallback only to another approved destination
### LOG-R7 — Failure/retry/cancel
- failed pickup, cancelled ride, provider rejection, return
- idempotent retry
- manual decision when cost/customer promise changes materially
### LOG-R8 — Analytics/tuning
- provider cost/ETA/reliability
- predicted vs actual package/ETA
- buffer tuning
- recurring failure patterns

## Dependencies

Telegram, Calculator, CRM/customer preferences, Identity, Accounting, Gateway and Library.

## Open questions for pass 2

Canonical owner of addresses/delivery priorities; real taxi pre-quote API capability; surge thresholds;
delivery-history storage; emergency/air-raid policy; estimate-vs-measurement threshold.

## Target milestone

Most routine transport completes end-to-end automatically with reliable tracking and clear exception handling.

## Steady state

Continue measured improvement after the target milestone; the module is not considered permanently finished.
