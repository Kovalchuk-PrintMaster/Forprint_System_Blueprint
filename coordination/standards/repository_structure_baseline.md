# Repository Structure Baseline

## Status

Target standard / gradual adoption

## Purpose

This document defines the preferred baseline repository structure for ForPrint modules.

It is a starting shape for new modules and a safe alignment target for existing modules.

It is not a command to immediately rewrite every existing project.

## Important adoption rule

This baseline must not be applied as a destructive or large refactor without explicit Blueprint approval.

Existing modules may keep their current structure if changing it would create unnecessary risk.

For existing modules, the expected first step is an alignment assessment:

```text
what already matches the baseline;
what can be safely improved now;
what should be deferred;
what module-specific structure should remain;
what questions need Blueprint decision.
```

For new modules, this baseline should be used as the preferred starting structure unless Blueprint approves a different shape.

## Minimal baseline for young modules

A young ForPrint module should normally start with:

```text
.
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
```

Not every directory needs many files at the beginning.

Empty directories may contain a short README.md or .gitkeep only when useful.

## Required coordination baseline

Every active module should gradually maintain:

```text
coordination/
├── README.md
├── blueprint_source.yaml
├── blueprint_awareness/
│   └── document_review_ledger.yaml
├── prompts/
│   ├── index.yaml
│   └── received/
├── reports/
│   ├── index.yaml
│   ├── completion/
│   └── commits/
└── status/
    ├── current_status.yaml
    ├── current_status.md
    └── next_questions_for_blueprint.md
```

Some early modules may not yet have all files.

Missing coordination files should be reported as gradual alignment work, not silently ignored.

## Common directory roles

app/

Main source code.

The internal package layout may differ by module.

config/

Non-secret configuration files.

Important rule:

paths, thresholds, repo URLs, timing rules and runtime options should live in config where practical.

Secrets must not be committed in config/.

coordination/

Live coordination status, prompts, reports, Blueprint awareness, roadmap alignment and questions.

docs/

Stable architecture and development documentation.

examples/

Safe sample inputs, outputs, fixtures, handoff examples and operator examples.

Examples must not contain private client data or real credentials.

reports/

Generated check reports and module status exports.

Tracked reports should be intentional source-of-truth artifacts only.

scripts/

Developer, operator, diagnostic, migration and report scripts.

Scripts should be grouped thematically as they grow.

tests/

Automated tests.

Small modules may start flat, but growing modules should move toward domain-level test folders.

## Runtime/local directories

Modules may also use local runtime directories:

```text
data/
logs/
tmp/
```

These directories are usually ignored by Git unless a file is explicitly intended as a safe fixture or documentation.

Do not commit private runtime data, logs with credentials, temporary files or local databases.

## Gradual alignment

Existing modules may differ.

Alignment should happen in small tested steps.

Do not break working modules only to match structure.

Large tree moves require:

explicit prompt or Blueprint approval;
tests before and after;
clear migration notes;
completion report entry.
## Non-goals

This baseline does not require:

identical internal architecture in every module;
the same framework in every module;
forced immediate refactoring;
deleting working project-specific structure;
moving production code without tests;
committing runtime data.
## Review rule

During module review, Blueprint may compare:

current module tree
vs.
this target baseline

The review should produce a safe alignment plan, not uncontrolled restructuring.
