# Blueprint Module Governance Terminal/Artifact Split v0.1

## Date

2026-07-16

## Purpose

Separate compact operator-facing terminal output from detailed governance
artifacts without changing governance decisions or artifact schemas.

## Baseline

```text
target: scripts/audit_module_governance.py
modules checked: 14
OK: 6
NEEDS_ALIGNMENT: 6
WARN: 2
DEFERRED: 0
exit code: 0
stderr: empty
```

## Artifact contracts

JSON top-level key order:

```text
generated_at
source_file
required_files
required_targets
summary
modules
```

Summary key order:

```text
OK
NEEDS_ALIGNMENT
WARN
DEFERRED
```

Markdown heading order:

```text
# ForPrint Module Governance Audit
## Summary
## Required files
## Required Makefile targets
## Module results
```

## Implementation boundary

Changed:

```text
terminal rendering
reporting consolidation registry
terminal regression tests
architecture/runbook/recovery documentation
```

Unchanged:

```text
ModuleAuditResult
module discovery
module auditing
summary calculation
JSON writer
Markdown writer
artifact filenames
CLI flags
exit codes
Makefile targets
```

## Verification rule

Timestamps are normalized before byte comparison because each writer creates
its own current UTC timestamp.

## Next implementation front

```text
blueprint_reporting_consolidation_closeout_v0_1
```
