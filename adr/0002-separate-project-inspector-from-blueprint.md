# ADR 0002: Separate Project Inspector from Blueprint

## Status

Accepted

## Context

Blueprint описує, як система має бути побудована. Inspector перевіряє, чи реальні модулі цьому відповідають.

## Decision

Не змішувати Blueprint і Inspector.

- `forprint_system_blueprint` — план і архітектурна правда.
- `forprint_project_inspector` — ревізор відповідності.

## Consequences

Blueprint залишається простим, прозорим і версіонованим. Inspector може розвиватися окремо.
