# FORPRINT • МОДУЛЬ 07/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## Integration Gateway

**Робоча класифікація:** `CORE INTEGRATION INFRASTRUCTURE / PLANNED`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Purpose - safe translation/routing where schemas, fields or semantics differ.
- Unknown must not become false/zero; ambiguity/incompatibility -> reject/HOLD + conflict report.
- Semantic definitions come from Library/relevant owner, not Gateway.

### Погоджений напрям
- Gateway runtime enforces contracts/transforms, but does not invent business meaning.
- Need contract tests, correlation/idempotency/errors/observability.

### Синтетичне розширення для обговорення
- Use a small typed contract model rather than giant primitive YAML; CUE-like validation patterns may inspire implementation.
- Could host adapter registry/version compatibility, while Contract Registry if kept may own canonical interface definitions.

### Відкриті рішення / невідомо
- Exact boundary with Contract Registry.
- Whether all internal module-to-module traffic must pass Gateway or only incompatible/external edges.
- Protocol stack and deployment topology.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- runtime mapping/enforcement
- adapter execution
- transport-level compatibility
- correlation/idempotency
- integration error semantics

**Не повинен owns:**
- business semantics
- source domain truth
- auth identity

**Ключові залежності:**
- Library
- Contract Registry disposition
- Identity
- all integrated modules

## 3. Розширений roadmap з мікрокроками

### R0 — Contract inventory

- R0.1 Enumerate integration edges.
- R0.2 Identify schema/semantic/unit mismatches.
- R0.3 Classify internal vs external adapters.
- R0.4 Define conflict/HOLD taxonomy.
- R0.5 Define correlation/idempotency requirements.
- R0.6 Decide Contract Registry boundary.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — Typed contract core

- R1.1 Versioned message envelopes.
- R1.2 Semantic IDs and units.
- R1.3 Required/optional/unknown representation.
- R1.4 Compatibility rules.
- R1.5 Error envelopes.
- R1.6 Contract test harness.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Adapter runtime

- R2.1 Mapping engine.
- R2.2 Validation before/after transform.
- R2.3 Retry/idempotency.
- R2.4 Dead-letter/conflict queue.
- R2.5 Correlation tracing.
- R2.6 Adapter version rollout/rollback.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Priority integrations

- R3.1 Website/Telegram/Mobile -> Calculator.
- R3.2 Calculator -> Accounting/Production.
- R3.3 Logistics provider adapters.
- R3.4 Accounting -> 1C.
- R3.5 CRM/channel events.
- R3.6 System Admin/external device APIs where needed.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Governance and scale

- R4.1 Compatibility matrix.
- R4.2 Breaking-change detection.
- R4.3 Performance/SLA metrics.
- R4.4 Security/PII boundaries.
- R4.5 Automated contract drift findings.
- R4.6 Decide whether Contract Registry stays separate.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Integrations fail safely, are versioned/tested/observable, and no adapter silently fabricates meaning.

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
