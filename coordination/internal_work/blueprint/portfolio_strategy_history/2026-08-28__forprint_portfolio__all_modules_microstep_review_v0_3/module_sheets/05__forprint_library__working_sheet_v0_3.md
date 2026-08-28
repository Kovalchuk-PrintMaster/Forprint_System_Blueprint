# FORPRINT • МОДУЛЬ 05/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## ForPrint Library

**Робоча класифікація:** `CORE SEMANTIC/REFERENCE AUTHORITY`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Canonical source для business/reference/semantic truth: current commercial proposals, forms/templates, material/product names, standards, instructions, classifiers, long-lived rules.
- Має lifecycle current/outdated/still-supported/forbidden, revisions/history, aliases/deprecations.
- Не є transactional physical stock, payment/order/CRM history.
- Не плутати з Blueprint Knowledge Foundation.

### Погоджений напрям
- Library надає stable semantic IDs і definitions; consumers читають, але не перевизначають.
- Rename/deprecation повинні зберігати aliases/migration history.
- Design System canonical tokens/component definitions логічно можуть жити тут як reference semantics.

### Синтетичне розширення для обговорення
- Потрібні resolve/query APIs, compatibility/freshness/confidence metadata, SDK/cache/version pinning.
- Library може стати canonical registry для design tokens і instruction metadata, але не runtime media delivery.

### Відкриті рішення / невідомо
- Фізичне розміщення великих media assets.
- Межа з Contract Registry для machine-readable interface contracts.
- Approval roles per content class.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- semantic/reference dictionaries
- product/material taxonomy
- standards/instructions metadata
- aliases/deprecations
- reference versions

**Не повинен owns:**
- stock quantities
- financial postings
- transactional orders
- client history

**Ключові залежності:**
- Blueprint governance
- Domain owners
- Identity
- Website/Calculator/Prepress/Ops Assistant consumers

## 3. Розширений roadmap з мікрокроками

### R0 — Authority and inventory

- R0.1 Зібрати reference artifacts і dictionaries.
- R0.2 Класифікувати current/outdated/still-supported/forbidden.
- R0.3 Ввести stable semantic IDs.
- R0.4 Побудувати alias/deprecation table.
- R0.5 Призначити content owners/approvers.
- R0.6 Відділити transactional data.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — Versioned semantic registry

- R1.1 Revision model.
- R1.2 Effective-from/valid-to.
- R1.3 Supersedes/replaced-by.
- R1.4 Compatibility relations.
- R1.5 Confidence/source provenance.
- R1.6 Search/index metadata.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Query/resolve service

- R2.1 Resolve current by semantic ID.
- R2.2 Resolve as-of timestamp/version.
- R2.3 Alias migration.
- R2.4 Bulk dictionary export.
- R2.5 Typed validation schemas.
- R2.6 Cache/ETag/version pinning.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Cross-module pilots

- R3.1 Calculator materials/products.
- R3.2 Prepress standards/presets.
- R3.3 Operations Assistant instructions.
- R3.4 Website catalog semantics.
- R3.5 Design System tokens/components metadata.
- R3.6 Detect stale consumer versions.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Governed evolution

- R4.1 Proposal/approval workflow.
- R4.2 Impact analysis before breaking change.
- R4.3 Consumer compatibility report.
- R4.4 Automated stale-reference findings.
- R4.5 Audit trail.
- R4.6 Disaster restore/version integrity.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Будь-який модуль може однозначно resolve semantic ID/version/status, отримати current definition і зрозуміти compatibility/freshness без власних локальних словників.

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
