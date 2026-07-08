# Prompt: Library Reference Consumption Pilot v0.3

## Target module

`forprint_library`

## Prompt ID

`library_reference_consumption_pilot_v0_3`

## Purpose

Create a small, controlled reference consumption pilot that demonstrates how downstream ForPrint modules should consume Library reference contracts without making Library responsible for downstream runtime behavior.

The goal is to prove that Library references can be read, validated and used as stable semantic identifiers by consumers such as Calculator Engine, Telegram Bot, Operational Registry, Accounting Registry or Prepress Hub.

This prompt must not start Configurable Product Workbench yet.

## Current context

Library has completed and Blueprint accepted:

- Make-first semantic reference readiness v0.1;
- Reference contract foundation v0.2;
- Coordination foundation alignment v0.1.

The latest accepted Library-side completion commit is:

`d5ae83d Add Library coordination alignment commit report`

Library currently owns canonical catalog semantics, stable catalog IDs, aliases and contract definitions.

Library must not own clients, orders, payments, stock truth, production runtime, 1C synchronization, CRM workflow, Telegram runtime or Calculator logic.

## Required implementation

Add a small reference consumption pilot inside Library that shows how another module would safely consume Library reference contracts.

The pilot should be local, read-only and example-driven.

It should include:

1. one or more consumer fixture examples;
2. validation that referenced Library IDs exist;
3. validation that consumer payloads do not redefine Library-owned semantics;
4. clear distinction between:
   - Library-owned reference IDs;
   - consumer-owned runtime fields;
   - foreign module references;
5. human-readable preview output or documented example;
6. tests for valid and invalid consumer payloads.

## Suggested technical direction

Likely directories or files may include:

- `examples/reference_consumption/`
- `docs/contracts/reference_consumption_pilot.md`
- `schemas/reference_consumption/`
- `scripts/validate_reference_consumption_pilot.py`
- `tests/coordination/test_reference_consumption_pilot.py`

The assistant may choose better names if they fit the current Library structure.

## Consumer examples

At least one consumer example should be included.

Preferred examples:

- Calculator Engine consuming a Library product/material reference for pricing context;
- Telegram Bot consuming a Library product type reference as a channel-local hint;
- Operational Registry storing a Library reference as foreign-domain reference metadata.

The pilot must make clear that these are examples only.

Do not implement real cross-module integration.

## Boundaries

Library may define and validate reference semantics.

Library may provide schemas, examples and validation helpers.

Library must not:

- implement Calculator formulas;
- implement Telegram runtime behavior;
- implement Operational Registry storage;
- write to 1C;
- import production 1C data;
- create clients;
- create orders;
- mutate stock;
- calculate final price;
- start production runtime;
- expose live API unless explicitly approved by Blueprint.

## Required checks

The module assistant must run:

- `make check`
- `make check-report`
- `make governance-check`
- `make module-validate`
- `git diff --check`

The check report should include visibility for the new reference consumption pilot validation if a new validator is added.

## Required report

At completion, Library must report only inside its own repository.

Required module-side coordination outputs:

- `coordination/reports/completion/<report>.md`
- `coordination/reports/index.yaml`
- `coordination/status/current_status.yaml`
- `coordination/status/current_status.md`
- `coordination/status/next_questions_for_blueprint.md`

Use completion packet automation if available.

If completion packet automation is deferred in this module, the report must explicitly say so and must not fake successful packet application.

## Blueprint reporting boundary

Library may read Blueprint prompts and standards.

Library must not write directly into:

`/srv/software_development/forprint-project/forprint_system_blueprint/`

Blueprint-side incoming report registration and Blueprint review are separate Blueprint-owned actions.

## Explicit non-goals

Do not implement:

- Configurable Product Workbench;
- Business Card Skeleton;
- product modeling UI;
- production catalog database;
- live API;
- 1C import;
- 1C synchronization;
- Calculator integration;
- Telegram Bot integration;
- Operational Registry write;
- production write;
- price calculation;
- material write-off logic.

## Definition of done

The prompt is complete when:

- at least one reference consumption example exists;
- valid consumer payloads pass validation;
- invalid consumer payloads fail clearly;
- Library-owned and consumer-owned responsibilities are documented;
- no downstream runtime ownership is added;
- no forbidden integration is added;
- tests are green;
- check report is green;
- completion report is created in the Library repository;
- Library current status is updated in the Library repository.
