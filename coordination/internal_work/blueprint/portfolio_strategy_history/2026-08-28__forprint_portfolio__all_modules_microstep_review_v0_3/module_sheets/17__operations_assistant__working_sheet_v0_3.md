# FORPRINT • МОДУЛЬ 17/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## Operations Assistant

**Робоча класифікація:** `INTERNAL EMPLOYEE INTERFACE / PLANNED`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Universal employee work interface, role/access-aware.
- Equipment/material QR -> contextual menu/instructions/specs/schematics/video; QR is context pointer, never authorization.
- Library likely owns canonical instruction metadata/version; Ops Assistant consumes.

### Погоджений напрям
- Guided execution through owner modules; no hidden business authority.
- Multimodal search/RAG useful for procedures/forms.

### Синтетичне розширення для обговорення
- Could become task cockpit: scan context, identify task, show current procedure, execute bounded owner-module actions, record evidence.
- Offline cache should be read-limited and freshness-explicit.

### Відкриті рішення / невідомо
- Device form factors in production.
- How much action execution vs pure guidance in first release.
- Media hosting ownership.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- employee interaction context
- guided task UX
- contextual search
- bounded action orchestration
- execution evidence UI

**Не повинен owns:**
- authorization policy
- canonical instructions
- equipment runtime truth
- business decisions

**Ключові залежності:**
- Identity
- Library
- System Administration
- owner modules
- Design System

## 3. Розширений roadmap з мікрокроками

### R0 — Use-case inventory

- R0.1 Top operator tasks.
- R0.2 QR/context taxonomy.
- R0.3 Role/access needs.
- R0.4 Instruction sources.
- R0.5 Offline scenarios.
- R0.6 Evidence/confirmation needs.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — Context/search

- R1.1 QR scan.
- R1.2 Equipment/material lookup.
- R1.3 Library current instruction resolution.
- R1.4 Multimodal search.
- R1.5 Freshness warning.
- R1.6 Accessibility/large-button UI.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Guided execution

- R2.1 Step-by-step procedure.
- R2.2 Required confirmations.
- R2.3 Owner-module actions.
- R2.4 Exception/escalation.
- R2.5 Evidence/photo capture.
- R2.6 Resume interrupted task.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Offline/resilience

- R3.1 Current approved cache.
- R3.2 Stale-cache labeling.
- R3.3 Sync recovery.
- R3.4 No offline privileged action without policy.
- R3.5 Local device diagnostics link.
- R3.6 Emergency procedure bundle.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Learning and scale

- R4.1 Search success metrics.
- R4.2 Repeated confusion -> documentation improvement.
- R4.3 Task duration/error trends.
- R4.4 New procedure onboarding.
- R4.5 Multi-device support.
- R4.6 Inspector checks for stale instruction usage.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Працівник швидко отримує саме актуальну інструкцію/контекст і виконує дозволені дії з мінімумом пошуку та помилок.

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
