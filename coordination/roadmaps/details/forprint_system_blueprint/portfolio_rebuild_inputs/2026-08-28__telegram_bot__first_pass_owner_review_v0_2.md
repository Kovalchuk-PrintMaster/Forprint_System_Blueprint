# Telegram Bot — evening first-pass owner review

Module: `telegram_bot`

Status: `FIRST_PASS_OWNER_DIRECTION_RECORDED / SYNTHETIC_MICROSTEPS_PENDING_SECOND_PASS`

## AGREED_WITH_OWNER

Telegram is an intelligent external communication gateway for customers, suppliers, contractors and other
outside actors. It understands natural language and attachments, builds relevant context, converts intent into
structured internal requests, calls owning modules and translates technical results back into natural conversation.

It does not calculate prices, own accounting, own logistics or become the canonical business database.

## Working boundary

Long-term omnichannel customer history should be available to Telegram but should likely live in CRM/communication
storage rather than be trapped inside one channel. Telegram owns channel/dialog behavior; domain truth stays in
profile modules.

## Synthetic roadmap expansion for pass 2

Everything below is `SYNTHETIC_CANDIDATE` unless explicitly described as owner direction.

### TG-R0 — Inventory current bot/ML/dialog work
- current intents/dialogs/identity mappings
- DeBERTa/Mistral/vision/STT integrations
- procurement/logistics/admin scenarios
- retain strong old pieces without making legacy UX authority
### TG-R1 — Identity + context linkage
- resolve verified person/contact/client identity
- link Telegram/phone to canonical identity
- read relevant CRM context
- respect cross-account security rules
### TG-R2 — Typed intent/entity parser
- intent classification
- product/order/date/quantity extraction
- confidence + missing information
- minimal high-information clarification
### TG-R3 — Attachment/multimodal intake
- images/PDF/Word/Excel/audio
- size/safety/retention policy
- route file work to Prepress/document tools
- bounded AI context bundles
### TG-R4 — Domain orchestration
- Calculator quote/order draft
- Accounting invoices/payment questions
- Logistics pickup/shipment/status
- Library forms/reference truth
- CRM relationship/follow-up
### TG-R5 — AI escalation layer
- structured logic first
- specialized model/provider when needed
- bounded attempts + explicit uncertainty
- human escalation for unresolved/unsafe cases
### TG-R6 — Human-friendly response
- preserve exact domain facts
- adapt technical results to natural language
- avoid hallucinating missing facts
- approved tone/style policy
### TG-R7 — Human escalation learning
- package exact context/reason
- capture operator correction
- classify hard vs automatable escalation
- feed recurring easy cases into backlog
### TG-R8 — Production metrics
- automatic completion rate
- clarification count
- routing accuracy
- correction/rework rate
- escalation reason mix

## Dependencies

Identity & Access, CRM, Calculator, Accounting, Logistics, Library, Prepress, Gateway, order/operational truth
and AI provider/model layer.

## Open questions for pass 2

Canonical omnichannel history owner; model routing/privacy/cost; attempt budget; legally/financially significant
message confirmation; future channels.

## Target milestone

Routine external conversations become structured end-to-end work; humans mainly receive genuinely ambiguous,
risky or exceptional cases.

## Steady state

Continue measured improvement after the target milestone; the module is not considered permanently finished.
