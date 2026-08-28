# FORPRINT • МОДУЛЬ 21/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## Warehouse Service

**Робоча класифікація:** `DEFERRED BUT LIKELY REQUIRED PHYSICAL-STOCK AUTHORITY`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Seed-only module; physical stock truth is a clear cross-module need, but separate-module justification is formally deferred.
- Accounting should own documentary movement/value; Warehouse physical fact.
- Calculator needs actual availability, not accounting balance or planned demand.

### Погоджений напрям
- Mismatch Warehouse physical fact vs Accounting documentary state becomes reconciliation incident.
- Planned materials remain Calculator; actual physical receipt/issue/count belongs Warehouse if module kept.

### Синтетичне розширення для обговорення
- Likely canonical entities: stock item/lot/location/reservation/physical movement/count discrepancy.
- Could support barcode/QR, cycle count, reservation and shortage events.

### Відкриті рішення / невідомо
- KEEP as separate service vs operational registry capability.
- Lot/batch/serial requirements.
- Physical locations and scanning hardware.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- candidate: physical quantity/location/lot/reservation/stock movement fact

**Не повинен owns:**
- valuation/accounting document state
- planned material demand
- product semantic definitions

**Ключові залежності:**
- Library
- Accounting
- Calculator
- Logistics
- Operations Assistant
- Identity

## 3. Розширений roadmap з мікрокроками

### R0 — Disposition and physical truth definition

- R0.1 Inventory stock processes.
- R0.2 Define physical vs documentary boundary.
- R0.3 Locations/bins/items/lots needs.
- R0.4 Reservation semantics.
- R0.5 Reconciliation responsibilities.
- R0.6 KEEP/ABSORB decision.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — Core stock registry

- R1.1 Item/location IDs.
- R1.2 Receipt.
- R1.3 Issue.
- R1.4 Transfer.
- R1.5 Adjustment/count.
- R1.6 Immutable movement history.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Availability/reservation

- R2.1 On-hand.
- R2.2 Available-to-promise.
- R2.3 Reservation.
- R2.4 Shortage.
- R2.5 Expiry/lot constraints if needed.
- R2.6 Calculator query API.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Scanning and operations

- R3.1 Barcode/QR.
- R3.2 Mobile/operator workflows.
- R3.3 Picking/packing.
- R3.4 Supplier receipt.
- R3.5 Production consumption.
- R3.6 Cycle count.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Accounting/logistics reconciliation

- R4.1 Documentary movement linkage.
- R4.2 Mismatch incident.
- R4.3 Shipment handoff.
- R4.4 Cost/valuation references without owning value.
- R4.5 Audit trail.
- R4.6 Shrinkage/accuracy metrics.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Physical stock fact is timely, scannable and reconciled with accounting; Calculator and production can trust availability without inventing quantities.

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
