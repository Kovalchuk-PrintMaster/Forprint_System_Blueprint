# Deterministic machine discoverability

Мета — не “зробити код інтуїтивним конкретній AI-моделі”, а зробити кожен модуль детерміновано discoverable.

Fresh assistant має швидко знаходити:
purpose, owner, capabilities, entrypoints, commands, tests, contracts, procedures, dependencies, deprecated surfaces, roadmap/current work, authority.

Rollout:
- до inventory: описати standard v0.1, без mass-refactor;
- під час inventory: виміряти ambiguity/legibility debt;
- після inventory: затвердити v1;
- нові модулі: strict golden path;
- старі модулі: incremental `touch it, improve it`.

Не робити масове перейменування Telegram/Calculator до inventory.

Після завершення inventory final target capabilities кожного модуля класифікуються: `procedure_graph_required` або `NOT_REQUIRED + reason`. Додаткові operational graphs можуть існувати понад final capabilities.
