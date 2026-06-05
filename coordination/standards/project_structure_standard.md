# ForPrint Project Structure Standard

## Status

Target standard / gradual adoption

## Purpose

This document defines the preferred ForPrint module project structure.

The goal is to make all ForPrint modules easier to inspect, test, coordinate and maintain.

This standard is not a destructive refactor order. Existing modules should move toward this structure gradually and safely.

## Core principle

ForPrint modules should have a predictable project shape.

A developer, assistant or inspector should be able to quickly find:

```text
application code;
catalogs or local data fixtures;
contracts;
schemas;
coordination files;
architecture docs;
development docs;
reports;
scripts;
tests;
Makefile;
module manifest.
```

## Target project tree

Recommended module structure:

```text
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
├── contracts/
│   └── placeholders/
│
├── coordination/
│   ├── blueprint_source.yaml
│   ├── README.md
│   ├── prompts/
│   │   ├── index.yaml
│   │   └── received/
│   ├── reports/
│   │   ├── index.yaml
│   │   ├── completion/
│   │   └── commits/
│   └── status/
│       ├── current_status.yaml
│       ├── current_status.md
│       └── next_questions_for_blueprint.md
│
├── docs/
│   ├── architecture/
│   └── development/
│
├── examples/
│
├── reports/
│   ├── <module>_check_report.json
│   └── <module>_check_report.md
│
├── scripts/
│   ├── run_<module>_checks.py
│   ├── check_blueprint_instructions.py
│   └── sync_blueprint_directives.py
│
├── schemas/
│
├── tests/
│   ├── unit/
│   ├── contract/
│   └── integration/
│
├── pyproject.toml
├── Makefile
├── README.md
└── forprint_module_manifest.yaml
```

## Optional directories

Some modules may also need:

```text
catalog/
fixtures/
migrations/
static/
templates/
support/
tools/
```

These are allowed when they match the module purpose.

## Existing modules

Existing modules must not be broken to satisfy this structure.

Safe adoption rule:

```text
1. Inspect the existing tree.
2. Keep working code stable.
3. Add missing standard directories gradually.
4. Avoid large structural rewrites without Blueprint approval.
5. Document deviations in coordination/status/current_status.md or docs/architecture/.
```

## New modules

New modules should start with this standard unless Blueprint approves a different structure.

## Coordination directory

Every active module should eventually have:

```text
coordination/blueprint_source.yaml
coordination/prompts/index.yaml
coordination/prompts/received/
coordination/reports/index.yaml
coordination/reports/completion/
coordination/reports/commits/
coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/status/next_questions_for_blueprint.md
```

## Reports directory

Machine and human check reports should live under:

```text
reports/
```

Recommended names:

```text
reports/<module>_check_report.json
reports/<module>_check_report.md
```

## Tests directory

Preferred layout:

```text
tests/unit/
tests/contract/
tests/integration/
```

If a module is still small, a flat `tests/` layout is temporarily acceptable, but future growth should move toward the preferred structure.

## Configuration rule

Avoid hardcoded paths and constants.

Module-specific paths and settings should be stored in:

```text
config files;
environment variables;
coordination/blueprint_source.yaml;
Makefile variables.
```

## Non-goals

This standard does not require:

```text
identical internal architecture in every module;
the same framework in every module;
forced immediate refactoring;
deleting working project-specific structure;
moving production code without tests.
```

## Review rule

During module review, Blueprint may compare:

```text
current module tree
vs.
this target structure
```

The review should produce a safe alignment plan, not uncontrolled restructuring.
