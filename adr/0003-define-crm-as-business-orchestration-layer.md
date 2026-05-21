# ADR 0003: Define CRM as Business Orchestration Layer

## Status

Accepted

## Context

CRM не має перетворитися на фізичне сховище всієї правди. Його роль — бізнес-диригування, людський інтерфейс, аналітика і координація модулів.

## Decision

Визначити `forprint_crm` як business orchestration UI, а не як canonical registry для клієнтів, замовлень, матеріалів або бухгалтерії.

Операційні записи мають перейти в `forprint_operational_registry`, бухгалтерія — в `accounting_registry_service`, довідники — в `forprint_library`.

## Consequences

- CRM залишається гнучким диригентом.
- Дані мають чітких власників.
- Система легше масштабується і підключає нові модулі.
