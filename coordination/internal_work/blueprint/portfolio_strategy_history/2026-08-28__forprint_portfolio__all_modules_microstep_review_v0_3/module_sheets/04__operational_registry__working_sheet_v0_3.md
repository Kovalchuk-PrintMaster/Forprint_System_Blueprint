# FORPRINT • МОДУЛЬ 04/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## Operational Registry

**Робоча класифікація:** `DEFERRED / OWNERSHIP UNCLEAR`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Модуль присутній у портфельному переліку, але остаточна роль не визначена.
- Можлива роль - entity/operational bridge між orders/jobs/equipment/production states, але є значний overlap з Calculator, Warehouse, CRM, Accounting і Runtime Inspector.

### Погоджений напрям
- Не будувати модуль тільки тому, що він існує в seed inventory.
- Спочатку треба знайти позитивну власну authority, якої немає в інших модулях.

### Синтетичне розширення для обговорення
- Найкращий кандидат ролі - canonical operational entity/state registry для Job/WorkOrder/ResourceAssignment, якщо scheduling/runtime truth не вкладається в Calculator.
- Другий варіант - модуль взагалі не потрібен і його capabilities розподіляються.

### Відкриті рішення / невідомо
- Чи існує унікальна canonical data область.
- Чи потрібен окремий Work Order registry.
- Межа з Production Runtime Inspector і Warehouse.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- UNKNOWN - тільки після disposition

**Не повинен owns:**
- не повинен дублювати client/accounting/stock/quote semantics

**Ключові залежності:**
- Calculator
- Warehouse
- Prepress
- Production Runtime Inspector
- Accounting

## 3. Розширений roadmap з мікрокроками

### R0 — Disposition evidence

- R0.1 Зібрати всі згадки Operational Registry у docs/code.
- R0.2 Побудувати capability overlap matrix.
- R0.3 Перерахувати canonical entities, які зараз не мають owner.
- R0.4 Визначити, чи Job/WorkOrder state вже owned іншим модулем.
- R0.5 Перевірити потребу в transactionally consistent operational registry.
- R0.6 Owner decision: KEEP / ABSORB / SPLIT / RETIRE.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — If KEEP - authority charter

- R1.1 Визначити canonical entities та immutable IDs.
- R1.2 Визначити state machines і legal transitions.
- R1.3 Визначити read/write ownership по сусідах.
- R1.4 Визначити conflict/reconciliation semantics.
- R1.5 Визначити event contract.
- R1.6 Заборонити дублювання price/stock/payment/client truth.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Core registry

- R2.1 CRUD тільки через domain transitions, не arbitrary edits.
- R2.2 Audit history.
- R2.3 Idempotent command handling.
- R2.4 Read models для operational dashboards.
- R2.5 Referential integrity з job/order/resource IDs.
- R2.6 Recovery/replay.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Integrations

- R3.1 Calculator handoff.
- R3.2 Prepress readiness.
- R3.3 Warehouse material assignment.
- R3.4 Runtime inspector observations.
- R3.5 Accounting actual completion/consumption events.
- R3.6 Operations Assistant work instructions.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Automation readiness

- R4.1 Validate state transition invariants.
- R4.2 Human exception queue.
- R4.3 Stale-state detection.
- R4.4 Conflict semantics.
- R4.5 Observability.
- R4.6 Independent keep/absorb reassessment after real use.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Або має чітку, незамінну canonical authority і контракт, або офіційно retired/absorbed без orphan capabilities.

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
