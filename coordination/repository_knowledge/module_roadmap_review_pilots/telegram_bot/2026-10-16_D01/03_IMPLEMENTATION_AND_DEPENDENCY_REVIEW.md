# Telegram — єдиний огляд від реалізації до кінцевої цілі

**Статус:** тематична зводка D01; деталі кожного TG-RB-XXX у незмінному R010 r004 reference, не копіювати вручну 52 пакети сюди.

## 1. Початкова реальність

- З L0: 42 можливості; 30 мають сліди реалізації без повного approval, 12 — верифікаційні прогалини.
- 21 історичний roadmap-крок і 52 candidate work packages збережено без дублювання IDs; 9 фази TG-R0…TG-R8, 17 логічних dependency layers.
- Локальний SQLite/ORDER handoff, audit, scoped memory мають різні рівні підтвердження. R032–R038 — дослідницькі кандидати, НЕ approved production changes.
- Legacy: direct Supabase business data writes, альтернативні entrypoints, 223 Python шляхи поза L0; це кандидати на архітектурну класифікацію, НЕ автоматично 223 нові функції.
- На s01 не виявлено прив'язаного Telegram процесу у bounded R008; global deployment невідомий.

## 2. Функціональна ціль

Telegram — канал взаємодії, що збирає й уточнює typed requests, тримає дозволений actor-scoped context, відправляє запити owner services через Gateway, повертає підтверджені відповіді, підтримує media/attachments і делегує людині, коли потрібно. Він не володіє master products, canonical customers, orders, pricing, payments, delivery execution.

## 3. Узгоджувані хвилі розвитку

| TG milestone | Розвиток / результат | Важливий обмежувач |
|---|---|---|
| R0 | історія → дійсні capabilities → концепція, legacy, roadmap crosswalk | 6 DFTB originals; owner D01 review |
| R1 | Identity, privacy, state, safe restart, CRM context | privacy/group policy; true actor proof |
| R2 | Intent/event taxonomy, entities, clarifications, classifier quality | Library/Gateway/contracts; dataset truth |
| R3 | Documents/images/audio intake і безпечна типізація | content storage/consent/PII/limits |
| R4 | Gateway→owner modules, order lifecycle/handoff, idempotency | provider owners and validated contracts |
| R5 | AI decision policy, confidence gates, safe fallback | security/reliable evaluation/budget authority |
| R6 | Human/operator communication, proactive messaging | consent and notification policies |
| R7 | Learning and personalization, monitored quality | validated independent training and governance |
| R8 | E2E, recovery/observability, controlled pilot, steady state | no evidence of active deployment; explicit approval |

Не всі фази послідовні: використовувати 17 dependency layers на рівні TG-RB-XXX, незалежні гілки можуть просуватися паралельно за умови готових контрактів.

## 4. Мінімальні умови «можна передавати розробниці»

- D01 owner choices мають ACCEPT/HOLD/REVISE та trace ID.
- TG-RB роботи описують deliverable, non-goals, owner, deps, tests/acceptance, rollback/privacy, proof and machine handoff.
- Критичні провайдери: `forprint_library`, `forprint_crm`, `forprint_integration_gateway`, `operations registry`, `calculator_engine`, `logistics_service`, `identity service` — тільки кандидатні взаємодії до контрактної перевірки.
- Жоден `SYNTHETIC_PROVISIONAL` не стане активним завданням без authorisation.
