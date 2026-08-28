# FORPRINT • МОДУЛЬ 10/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## Telegram Bot / Channel Orchestrator

**Робоча класифікація:** `CUSTOMER CHANNEL / PLANNED`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Telegram - поточний зовнішній channel; email/Viber/WhatsApp можливі пізніше.
- Перетворює human semantics у structured request, викликає owner module і повертає дружню відповідь.
- Не owns prices/accounting/logistics decisions.
- 2-3 bounded AI attempts, далі manager escalation з контекстом.

### Погоджений напрям
- 'Same as last time' має намагатись знайти prior job/file.
- Repeated trivial escalation - automation failure signal.
- Cross-channel history likely CRM.

### Синтетичне розширення для обговорення
- Зробити channel adapter architecture, щоб Telegram не став монолітом для всіх месенджерів.
- Conversation memory має посилатись на CRM/Identity IDs, не створювати власну client truth.

### Відкриті рішення / невідомо
- Exact approval/consent model for client actions.
- How to handle unsupported media/large files.
- Multi-language needs.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- conversation/channel state
- message transport
- structured intent extraction
- channel-specific UX
- bounded escalation packaging

**Не повинен owns:**
- quote decision
- client profile canonical truth
- shipment state
- payment state

**Ключові залежності:**
- Identity
- CRM
- Calculator
- Logistics
- Prepress
- Operations Assistant for internal flows

## 3. Розширений roadmap з мікрокроками

### R0 — Channel contract

- R0.1 Message/session model.
- R0.2 Identity binding rules.
- R0.3 Consent/confirmation semantics.
- R0.4 Intent schema.
- R0.5 Escalation criteria.
- R0.6 Attachment/media policy.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — Core interaction

- R1.1 Text intent extraction.
- R1.2 Clarification loop max attempts.
- R1.3 Structured confirmation.
- R1.4 Owner-module dispatch.
- R1.5 Friendly result formatting.
- R1.6 Manager handoff packet.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — History/context

- R2.1 CRM conversation linkage.
- R2.2 Prior job lookup.
- R2.3 'same as last time' disambiguation.
- R2.4 File/photo context.
- R2.5 Client preference projection.
- R2.6 Privacy retention policy.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Operational integrations

- R3.1 Calculator quote.
- R3.2 Logistics tracking/actions.
- R3.3 Prepress warnings/approval.
- R3.4 Payment/status notifications.
- R3.5 Human manager actions.
- R3.6 Event audit.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Multi-channel evolution

- R4.1 Abstract channel adapter.
- R4.2 Email.
- R4.3 Viber/WhatsApp if justified.
- R4.4 Cross-channel deduplication.
- R4.5 Response quality/escalation metrics.
- R4.6 Channel-specific policy without duplicating business logic.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Клієнт може природно сформувати запит, підтвердити структуровану інтерпретацію, отримати owner-module result і безболісно ескалувати менеджеру.

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
