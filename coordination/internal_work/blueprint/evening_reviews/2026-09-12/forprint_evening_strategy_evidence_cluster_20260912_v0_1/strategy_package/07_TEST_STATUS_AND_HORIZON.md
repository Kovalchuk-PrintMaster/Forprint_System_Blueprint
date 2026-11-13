# Tests, status and Architecture Horizon

## Test tiers
- `check-local` — секунди;
- `check-affected` — обчислений dependency/validation impact;
- `check-core` — ширший integration gate;
- `make check` — повна system validation, семантика існуючої команди не змінюється.

Affected checks мають визначатися registry/dependency mapping, не інтуїцією assistant.

## Full Check Debt
Враховує elapsed time, accepted mutations, critical surfaces, fan-out, contract/core changes, wave/checkpoint/publication context. Може бути `GREEN/YELLOW/RED`.

## Operator surfaces
Machine commands non-interactive. Окремий control/dashboard може давати quick status, detailed status, affected/full checks, dependencies, horizon.

## Architecture / Capability Horizon
Окремо від roadmap. States candidate:
`WATCH / ASSESS / TRIAL / READY_FOR_DECISION / ADOPTED / REJECTED / SUPERSEDED`.

Кожен item має problem, current decision, why-not-now, candidate options, measurable reconsideration triggers, changed assumptions, provenance. Trigger означає `REVIEW_REQUIRED`, а не automatic adoption.

Перший кандидат: structured operational storage/read model. Не рішення “впровадити SQLite”, а критерії, коли file-based state треба переоцінити; derived SQLite read model можна оцінювати раніше, не роблячи DB canonical authority.
