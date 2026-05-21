# ADR 0001: Create ForPrint System Blueprint Layer

## Status

Accepted

## Context

ForPrint складається з багатьох модулів. Є ризик, що модулі окремо працюватимуть нормально, але разом не стикуватимуться.

## Decision

Створити окремий проєкт `forprint_system_blueprint`, який зберігає архітектурну правду у YAML/Markdown/Mermaid.

## Consequences

- У системи з'являється джерело правди для архітектури.
- Inspector зможе порівнювати реальні модулі з очікуваною архітектурою.
- Module guides можна генерувати з одного місця.
