# FORPRINT • МОДУЛЬ 13/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## Website / Storefront

**Робоча класифікація:** `EXISTING LEGACY WORKING PROJECT / PAUSED FOR MAJOR CHANGES`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Old independent working project; cabinet/account/cart/order exist but imperfect.
- Future role - thin storefront/presentation: design/images/descriptions/examples/SEO/catalog/landing/specialist services.
- Pricing/configuration -> Calculator; auth -> Identity; payment delegated to Accounting/payment layer.
- Existing visual design is production baseline; no redesign without explicit approval.

### Погоджений напрям
- Legacy flows stabilize until replacements ready; migration gradual/tested with rollback.
- Do not invest heavily in duplicate site intelligence.

### Синтетичне розширення для обговорення
- Adopt shared Design System through adapters/components gradually, not a big-bang rewrite.
- Use server-side SEO/content rendering independent of heavy business logic.

### Відкриті рішення / невідомо
- Exact framework/hosting modernization.
- Payment provider boundary.
- Which existing cabinet features are retained vs replaced.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- storefront presentation
- catalog browsing projection
- SEO/landing content
- web session UX

**Не повинен owns:**
- pricing engine
- identity authority
- financial ledger
- CRM relationship truth

**Ключові залежності:**
- Identity
- Calculator
- CRM
- Accounting/payment
- Library
- Design System

## 3. Розширений roadmap з мікрокроками

### R0 — Legacy stabilization and inventory

- R0.1 Map existing routes/features.
- R0.2 Mark stable/broken/replace-later flows.
- R0.3 Preserve production visual baseline.
- R0.4 Add regression smoke tests.
- R0.5 Identify duplicated pricing/auth/client logic.
- R0.6 No redesign during inventory.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — Thin-storefront boundaries

- R1.1 Catalog/content model.
- R1.2 Calculator integration contract.
- R1.3 Identity/OIDC integration plan.
- R1.4 CRM/account projection.
- R1.5 Payment initiation boundary.
- R1.6 Error/degraded-mode UX.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Shared Design System gradual adoption

- R2.1 Map current components to canonical tokens.
- R2.2 Pilot low-risk components.
- R2.3 Accessibility baseline.
- R2.4 Local visual regression.
- R2.5 Explicit owner approval per visible migration wave.
- R2.6 Rollback path.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Commerce flow modernization

- R3.1 Structured product configuration.
- R3.2 Quote/order handoff.
- R3.3 Account/session via Identity.
- R3.4 Order/history via CRM projections.
- R3.5 Payment status.
- R3.6 File upload/prepress handoff.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Content/SEO/performance

- R4.1 Landing pages.
- R4.2 Examples/media.
- R4.3 Structured metadata.
- R4.4 Search/performance.
- R4.5 Analytics events.
- R4.6 Content governance through Library/Marketing.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Fast stable storefront presents products/content, captures structured intent and delegates all core business decisions to owner services.

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
