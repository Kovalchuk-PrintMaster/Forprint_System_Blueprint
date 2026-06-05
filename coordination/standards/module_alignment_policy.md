# ForPrint Module Alignment Policy

## Status

Active policy / gradual adoption

## Purpose

This document defines how ForPrint modules should align with Blueprint standards.

Blueprint standards are meant to guide modules toward a common structure and workflow without breaking working code.

## Core principle

Alignment must be gradual, safe and test-backed.

Do not perform large structural rewrites only because a standard exists.

## What modules should read

Each module should gradually learn to read:

```text
coordination/global_policy/
coordination/standards/
coordination/module_policy/<module_id>/module_policy.md
coordination/directives/global/index.yaml
coordination/directives/modules/<module_id>/index.yaml
```

## What modules should report

When a module adopts Blueprint standards, it should report:

```text
what already matches;
what does not match yet;
what is intentionally different;
what can be safely changed now;
what should be deferred;
what requires Blueprint decision.
```

## Alignment categories

Recommended categories:

```text
aligned;
partially_aligned;
deferred_alignment;
intentional_deviation;
needs_blueprint_decision;
not_applicable.
```

## Standard adoption workflow

Recommended flow:

```text
1. Pull Blueprint.
2. Check Blueprint paths.
3. Sync active directives.
4. Read global policy.
5. Read module policy.
6. Read standards.
7. Compare current module state.
8. Make only safe, scoped changes.
9. Run tests.
10. Update coordination status and report.
11. Commit and push.
```

## Existing module rule

Existing modules may already have working structures.

They should not be forcefully reshaped.

Allowed approach:

```text
add missing coordination files;
add standard Makefile target wrappers;
keep existing internal implementation;
document deviations;
move structure gradually only when safe.
```

## New module rule

New modules should start closer to the standard structure.

They should include from the beginning:

```text
Makefile;
pyproject.toml;
README.md;
forprint_module_manifest.yaml;
coordination/;
docs/architecture/;
scripts/;
tests/;
reports/.
```

## Makefile alignment

All modules should gradually expose standard target names.

Implementation may remain module-specific.

Example:

```text
make check
```

can run different internal commands in different modules, but the external command should be stable.

## Test alignment

All modules should gradually support:

```text
make test;
make check;
make check-report.
```

Tests should cover the module's real current scope.

## Coordination alignment

All active modules should gradually support:

```text
make blueprint-pull;
make blueprint-check;
make blueprint-sync-directives;
make coordination-check;
make coordination-fix.
```

## Directive import rule

Blueprint pull and Blueprint check are not directive import.

The standard distinction is:

```text
blueprint-pull = update local Blueprint repository
blueprint-check = verify Blueprint paths
blueprint-sync-directives = import active module directives
```

Active module directives should be read from:

```text
module_directives.active
```

## Avoiding over-automation

Do not build large automation too early.

Manual or semi-manual review is acceptable while the project is still forming.

Prefer:

```text
small validators;
clear reports;
safe sync scripts;
explicit status files.
```

Avoid:

```text
large automatic refactors;
implicit hidden behavior;
silent cross-module mutation;
unreviewed production actions.
```

## Owner / Blueprint relationship

For now, high-level governance remains:

```text
owner / mentor
+
architectural assistant
+
ForPrint System Blueprint
```

ForPrint Strategic Control Plane is planned but deferred until core modules are alive enough.

## Deviation documentation

If a module cannot follow a standard, document it in one or more places:

```text
coordination/status/current_status.md;
coordination/status/next_questions_for_blueprint.md;
docs/architecture/<relevant_doc>.md;
completion report.
```

## Review rule

Blueprint should review modules using:

```text
module_policy;
module_docs_snapshots;
coordination status;
check reports;
repository tree;
tests;
Makefile targets.
```

The review should result in safe next actions, not uncontrolled rewrites.
