# FORPRINT • МОДУЛЬ 09/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## Contract Registry

**Робоча класифікація:** `DEFERRED / BOUNDARY UNRESOLVED`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Potential role - canonical machine-readable interface contracts; overlap with Integration Gateway and Library unresolved.
- Current decision: disposition deferred, not silently deleted.

### Погоджений напрям
- Do not create a second semantic authority that conflicts with Library.
- Gateway may enforce runtime contracts while registry, if kept, stores authoritative contract definitions/history.

### Синтетичне розширення для обговорення
- Could become a compact schema/contract catalog with compatibility/consumer graph and contract-test artifacts.
- Could instead be absorbed into Library+Gateway if no independent governance need exists.

### Відкриті рішення / невідомо
- KEEP vs ABSORB vs RETIRE.
- Canonical owner of schemas/types/events/API compatibility.
- Whether contract history merits separate lifecycle.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- UNKNOWN pending disposition

**Не повинен owns:**
- business semantics if Library owns them
- runtime adapter execution if Gateway owns it

**Ключові залежності:**
- Library
- Integration Gateway
- Blueprint

## 3. Розширений roadmap з мікрокроками

### R0 — Disposition analysis

- R0.1 Inventory all schema/contract artifacts.
- R0.2 Compare Library/Gateway ownership.
- R0.3 Identify orphan contract capabilities.
- R0.4 Assess need for independent approval/versioning.
- R0.5 Model KEEP/ABSORB cost.
- R0.6 Owner decision.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — If KEEP - contract catalog

- R1.1 Stable contract IDs.
- R1.2 Version/supersession.
- R1.3 Producer/consumer ownership.
- R1.4 Semantic references to Library.
- R1.5 Compatibility classification.
- R1.6 Contract test bindings.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Lifecycle and tooling

- R2.1 Proposal/review/accept.
- R2.2 Breaking-change impact.
- R2.3 Generated docs/SDK metadata.
- R2.4 Drift detection.
- R2.5 Consumer pinning.
- R2.6 Deprecation/removal policy.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Gateway integration

- R3.1 Gateway resolves accepted contract.
- R3.2 Adapter validates contract version.
- R3.3 Runtime errors reference contract IDs.
- R3.4 Compatibility dashboards.
- R3.5 Rollback.
- R3.6 Reassess separate-module value.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Either a clearly bounded contract authority exists, or every capability is deliberately absorbed elsewhere with no duplicate source of truth.

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
