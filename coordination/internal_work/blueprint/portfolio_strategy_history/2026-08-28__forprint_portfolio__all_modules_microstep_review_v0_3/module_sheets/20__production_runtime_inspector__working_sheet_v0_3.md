# FORPRINT • МОДУЛЬ 20/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## Production Runtime Inspector

**Робоча класифікація:** `DEFERRED / OVERLAP UNCLEAR`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Seed-only module; possible overlap with Project Inspector, System Administration and production monitoring.
- Disposition intentionally deferred until capability gaps are clearer.

### Погоджений напрям
- Не плутати governance/code Inspector із live production/equipment telemetry.
- Окремий модуль виправданий тільки якщо має власну runtime-observation authority.

### Синтетичне розширення для обговорення
- Potential role: live production telemetry, job/machine runtime anomalies, queue/station health, evidence feed to Operational Registry/Calculator.
- Could instead be absorbed into System Administration + operational module.

### Відкриті рішення / невідомо
- Чи потрібна окрема authority.
- Які equipment protocols/data доступні.
- Boundary with scheduling and SysAdmin.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- UNKNOWN pending disposition

**Не повинен owns:**
- architecture audit
- fleet configuration policy unless assigned

**Ключові залежності:**
- System Administration
- Calculator
- Operational Registry
- Prepress/production devices
- Project Inspector

## 3. Розширений roadmap з мікрокроками

### R0 — Disposition

- R0.1 Inventory runtime telemetry needs.
- R0.2 Separate equipment health vs production-job state.
- R0.3 Compare SysAdmin/Inspector/Operational Registry.
- R0.4 Identify unowned live signals.
- R0.5 Evaluate integration cost.
- R0.6 KEEP/ABSORB/RETIRE decision.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — If KEEP - telemetry model

- R1.1 Equipment/station IDs.
- R1.2 Job runtime events.
- R1.3 Health/anomaly schema.
- R1.4 Timestamp/clock consistency.
- R1.5 Sampling/retention.
- R1.6 Read-only observation boundary.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Collection

- R2.1 Device adapters.
- R2.2 Local buffering.
- R2.3 Event normalization.
- R2.4 Missing/stale signal detection.
- R2.5 Offline recovery.
- R2.6 Data quality evidence.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Operational value

- R3.1 Queue delay projection.
- R3.2 Machine outage signals to Calculator.
- R3.3 Operator alerts.
- R3.4 Job progress feed.
- R3.5 Inspector/compliance evidence.
- R3.6 Reassess separate-module value.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Або має чіткий live-production observation domain, або capabilities поглинаються без дублювання.

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
