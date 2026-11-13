# FORPRINT • МОДУЛЬ 22/22 • РОЗШИРЕНИЙ РОБОЧИЙ ЛИСТ
## ForPrint Identity & Access Service (ForPrint Account)

**Робоча класифікація:** `PROPOSED NEW CROSS-CUTTING MODULE`  
**Статус документа:** WORKING REVIEW / НЕ CANONICAL ROADMAP  
**Authority rule:** `coordination/releases/current.yaml` має перевагу над цим документом.

## 1. Що ми зараз знаємо

### Є в поточній картині / підтверджено джерелами
- Owner-agreed candidate for centralized identity/authentication/authorization across Website, Mobile, CRM, Operations Assistant, Telegram and internal tools.
- Identity = who; authentication = proof; authorization = what may do.
- Likely standards: OIDC/OAuth, WebAuthn/passkeys, MFA/OTP; no custom login protocol.
- Cross-Client-ID access is high-risk and deny-by-default.

### Погоджений напрям
- Known alternate contact alone is insufficient recovery unless previously bound/verified.
- Employees stricter than ordinary customers.
- Identity match does not imply cross-account authorization.

### Синтетичне розширення для обговорення
- Use canonical Person/Identity subject IDs and explicit account/context grants.
- Session/device inventory and audit should be first-class.
- Recovery must be multi-channel and risk-adaptive.

### Відкриті рішення / невідомо
- Identity provider implementation/build-vs-buy.
- Exact role/permission model for staff and business accounts.
- Legal/privacy retention requirements.

## 2. Ownership boundary

**Ймовірно/погоджено owns:**
- credentials/authentication
- sessions/tokens
- MFA/passkeys
- verified identifiers
- recovery
- role/access claims
- login audit

**Не повинен owns:**
- CRM business profile
- financial/client relationship truth
- cross-account business approval itself

**Ключові залежності:**
- CRM
- Website
- Mobile
- Telegram
- Operations Assistant
- System Administration
- all privileged modules

## 3. Розширений roadmap з мікрокроками

### R0 — Identity model and security policy

- R0.1 Subject/person identity model.
- R0.2 Client/account context model.
- R0.3 Verified contact identifiers.
- R0.4 Employee vs customer assurance levels.
- R0.5 Cross-Client-ID deny-by-default rule.
- R0.6 Threat/recovery model.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R1 — Authentication core

- R1.1 OIDC/OAuth provider/client topology.
- R1.2 Password/passkey strategy.
- R1.3 MFA/OTP.
- R1.4 Session/token lifecycle.
- R1.5 Device/session management.
- R1.6 Login audit/rate limiting.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R2 — Recovery/linking

- R2.1 Verified recovery channels.
- R2.2 Phone/email/Telegram binding.
- R2.3 Account recovery proof levels.
- R2.4 Linked identities.
- R2.5 Lost-device/session revocation.
- R2.6 Manual high-risk recovery.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R3 — Authorization

- R3.1 Roles/claims/scopes.
- R3.2 Per-Client-ID grants.
- R3.3 Multi-person organization access.
- R3.4 Employee privileged scopes.
- R3.5 Delegation/temporary access.
- R3.6 No implicit cross-account propagation.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R4 — Channel/service adoption

- R4.1 Website.
- R4.2 Mobile.
- R4.3 Telegram.
- R4.4 CRM/internal tools.
- R4.5 Operations Assistant.
- R4.6 Service-to-service identities.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

### R5 — Maturity

- R5.1 Security monitoring.
- R5.2 Key/secret rotation.
- R5.3 Access review.
- R5.4 Privacy/export/delete policy.
- R5.5 Incident response.
- R5.6 Pen-test/security audit before broad privileged automation.

**Питання вечірнього погодження:** що залишити / відкинути / перенести / додати?

## 4. Фінішна мета

Одна людина/службовий суб'єкт автентифікується через стандартний secure flow; кожен channel отримує explicit scoped authorization без небезпечного implicit account linking.

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
