# FORPRINT • МОДУЛЬ 18/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## System Administration

**Робоча класифікація:** `CORE INFRASTRUCTURE / OFFLINE-FIRST REQUIREMENT`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Offline/local survivability is defining requirement.
- Central fleet control plus local autonomous workstation agent/toolkit.
- Fallback: local cache -> LAN/server repo -> internet/vendor.
- Inspector checks compliance; SysAdmin executes.

### Погоджений напрям
- Local emergency cache includes drivers/recovery tools/current profile/last-known-good/attached-device critical packages.
- Cloud Backup may later be absorbed; boundary open.

### Синтетичне розширення для обговорення
- Treat workstation profile as versioned desired state with phased rollout/rollback.
- Need least-privilege elevation broker and signed package metadata.

### Відкриті рішення / невідомо
- Agent technology/OS mix.
- Exact privileged action approval model.
- Separate Cloud Backup long-term.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- fleet desired state
- provisioning/repair execution
- package/preset rollout
- device diagnostics
- offline recovery toolkit

**Не повинен owns:**
- backup storage semantics if separate Backup module
- audit findings
- business app logic

**Ключові залежності:**
- Cloud Backup Manager
- Identity
- Project Inspector
- Library metadata
- workstations/network

## 3. Розширений roadmap з мікрокроками

### R0 — Fleet inventory

- R0.1 Discover devices.
- R0.2 Hardware/OS/software inventory.
- R0.3 Critical printer/device mapping.
- R0.4 Desired profile taxonomy.
- R0.5 Privilege model.
- R0.6 Offline survival requirements.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — Local agent/toolkit

- R1.1 Health/status collection.
- R1.2 Package install/repair.
- R1.3 Driver management.
- R1.4 Printer/preset configuration.
- R1.5 Local emergency cache.
- R1.6 Audited privileged execution.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Central control

- R2.1 Fleet desired state.
- R2.2 Drift detection.
- R2.3 Staged rollout.
- R2.4 Rollback.
- R2.5 Version pinning.
- R2.6 Maintenance windows.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Offline/LAN resilience

- R3.1 LAN package repo.
- R3.2 Last-known-good profiles.
- R3.3 Recovery media/tools.
- R3.4 Network/device diagnostics.
- R3.5 Fallback source ordering.
- R3.6 Offline repair drill.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Backup/distribution boundary

- R4.1 Integrate Cloud Backup artifacts.
- R4.2 Fonts/presets/packages.
- R4.3 Integrity/signing.
- R4.4 Retention/rollback.
- R4.5 Decide module absorption.
- R4.6 Inspector compliance recheck.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Робочі станції можна provision/repair/restore навіть при проблемах мережі; rollout контрольований, reversible і auditable.

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
