# FORPRINT • МОДУЛЬ 02/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## Calculator Engine

**Робоча класифікація:** `CORE BUSINESS ENGINE / STRATEGIC PRIORITY`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Центральний engine прорахунку замовлення: feasibility, price, time, materials, operations, equipment, structured job specification.
- Має враховувати quantity, technology, waste, urgency, currency, shortages, failures, congestion і commercial policy.
- Production queue/lead-time ownership поки лишається Calculator, якщо scheduling не виросте в окрему складну систему.
- Library має бути джерелом canonical semantics; Warehouse - actual availability; Accounting - financial consequences.

### Погоджений напрям
- Калькулятор не просто рахує ціну, а приймає структуроване рішення 'чи можемо/як/коли/за скільки'.
- Потрібні product-specific constructors/previews там, де це комерційно виправдано.
- Сайт/Telegram/Mobile мають передавати structured request, а не дублювати pricing logic.

### Синтетичне розширення для обговорення
- Рішення варто моделювати як explainable quote decision з versioned inputs/policies.
- В майбутньому engine може мати sensitivity analysis і scenario quote, але не повинен сам змінювати commercial policy.

### Відкриті рішення / невідомо
- Точна межа scheduling у Calculator vs окремий Production Scheduling capability.
- Пріоритети продуктів для конструкторів після market-demand research.
- Яка частина commercial policy canonical у Calculator, а яка в окремому pricing policy layer/Library.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- quote decision
- feasibility
- planned materials/waste
- planned operations/equipment
- estimated lead time
- structured job specification

**Не повинен owns:**
- actual physical stock
- actual accounting postings/payments
- client relationship truth
- prepress file readiness

**Ключові залежності:**
- Library
- Warehouse Service
- Accounting Registry
- Prepress Hub
- Website/Mobile/Telegram
- Operational/production state

## 3. Розширений roadmap з мікрокроками

### R0 — Inventory і contract stabilization

- R0.1 Зібрати фактичні pricing/feasibility rules з існуючого repo.
- R0.2 Відділити active rules від legacy/manual exceptions.
- R0.3 Визначити canonical input schema і unit conventions.
- R0.4 Визначити output decision model: AVAILABLE/CONSTRAINED/TEMPORARILY_UNAVAILABLE/HIDDEN/MANUAL_QUOTE.
- R0.5 Прив'язати rule/preset IDs до Library semantics.
- R0.6 Зафіксувати regression quote set з реальних типових замовлень.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — Core calculation engine

- R1.1 Нормалізувати product/quantity/dimensions/material/finish options.
- R1.2 Побудувати operation graph для кожного product family.
- R1.3 Додати waste/yield/min-run/machine-setup economics.
- R1.4 Врахувати urgency, shift/load, machine outage, shortage і currency inputs.
- R1.5 Повернути explainable breakdown без витоку внутрішніх секретних коефіцієнтів клієнту.
- R1.6 Забезпечити deterministic/idempotent quote calculation по versioned inputs.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Availability і scheduling

- R2.1 Підключити actual stock/availability read model від Warehouse.
- R2.2 Підключити machine/production availability projection.
- R2.3 Ввести constrained substitutions тільки через дозволені Library mappings.
- R2.4 Розрахувати tentative production slot і ETA.
- R2.5 Додати queue/congestion penalties та capacity threshold.
- R2.6 Відокремити quote expiration від фактичного reservation/commit.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Channel and constructor integration

- R3.1 API contract для Website/Mobile/Telegram.
- R3.2 Product-specific constructor schema з shared primitives.
- R3.3 Preview/visualization hooks без дублювання Prepress logic.
- R3.4 Progressive disclosure: прості продукти без зайвих питань, складні - guided configuration.
- R3.5 Save/reload/requote з version pinning.
- R3.6 Передати accepted job spec downstream без ручного переписування.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Commercial intelligence і quality

- R4.1 Порівнювати estimate vs actual cost/time/materials.
- R4.2 Виявляти systematically underpriced/overpriced scenarios.
- R4.3 Додати scenario analysis для quantity/material/urgency alternatives.
- R4.4 Вводити policy change simulation до публікації.
- R4.5 Вести confidence/manual-quote reasons.
- R4.6 Regression gate на ключових commercial baskets.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R5 — Mature quote decision service

- R5.1 SLA/latency для interactive channels.
- R5.2 Versioned policy deployment + rollback.
- R5.3 Auditable quote lineage до order/job.
- R5.4 Resilient degraded mode при недоступності non-critical sources.
- R5.5 No invented stock/material/price semantics; unknown -> explicit hold/manual quote.
- R5.6 Market-demand data впливає на product roadmap, але не змінює rules без approval.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Один структурований request стабільно дає explainable feasible/not-feasible decision, price, ETA, resource plan і job spec; однакова логіка працює у всіх каналах.

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
