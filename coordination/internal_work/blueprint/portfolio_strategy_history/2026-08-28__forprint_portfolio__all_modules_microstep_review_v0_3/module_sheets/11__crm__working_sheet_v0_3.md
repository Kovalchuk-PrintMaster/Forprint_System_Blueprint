# FORPRINT • МОДУЛЬ 11/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## CRM

**Робоча класифікація:** `CORE RELATIONSHIP/COUNTERPARTY WORK SURFACE`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Manager work surface: client card, debt/value/frequency/average order/seasonality/products/materials/active stage/shipments/check/defects/returns/problem level.
- Aggregates facts from Accounting, Logistics, production, Calculator, Library.
- Likely owns relationship/profile, contacts/preferences, notes, segmentation, communications.

### Погоджений напрям
- May cover clients/suppliers/contractors, but counterparty base model needs explicit decision.
- Cross-channel history should not live independently in Telegram.

### Синтетичне розширення для обговорення
- Separate Person, Counterparty/Client, ContactPoint and Relationship Role.
- Use event projections for financial/operational facts rather than copying mutable truths.

### Відкриті рішення / невідомо
- All counterparties in CRM vs shared Counterparty registry.
- Exact sales pipeline/stage model.
- Marketing segmentation write-back ownership.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- relationship profile
- contacts/preferences
- manager notes
- segmentation
- communication history/projections

**Не повинен owns:**
- financial ledger
- shipment state
- quote engine
- physical stock

**Ключові залежності:**
- Identity
- Accounting
- Logistics
- Calculator
- Telegram/Website/Mobile
- Marketing

## 3. Розширений roadmap з мікрокроками

### R0 — Entity and authority model

- R0.1 Person vs Counterparty vs Client.
- R0.2 ContactPoint/Identifier.
- R0.3 Legal organization/EDRPOU.
- R0.4 Relationship roles.
- R0.5 Canonical vs projected fields.
- R0.6 Legacy Name_+380 alias migration.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — Client/counterparty card

- R1.1 Contacts/preferences.
- R1.2 Notes/tags.
- R1.3 Order/product history projection.
- R1.4 Debt/payment projection.
- R1.5 Shipment/problem projection.
- R1.6 Quick actions.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Pipeline and service

- R2.1 Lead/opportunity stages.
- R2.2 Tasks/reminders.
- R2.3 Complaint/defect/return context.
- R2.4 Manager ownership.
- R2.5 Service SLA flags.
- R2.6 Escalation/history.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Channel unification

- R3.1 Telegram linkage.
- R3.2 Website/mobile account linkage via Identity.
- R3.3 Email/other channels.
- R3.4 Deduplicate contacts.
- R3.5 Consent/preferences.
- R3.6 Cross-channel timeline.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Analytics and marketing

- R4.1 Value/frequency/seasonality.
- R4.2 Segmentation.
- R4.3 Churn/risk signals.
- R4.4 Marketing audience projections.
- R4.5 Conversion attribution input.
- R4.6 Do not overwrite financial truth from analytics.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Manager sees one coherent relationship view with trusted projections and can act without manually hunting across modules.

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
