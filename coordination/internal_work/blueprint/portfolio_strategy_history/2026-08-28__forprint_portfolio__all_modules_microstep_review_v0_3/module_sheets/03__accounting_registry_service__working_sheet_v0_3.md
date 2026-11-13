# FORPRINT • МОДУЛЬ 03/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## Accounting Registry Service

**Робоча класифікація:** `CORE COMMERCIAL/FINANCIAL REGISTRY`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Мета - operational/commercial accounting registry, що поступово забирає щоденну операційну роботу з 1C, але не замінює statutory/tax reporting на старті.
- Охоплення: purchases, sales, invoices, payments, settlements, writeoffs, management reporting, document state, reconciliation.
- 1C лишається statutory/downstream system while needed.
- Warehouse owns physical stock fact; Accounting owns documentary movement/value/state/reconciliation.

### Погоджений напрям
- Money/document flows мають бути exact, idempotent, audit-ready і без duplicate/lost postings.
- Людина втручається при conflicts, ambiguous mappings, corrections і untrusted facts.
- Planned material/price від Calculator не дорівнює actual consumption/accounting.

### Синтетичне розширення для обговорення
- Сервіс має мати double-entry-like invariant або еквівалентну формальну reconciliation model, навіть якщо UI не бухгалтерський.
- 1C connector краще будувати як controlled adapter з reconciliation ledger, а не двосторонню магічну синхронізацію.

### Відкриті рішення / невідомо
- Точна authority при конфлікті ForPrint vs 1C на різних етапах переходу.
- Чи будуть supplier/client counterparties owned CRM або shared Counterparty entity.
- Які statutory exports потрібні довгостроково.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- commercial documents
- payments/settlements state
- documentary goods movement
- management financial facts
- reconciliation incidents

**Не повинен owns:**
- physical stock truth
- pricing decision
- client relationship profile
- statutory tax authority at initial stages

**Ключові залежності:**
- CRM
- Warehouse Service
- Calculator
- 1C connector
- Logistics
- Identity

## 3. Розширений roadmap з мікрокроками

### R0 — Current accounting inventory

- R0.1 Інвентаризувати існуючі 1C/ручні потоки і документи.
- R0.2 Визначити canonical Accounting module ID і aliases.
- R0.3 Побудувати document/payment/state dictionary.
- R0.4 Виділити immutable external identifiers та idempotency keys.
- R0.5 Описати authority matrix ForPrint vs 1C per entity/phase.
- R0.6 Зібрати reconciliation test cases: duplicate, late payment, correction, partial payment, return.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — Commercial ledger core

- R1.1 Order-linked invoice/sale/purchase document model.
- R1.2 Payment events і allocation to documents.
- R1.3 Counterparty references через stable IDs.
- R1.4 Documentary goods movement and valuation.
- R1.5 Correction/reversal model без destructive history rewrite.
- R1.6 Management balance and settlement views.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — 1C bridge and reconciliation

- R2.1 One-way export baseline з explicit mapping.
- R2.2 Import acknowledgements/errors в reconciliation ledger.
- R2.3 Detect duplicates/missing/mismatched totals.
- R2.4 Manual conflict workbench для ambiguous mapping.
- R2.5 Idempotent retry/replay.
- R2.6 Period close comparison і signed reconciliation evidence.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Cross-module automation

- R3.1 Consume accepted order/job identifiers.
- R3.2 Consume actual Warehouse movements, не planned demand.
- R3.3 Receive Logistics charges/adjustments.
- R3.4 Expose payment/debt/financial summaries to CRM with least privilege.
- R3.5 Emit financial events to analytics/Marketing without leaking sensitive detail.
- R3.6 Role-based approval for high-risk correction/writeoff.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Operational replacement of daily 1C work

- R4.1 Shift routine invoice/payment/settlement operations to ForPrint.
- R4.2 Keep statutory posting/export boundary explicit.
- R4.3 Monitor no-lost/no-duplicate invariants.
- R4.4 Reconciliation incident SLA.
- R4.5 Recovery/replay from event/document history.
- R4.6 1-2 quarter stability observation before further authority expansion.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R5 — Mature financial registry

- R5.1 Auditable lineage order -> documents -> payments -> settlements.
- R5.2 Exact currency/rounding rules versioned.
- R5.3 Configurable tax/statutory connectors without changing core ledger semantics.
- R5.4 Management reporting with source-level drilldown.
- R5.5 Controlled period locks and exception workflow.
- R5.6 Long-term 1C role reduced to statutory/downstream only if separately approved.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Усі operational commercial документи/платежі/взаєморозрахунки відтворювані, reconciled, без дублювання; 1C отримує контрольований downstream feed доки потрібен.

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
