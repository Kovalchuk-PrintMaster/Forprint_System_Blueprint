# FORPRINT • МОДУЛЬ 08/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## Prepress Hub

**Робоча класифікація:** `CORE PRODUCTION PREPARATION / PLANNED`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Automates preflight, normalization, safe fixes and print-ready preparation through Acrobat/Photoshop/Illustrator/PitStop/Quite Imposing style adapters.
- Uncertain cases go to human; client-facing warnings and approval should be friendly and actionable.
- Owns prepress readiness/requirements/blockers/station preset policy.

### Погоджений напрям
- Stages: preflight -> normalize/fix -> production-ready -> integrations.
- Need evidence/preview/quality checks and tool/preset version lineage.

### Синтетичне розширення для обговорення
- Represent every transformation as reproducible recipe + input/output hashes.
- Quality model can learn common failure patterns but must not auto-fix ambiguous design semantics.

### Відкриті рішення / невідомо
- Which commercial tools remain mandatory.
- How much image/design repair can be safely automated.
- Where large source/output files are stored.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- prepress readiness
- preflight findings
- safe normalization/fix recipes
- production-ready derivative
- prepress presets

**Не повинен owns:**
- product pricing
- business approval
- original client intent when ambiguous
- printer runtime execution

**Ключові залежності:**
- Calculator job spec
- Library standards
- Design System only for UI
- Operations Assistant
- Production runtime

## 3. Розширений roadmap з мікрокроками

### R0 — Rule/tool inventory

- R0.1 Collect current manual prepress rules.
- R0.2 Map rule to tool/preset.
- R0.3 Classify auto-fix safe/unsafe/conditional.
- R0.4 Build representative file corpus.
- R0.5 Define print-ready acceptance profile per product/process.
- R0.6 Version tool/preset environment.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — Preflight engine

- R1.1 PDF/file format checks.
- R1.2 Geometry/bleed/trim.
- R1.3 Color/spot/transparency.
- R1.4 Fonts/text embedding.
- R1.5 Resolution/image checks.
- R1.6 Structured finding report.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Normalization/fix

- R2.1 Safe PDF normalization.
- R2.2 Color/profile corrections where deterministic.
- R2.3 Font/resource handling.
- R2.4 Imposition/pagination recipes.
- R2.5 Before/after preview/evidence.
- R2.6 Human approval for uncertain/destructive fixes.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Tool adapters

- R3.1 Acrobat/PitStop automation.
- R3.2 Photoshop adapter.
- R3.3 Illustrator adapter.
- R3.4 Quite Imposing/imposition adapter.
- R3.5 Tool failure/retry handling.
- R3.6 Version/preset compatibility tests.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Production integration

- R4.1 Consume Calculator job spec.
- R4.2 Emit readiness/blockers.
- R4.3 Operations Assistant operator guidance.
- R4.4 Production preset handoff.
- R4.5 Client approval loop when visual change matters.
- R4.6 Regression corpus and quality metrics.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Files pass deterministic print-readiness checks, safe fixes are reproducible, uncertainty is explicit, and operators receive evidence-rich handoff.

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
