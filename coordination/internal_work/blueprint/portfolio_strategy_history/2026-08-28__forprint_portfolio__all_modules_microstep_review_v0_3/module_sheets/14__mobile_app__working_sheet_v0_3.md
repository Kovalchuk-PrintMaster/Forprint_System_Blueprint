# FORPRINT • МОДУЛЬ 14/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## Mobile App

**Робоча класифікація:** `PLANNED CUSTOMER CHANNEL`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Мобільний додаток входить у target system, але деталізація менша за Website/Telegram.
- Не повинен дублювати Calculator/CRM/Identity/Logistics logic.

### Погоджений напрям
- Має бути ще одним thin client до спільних business services.
- Central Identity потрібний для auth/session/recovery.

### Синтетичне розширення для обговорення
- Перший реліз варто сфокусувати на account/order/quote/status/file/notification flows, а не на повному desktop parity.
- Offline mode тільки для cached view/drafts, не для authoritative business commits.

### Відкриті рішення / невідомо
- iOS/Android native vs cross-platform.
- Push provider stack.
- Exact first-release scope.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- mobile UX
- device session integration
- push notifications
- local drafts/cache

**Не повинен owns:**
- price/order truth
- client profile authority
- payment ledger
- shipment truth

**Ключові залежності:**
- Identity
- CRM
- Calculator
- Logistics
- Website APIs/Gateway
- Design System

## 3. Розширений roadmap з мікрокроками

### R0 — Product definition

- R0.1 Top mobile jobs-to-be-done.
- R0.2 Platform/framework choice.
- R0.3 Auth/security constraints.
- R0.4 Notification scope.
- R0.5 Offline/cache rules.
- R0.6 MVP acceptance.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — Account and navigation

- R1.1 Identity login/passkey/MFA.
- R1.2 Client/account context selection.
- R1.3 Profile/preferences projection.
- R1.4 Secure local session storage.
- R1.5 Design System mobile tokens.
- R1.6 Accessibility.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Quote/order flows

- R2.1 Product browse.
- R2.2 Structured configuration.
- R2.3 Calculator quote.
- R2.4 Draft/save.
- R2.5 Order confirmation.
- R2.6 File attachment/prepress handoff.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Status and communication

- R3.1 Order timeline.
- R3.2 Logistics tracking.
- R3.3 Payment status.
- R3.4 Push notifications.
- R3.5 Support/escalation.
- R3.6 Cross-channel CRM history.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Maturity

- R4.1 Crash/performance telemetry.
- R4.2 Feature flags/rollout.
- R4.3 Offline draft conflict handling.
- R4.4 Security review.
- R4.5 Store release automation.
- R4.6 Adoption/retention feedback into product roadmap.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Клієнт має швидкий мобільний доступ до quote/order/status/files/notifications без дублювання business logic.

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
