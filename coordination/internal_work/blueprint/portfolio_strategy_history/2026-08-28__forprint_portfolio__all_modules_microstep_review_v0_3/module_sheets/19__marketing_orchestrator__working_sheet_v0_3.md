# FORPRINT • МОДУЛЬ 19/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## Marketing Orchestrator

**Робоча класифікація:** `INTELLIGENT MARKETING PLANNER / PLANNED`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Closed-loop marketing planner/orchestrator using Telegram/CRM/DB/accounting/site/search analytics.
- Plans week/month/quarter and generates multiple scenarios; 3 default configurable.
- Execution after approval/policy; measure actual vs expected and learn.

### Погоджений напрям
- Powerful AI with human expert escalation.
- Consumes trusted facts; owns plans/hypotheses/campaign/content orchestration/performance learning.

### Синтетичне розширення для обговорення
- Scenario objects should include budget, channels, audience, assumptions, expected effect, risk and stop conditions.
- Can support content generation, but brand/compliance approval must be explicit.

### Відкриті рішення / невідомо
- Which ad platforms first.
- Autopublish authority thresholds.
- Media asset ownership boundary with Ops/Library.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- marketing plans
- campaign hypotheses
- content orchestration
- budget allocation proposal
- performance learning

**Не повинен owns:**
- CRM truth
- accounting truth
- product price
- identity

**Ключові залежності:**
- CRM
- Accounting
- Website
- Telegram
- Library
- Strategic Control Plane
- Identity

## 3. Розширений roadmap з мікрокроками

### R0 — Data/goal contract

- R0.1 Trusted source inventory.
- R0.2 Objective taxonomy.
- R0.3 Audience/segment inputs.
- R0.4 Budget constraints.
- R0.5 Brand/compliance rules.
- R0.6 Approval levels.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — Planning

- R1.1 Weekly plan.
- R1.2 Monthly plan.
- R1.3 Quarterly themes.
- R1.4 Three default scenarios.
- R1.5 Expected outcomes/risks.
- R1.6 Human expert escalation.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Campaign orchestration

- R2.1 Campaign object.
- R2.2 Channel tasks.
- R2.3 Content briefs/assets.
- R2.4 Schedule.
- R2.5 Budget guard.
- R2.6 Approval/publish workflow.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Attribution and learning

- R3.1 Lead/source events.
- R3.2 Conversion mapping.
- R3.3 Revenue/value projection.
- R3.4 Actual vs expected.
- R3.5 Stop/adjust rule.
- R3.6 Learn by campaign/segment/channel.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Advanced intelligence

- R4.1 Opportunity detection.
- R4.2 SCP research integration.
- R4.3 Experiment design.
- R4.4 Multi-model creative review.
- R4.5 Controlled autopublish for low-risk classes only.
- R4.6 Long-term strategy feedback without overriding Blueprint.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Маркетинг працює як measurable closed loop: plan -> approve -> execute -> attribute -> learn, з контрольованими AI actions.

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
