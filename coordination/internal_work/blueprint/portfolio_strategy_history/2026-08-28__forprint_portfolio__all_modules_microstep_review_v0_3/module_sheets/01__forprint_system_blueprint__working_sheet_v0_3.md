# FORPRINT • МОДУЛЬ 01/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## ForPrint System Blueprint

**Робоча класифікація:** `ACTIVE / CURRENT COORDINATION CORE`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Координує архітектуру, ownership boundaries, execution queue, coordination standards, module policy та project-wide governance.
- Чинна release authority визначається coordination/releases/current.yaml; START_HERE та generated projections є навігацією, а не вищою authority.
- Поточна фаза v0.4.1/H10 залишається чинною; Logistics - єдиний automation pilot; cross-module expansion заблокований.
- Перший повний Knowledge Inventory pass B01-B10 завершено: 181 raw findings зведені у 14 global reconciliation programs.
- N10-02 targeted evidence adjudication завершено; наступний крок - N10-03 remediation specification без реалізації.

### Погоджений напрям
- Blueprint лишається центром архітектури, координації, roadmap/dependency control і governance.
- Після повного закриття v0.4.1 - Knowledge Foundation перед широкою автономізацією.
- Рутинне same-phase просування може автоматизуватися лише через fail-closed gates; стратегічні межі, destructive/security/cross-repo рішення лишаються під людським контролем.

### Синтетичне розширення для обговорення
- Зрілий Blueprint працює як portfolio control plane: current-state resolver, dependency graph, WIP balancing, progress/cost/quality telemetry, safe-next-work selection.
- Має бути один deterministic read model для release/phase/slice/pilot/lifecycle/authority/supersession.
- Має підтримувати 10+ кроків уперед як план, але не створювати фальшиву точність або самовільно змінювати owner priorities.

### Відкриті рішення / невідомо
- Остаточна границя Blueprint vs Strategic Control Plane vs Project Inspector.
- Які governance helpers залишаться Blueprint-owned після Knowledge Foundation.
- Який мінімальний web dashboard потрібен після console/machine control plane.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- architecture policy
- module boundaries
- coordination standards
- portfolio roadmap/dependency state
- release/phase navigation projection
- governance gate definitions

**Не повинен owns:**
- runtime business truth модулів
- strategic market truth (SCP)
- independent audit findings (Inspector)
- physical stock/payments/client relation truth

**Ключові залежності:**
- усі модулі через reports/evidence
- Project Inspector
- Strategic Control Plane
- Knowledge Foundation (future)
- Identity для privileged operator surfaces

## 3. Розширений roadmap з мікрокроками

### R0 — Закрити v0.4.1 governance/control-plane reconciliation

- R0.1 Зафіксувати current.yaml як єдине effective release/current-state root і не змінювати H10 authority.
- R0.2 Специфікувати repair для B09 blocker chain: H10 authority resolver, H10 check gate, complete module/pilot policy universe.
- R0.3 Узгодити GR-03: один executable prompt/completion lifecycle, release-gated eligibility, fail-closed acceptance.
- R0.4 Виправити current-looking stale projections через derived read model, а не переписування історії.
- R0.5 Закрити confirmed Markdown fence corruption та zero-byte status artifact через окремі bounded fixes.
- R0.6 Зберегти compatibility_registry до H11; не робити cross-module expansion.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — Knowledge Foundation prerequisites

- R1.1 Нормалізувати artifact lifecycle: current/candidate/historical/generated.
- R1.2 Додати supersedes/corrects/effective-from/source_commit/hash/generated_at/freshness semantics.
- R1.3 Побудувати authority-aware zero-context bundle з current.yaml/doctrine перед Repository Knowledge evidence.
- R1.4 Уніфікувати external input validation contract та evidence manifests.
- R1.5 Побудувати knowledge indexes: capability, standards, dependencies, rationale, unknowns, owners.
- R1.6 Ввести readiness gate; Knowledge Foundation активується лише окремим owner decision після v0.4.1 closeout.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Portfolio roadmap normalization

- R2.1 Для кожного модуля мати Charter/Target State/Capability Catalog/roadmap/unknowns.
- R2.2 Ввести canonical module IDs + aliases і один module universe.
- R2.3 Розділити maturity, release adoption, pause, pilot, dispatch eligibility і strategic priority.
- R2.4 Побудувати typed dependency graph з owner module на кожному dependency ref.
- R2.5 Ввести stable step IDs, design intent, acceptance, evidence, work weight, risk і rollback.
- R2.6 Позначити старі roadmaps historical, якщо вони не є post-Q selection authority.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Portfolio control & dashboard

- R3.1 Console-first dashboard: current phase, blockers, WIP, dependencies, next legal work.
- R3.2 Weighted progress без фальшивої точності; окремо accepted history і remaining work.
- R3.3 Cost/time/rework/quality/executor-model telemetry.
- R3.4 Critical path і dependency starvation detection.
- R3.5 Balance rules: не випускати модуль далеко вперед, якщо його downstream/upstream dependency не готова.
- R3.6 Показувати gray-zone capabilities, orphan intent, unresolved owners і deferred modules.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Managed executor automation

- R4.1 Стандартизувати Work Package + preflight knowledge lookup + evidence report.
- R4.2 Дозволяти deterministic same-phase progression лише fail-closed.
- R4.3 Ввести retry/time/cost/no-progress circuit breakers.
- R4.4 Inspector findings підключити як advisory/maintenance queue, а не як architecture authority.
- R4.5 Автоматизувати recheck/closure evidence, але не business ACCEPT/RETURN/HOLD без окремого дозволу.
- R4.6 Вести trust level executor/model per task class і поступово розширювати автономію.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R5 — Steady-state coordination

- R5.1 Щоденно підтримувати current-state projection і knowledge freshness.
- R5.2 Планувати не менше 5 кроків, target 8+, без максимуму; horizon адаптивний.
- R5.3 Виявляти dependency drift до того, як він блокує downstream modules.
- R5.4 Порівнювати plan vs actual по lead time, quality, cost, rework.
- R5.5 Підтримувати disaster/recovery path для governance state.
- R5.6 Людина втручається лише на phase boundaries, security/destructive exceptions і справжні owner decisions.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Новий сильний zero-context executor за кілька кроків знаходить current authority, legal next work, dependencies, standards і evidence; портфель рухається збалансовано, а governance automation є fail-closed і відновлюваною.

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
