# Read first

Цей ZIP — не source of truth і не готовий patch. Це вхід для ранкового reconciliation.

Прийнятий порядок:
1. Дожати поточний Handoff/Assistant Pack v1 у нинішній архітектурі.
2. Звірити сьогоднішні домовленості з реальним Blueprint та roadmap-ами всіх зачеплених модулів.
3. Реалізувати Control Foundation: project laws, governed procedures, machine discoverability, rationale/history, horizon, review obligations, health/test tiers, cross-module rules.
4. Після accepted implementation фундаменту — Handoff v2.
5. Після цього — поетапний Blueprint AI Coordinator.

Ключове правило: **Handoff описує лише вже реалізовані й валідовані механізми; roadmap описує майбутні.**

Ранкова інтеграція повинна спочатку класифікувати кожну тему як `EXISTS / PARTIAL / MISSING / OBSOLETE / SUPERSEDED`, а не створювати дублікати.
