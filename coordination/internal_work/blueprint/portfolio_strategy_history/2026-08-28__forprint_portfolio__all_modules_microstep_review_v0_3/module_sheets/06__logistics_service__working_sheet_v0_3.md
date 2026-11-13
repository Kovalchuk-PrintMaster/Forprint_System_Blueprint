# FORPRINT • МОДУЛЬ 06/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## Logistics Service

**Робоча класифікація:** `CURRENT H10 SOLE AUTOMATION PILOT`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Physical movement orchestrator ForPrint↔client and contractor/supplier→ForPrint; Telegram integration planned.
- Initial carriers: Nova Poshta, Ukrposhta, taxi; anomalous taxi cost requires approval.
- H10 scope is Logistics-only; no expansion until governed stability evidence and separate decision.
- Transport process/state belongs Logistics, not CRM/Calculator/Library.

### Погоджений напрям
- Readiness request includes origin/destination/deadline/order, dimensions/weight/packaging.
- Track arrival/waiting/no-handoff/cancel/ETA/traffic.
- Client delivery preferences likely owned CRM.

### Синтетичне розширення для обговорення
- Use provider adapters + normalized shipment state machine; keep provider-specific details behind adapters.
- Future route optimization can be added only after reliable basic event tracking.

### Відкриті рішення / невідомо
- Exact source of canonical dimensions/weight after packaging.
- Which taxi/last-mile integrations are stable enough.
- Return/reverse logistics policy.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- shipment intent/process
- carrier selection result
- shipment state/events
- handoff evidence
- transport exceptions

**Не повинен owns:**
- client profile
- order price
- physical inventory
- payment truth

**Ключові залежності:**
- CRM
- Calculator/order context
- Warehouse/packing
- Telegram
- Accounting for charges
- Identity for approvals

## 3. Розширений roadmap з мікрокроками

### R0 — H10 governance readiness

- R0.1 Keep current.yaml as H10 authority.
- R0.2 Repair policy-universe coverage so logistics_service is mandatory in current pilot controls.
- R0.3 Add H10-specific authoritative check gate.
- R0.4 Ensure prompt/release eligibility is fail-closed and release-scoped.
- R0.5 Do not count automatic runs as governed stability evidence until GR-02/GR-03 repaired.
- R0.6 Preserve manual phase/business acceptance boundaries.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — Canonical shipment model

- R1.1 Shipment request schema.
- R1.2 Address/contact normalization without taking CRM ownership.
- R1.3 Package dimensions/weight/packaging references.
- R1.4 Carrier/service option model.
- R1.5 Shipment state machine.
- R1.6 Exception/retry/cancel model.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Provider adapters

- R2.1 Nova Poshta adapter.
- R2.2 Ukrposhta adapter.
- R2.3 Taxi/last-mile adapter abstraction.
- R2.4 Idempotent booking.
- R2.5 Tracking event normalization.
- R2.6 Provider outage/degraded mode.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Operational workflow

- R3.1 Outbound handoff readiness.
- R3.2 Inbound supplier/contractor receipt.
- R3.3 Waiting/no-handoff timeout.
- R3.4 ETA/traffic monitoring where available.
- R3.5 Cost anomaly approval.
- R3.6 Proof-of-handoff/delivery evidence.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Cross-module integration

- R4.1 CRM delivery preferences.
- R4.2 Telegram notifications/actions.
- R4.3 Accounting charge feed.
- R4.4 Warehouse packing/dispatch events.
- R4.5 Operations Assistant contextual actions.
- R4.6 Audit/Inspector checks.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R5 — Stable automation

- R5.1 Two+ governed real automatic runs after control-plane repair.
- R5.2 Stability review PASS.
- R5.3 Error/retry/no-duplicate booking metrics.
- R5.4 Provider failover policy.
- R5.5 Return/reverse logistics.
- R5.6 Separate owner decision before any H10 expansion.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Shipment can be created/tracked/reconciled end-to-end across providers with clear exceptions, evidence and human approval only where policy requires.

## 5. Критерії функціональної зрілості

- Є чіткий canonical owner для даних/станів, якими модуль реально володіє.
- End-to-end сценарії відтворюються з audit/evidence і без прихованого ручного дублювання.
- Dependencies typed і не створюють циклічної authority.
- Failures/unknowns не перетворюються на вигадані success/false/zero.
- Є rollback/recovery/observability для критичних змін.
- Немає критичної сірої зони ownership, що робить automation небезпечною.

## 6. Нотатки / рішення

- [ ] Погоджено без змін
- [ ] Погоджено з правками
- [ ] Потребує додаткової предметної розмови

---
Робочий матеріал • не canonical roadmap • після усного погодження перегенерується.
