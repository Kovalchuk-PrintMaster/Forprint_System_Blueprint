## Status

Target standard / gradual adoption

## Purpose

This document defines the preferred ForPrint module project structure.

The goal is to make all ForPrint modules easier to inspect, test, coordinate, migrate and maintain.

This standard is not a destructive refactor order.

Existing modules should move toward this structure gradually and safely.

## Core principle

ForPrint modules should have a predictable project shape.

A developer, assistant or inspector should be able to quickly find:

```text
application code;
configuration;
secrets documentation;
contracts;
schemas;
coordination records;
Blueprint awareness records;
roadmaps;
architecture docs;
development docs;
examples;
reports;
scripts;
tests;
Makefile;
module manifest.
Target project tree

Recommended module structure:

<module_root>/
├── app/
│   └── <python_package>/
│       ├── __init__.py
│       ├── domain/
│       ├── services/
│       ├── repositories/
│       ├── schemas/
│       └── config/
│
├── config/
│   ├── README.md
│   ├── defaults.yaml
│   ├── module.yaml
│   ├── environments/
│   ├── adapters/
│   ├── paths/
│   └── schemas/
│
├── coordination/
│   ├── README.md
│   ├── blueprint_source.yaml
│   ├── blueprint_awareness/
│   ├── prompts/
│   ├── reports/
│   ├── roadmaps/
│   └── status/
│
├── contracts/
├── docs/
│   ├── architecture/
│   └── development/
├── examples/
├── reports/
├── scripts/
├── tests/
├── Makefile
├── README.md
├── pyproject.toml
└── forprint_module_manifest.yaml

This is a target shape.

Young modules may start with fewer subdirectories.

Minimal young-module structure

A new lightweight module may start with:

<module_root>/
├── app/
├── config/
├── coordination/
├── docs/
├── examples/
├── reports/
├── scripts/
├── tests/
├── Makefile
├── README.md
├── pyproject.toml
└── forprint_module_manifest.yaml

The module should add deeper directories only when needed.

Top-level directory roles
app/

Main application code.

The internal layout depends on module purpose, but common folders include:

domain/
services/
repositories/
schemas/
adapters/
config/

Do not place operator scripts, reports or coordination records inside app/.

config/

Non-secret configuration.

Config should follow:

coordination/standards/configuration_policy.md
coordination/standards/secrets_and_env_policy.md

config/ may contain safe defaults, module identity, environment-specific non-secret settings, adapter config, path config and schemas.

config/ must not contain real secrets.

coordination/

Coordination state and Blueprint-facing records.

Expected areas include:

coordination/blueprint_source.yaml
coordination/blueprint_awareness/
coordination/prompts/
coordination/reports/
coordination/roadmaps/
coordination/status/

This directory is part of the operational development workflow.

It should stay readable and structured.

contracts/

Interface contracts, placeholder contracts, DTO examples and schema references shared with other modules.

Contracts must not pretend to be canonical ownership when they are placeholders.

docs/

Human-readable architecture, development and operation documentation.

Recommended subdirectories:

docs/architecture/
docs/development/
docs/operations/
examples/

Safe examples, fixtures, sample inputs, handoff examples and operator previews.

Examples must not contain real credentials or private client data.

reports/

Generated or exported reports.

Common files:

reports/<module>_check_report.json
reports/<module>_check_report.md
reports/<module>_module_status.json
reports/<module>_module_status.md

Generated local check reports may be ignored if they are not source-of-truth artifacts.

scripts/

Operator, developer, diagnostic, migration, preview and coordination scripts.

Scripts must be grouped thematically as they grow.

Recommended groups:

scripts/coordination/
scripts/diagnostics/
scripts/previews/
scripts/migrations/
scripts/adapters/
scripts/validation/

Do not let scripts/ become a dumping ground.

tests/

Automated tests.

Recommended layout for growing modules:

tests/unit/
tests/contract/
tests/in, caches, logs and temporary files.

Do not commit private data, local databases or runtime logs unless explicitly intended as safe fixtures.

## Optional directories

Some modules may also need:

```text
catalog/
fixtures/
migrations/
schemas/
static/
templates/
support/
tools/

These are allowed when they match the module purpose.

Avoid adding top-level directories without a clear role.

Directory growth rule

When a directory starts accumulating many unrelated files, create thematic subdirectories.

For new work, prefer one level of thematic grouping first.

Examples:

scripts/coordination/
scripts/diagnostics/
tests/coordination/
tests/config/

Avoid deep nesting unless there is a strong reason.

Do not reorganize old existing files unless the migration is explicitly planned.

Configuration rule

Avoid hardcoded paths and constants.

Module-specific paths and settings should be stored in:

config files;
environment variables;
coordination/blueprint_source.yaml;
Makefile variables.

Secrets must follow:

coordination/standards/secrets_and_env_policy.md
Makefile rule

Every module should gradually expose a structured Makefile based on:

coordination/standards/make_command_standard.md
coordination/templates/module_makefile_standard.template.mk

The Makefile is the operator control surface for the module.

New commands should be placed into the correct Makefile zone.

Existing modules

Existing modules must not be broken to satisfy this structure.

Safe adoption rule:

1. Inspect the existing tree.
2. Keep working code stable.
3. Add missing standard directories gradually.
4. Move files only in small tested steps.
5. Avoid large structural rewrites without Blueprint approval.
6. Document deviations in coordination/status/current_status.md or docs/architecture/.
New modules

New modules should start with this standard unless Blueprint approves a different structure.

A young module may start minimal, but should not invent unrelated names when standard names already exist.

Review rule

During module review, Blueprint may compare:

current module tree
vs.
this target structure

The review should produce a safe alignment plan, not uncontrolled restructuring.

Non-goals

This standard does not require:

identical internal architecture in every module;
the same framework in every module;
forced immediate refactoring;
deleting working project-specific structure;
moving production code without tests;
committing runtime data;
using every optional directory from day one.

---
