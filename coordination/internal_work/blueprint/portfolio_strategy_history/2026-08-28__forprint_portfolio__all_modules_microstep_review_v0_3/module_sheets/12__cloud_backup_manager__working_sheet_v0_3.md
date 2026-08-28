# FORPRINT • МОДУЛЬ 12/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## Cloud Backup Manager

**Робоча класифікація:** `EXISTING SEPARATE PROJECT / NEAR FUNCTIONAL TESTING`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Existing separate project nearing functional testing/final state; absorb/adopt only after explicit owner go-ahead.
- Backup sources/DB/config/installers/apps/cloud/FTP; mirror/distribution/sync workstation environment.
- Fonts central directory and redistribution, printer presets master workstation, software package drift/update.

### Погоджений напрям
- System Administration owns policy/control; Backup stores/versions/replicates/distributes.
- Potential future absorption into System Administration remains open.

### Синтетичне розширення для обговорення
- Treat artifact distribution and backup/recovery as distinct capabilities even if same implementation package.
- Need restore drills, integrity proofs and ransomware-safe/immutable recovery copies.

### Відкриті рішення / невідомо
- Separate module long-term vs System Administration submodule.
- Cloud providers/retention/RPO/RTO targets.
- How much software distribution should move to package repository.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- backup sets
- replication/versioning
- restore artifacts
- controlled distribution cache

**Не повинен owns:**
- fleet policy
- privilege/security policy
- canonical semantic definitions

**Ключові залежності:**
- System Administration
- Library metadata
- Identity
- workstations/storage/cloud

## 3. Розширений roadmap з мікрокроками

### R0 — Existing-project acceptance

- R0.1 Freeze current target scope.
- R0.2 Run functional tests.
- R0.3 Validate backup integrity.
- R0.4 Validate restore path.
- R0.5 Document known gaps.
- R0.6 Explicit owner go-ahead before Blueprint integration.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — Backup baseline

- R1.1 Source inventory.
- R1.2 Retention/version rules.
- R1.3 Encryption/credentials.
- R1.4 Integrity hashes.
- R1.5 Scheduled backup.
- R1.6 Failure alerting.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Recovery

- R2.1 File restore.
- R2.2 DB restore.
- R2.3 Workstation configuration restore.
- R2.4 Bare-minimum emergency kit.
- R2.5 RPO/RTO measurement.
- R2.6 Periodic restore drill.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Controlled distribution

- R3.1 Font inventory/distribution.
- R3.2 Printer preset master/versioning.
- R3.3 Software installers/packages.
- R3.4 Drift detection feed to SysAdmin.
- R3.5 Offline/LAN cache.
- R3.6 Rollback.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Module disposition

- R4.1 Compare overlap with SysAdmin.
- R4.2 Keep storage engine separable.
- R4.3 Decide separate service vs absorbed capability.
- R4.4 Preserve APIs/contracts.
- R4.5 Security review.
- R4.6 Long-term maintenance ownership.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Critical environment can be restored reproducibly; artifacts/fonts/presets/packages are versioned and distributable without becoming an uncontrolled admin plane.

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
