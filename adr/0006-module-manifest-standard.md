# ADR 0006: Standardize ForPrint Module Manifests

## Status

Accepted

## Context

ForPrint складається з багатьох окремих модулів. Blueprint описує очікувану архітектуру, але реальні модулі можуть поступово відхилятися від неї. Якщо кожен модуль описує себе у власному форматі, Project Inspector не зможе стабільно порівнювати план із фактичною реалізацією.

## Decision

Кожен ForPrint-модуль має отримати файл:

```text
forprint_module_manifest.yaml