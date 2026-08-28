# FORPRINT • МОДУЛЬ 15/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## Project Inspector

**Робоча класифікація:** `SUPERVISORY AUDIT MODULE / PLANNED-ADVANCING`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Continuously compares modules to governing docs and changing rules; catches architecture/code/dependency/contract drift.
- External best practice is evidence/risk, not authority.
- Future intervention ladder: OBSERVE -> WARN -> CRITICAL_FINDING -> REQUEST/ISSUE_PAUSE; auto-pause only narrowly preauthorized.

### Погоджений напрям
- Inspector is observer/auditor, not architecture owner.
- Findings need lifecycle, recheck and false-positive handling.

### Синтетичне розширення для обговорення
- Inspector should evaluate its own precision/recall and avoid alert fatigue.
- Policy readers should be version-aware and use current authority resolver.

### Відкриті рішення / невідомо
- Exact auto-pause conditions.
- Scope of runtime production monitoring vs Production Runtime Inspector.
- How findings enter executor maintenance queue.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- audit findings
- drift observations
- recheck status
- evidence links
- inspection policy execution

**Не повинен owns:**
- architecture decisions
- business truth
- strategic direction

**Ключові залежності:**
- Blueprint
- all module repos
- Knowledge Foundation
- Strategic Control Plane for external evidence only

## 3. Розширений roadmap з мікрокроками

### R0 — Inspection policy foundation

- R0.1 Define current authority reader.
- R0.2 Finding schema/severity/confidence.
- R0.3 Evidence requirements.
- R0.4 False-positive/dispute lifecycle.
- R0.5 Recheck semantics.
- R0.6 Scope boundary vs runtime inspector.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — Static governance inspection

- R1.1 Roadmap conformity.
- R1.2 Architecture boundaries.
- R1.3 Dependency declarations.
- R1.4 Contract/version drift.
- R1.5 Documentation freshness.
- R1.6 Generated artifact lineage.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Code/repository inspection

- R2.1 Deprecated API usage.
- R2.2 Duplicate semantics.
- R2.3 Unowned capabilities.
- R2.4 Security/config drift signals.
- R2.5 Test/acceptance coverage drift.
- R2.6 No-write inspection mode.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Finding lifecycle integration

- R3.1 Maintenance queue output.
- R3.2 Owner acknowledgement.
- R3.3 Fix evidence.
- R3.4 Automated recheck.
- R3.5 Close/reopen.
- R3.6 Escalation to Blueprint.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Controlled intervention

- R4.1 OBSERVE.
- R4.2 WARN.
- R4.3 CRITICAL_FINDING.
- R4.4 REQUEST_PAUSE.
- R4.5 Narrow preauthorized auto-pause only with explicit policy.
- R4.6 Measure Inspector quality and alert fatigue.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Inspector reliably detects meaningful drift early, produces reproducible findings and can trigger bounded governance responses without becoming a shadow authority.

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
