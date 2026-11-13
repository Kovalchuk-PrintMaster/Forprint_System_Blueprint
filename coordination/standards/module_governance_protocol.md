# Module Governance Protocol v0.1

## Status

Active Blueprint standard / gradual adoption

## Purpose

ForPrint has multiple active modules and assistants. Every module assistant must work from the current Blueprint state, not from stale local memory.

This standard defines the mandatory module governance ritual:

1. Assistant start protocol.
2. Pre-commit protocol.
3. Post-commit report protocol.
4. Directive sync protocol.
5. Governance check target.

The goal is to prevent:

- stale architecture;
- missing active directives;
- lost reports;
- duplicated work;
- broken coordination metadata;
- silent module drift.

## Official protocol names

This standard explicitly defines the following official governance protocols:

```text
Module Assistant Start Protocol
Pre-commit protocol
Post-commit report protocol
Directive sync protocol
```

These names are intentionally stable because Blueprint tests and future module audits may reference them.

## Required module command

Every active module should eventually provide:

```bash
make governance-check
```

This is the umbrella command for module governance readiness.

It should check that the module has read current Blueprint rules, module policy, active directives, coordination metadata and local status/report files.

## Assistant start protocol

At the start of work inside any module, the assistant must check:

Current branch and git status.
Latest Blueprint pull.
Module policy from Blueprint.
Global standards from Blueprint.
Active directives for this module.
Local coordination status.
Reports index.
Prompts index.
Next questions for Blueprint.
Current module check-report.

Recommended command sequence:

make governance-check

If governance-check is not yet implemented, use the fallback sequence:

make blueprint-check
make blueprint-sync-directives
make module-policy-check
make coordination-check
make status-report

If some targets are not implemented yet, the module should clearly report DEFERRED or MISSING_NEEDS_ALIGNMENT.

It must not fake success.

## Pre-commit protocol

Before any module commit, the assistant must run:

make blueprint-check
make blueprint-sync-directives
make module-policy-check
make coordination-check
make check
make check-report
git status --short

If the module has preview targets, run the relevant previews too.

Examples:

make client-card-preview
make data-foundation-preview
make order-preview
make dictionary-preview
make dictionary-mapping-preview

A module must not commit if:

tests fail;
check-report fails;
coordination metadata fails;
active directives were not synced;
current_status.yaml is invalid;
coordination/reports/index.yaml has missing report_file;
accidental cache/generated garbage is present;
module-specific validation or boundaries blocks were deleted.
## Post-commit report protocol

After successful commit and push, the module should report:

Commit hash.
Push status.
Working tree status.
Test result.
Check-report result.
Coordination status/report update.
Open questions for Blueprint.
Recommended next step.

Blueprint should then collect the module coordination snapshot.

## Directive sync protocol

Every active module should support:

make blueprint-check
make blueprint-sync-directives

The module should check:

global Blueprint policies;
global standards;
module-specific policy;
global directives;
module-specific active directives.

Active directives must be imported or clearly reported as not imported.

Silent ignore is not allowed.

## Governance-check target

Recommended future module behavior:

make blueprint-check
make blueprint-sync-directives
make module-policy-check
make coordination-check
make status-report

governance-check may also run lightweight previews or local status reports if they are cheap.

It should not perform destructive actions.

It should not commit.

It should not push.

## Deferred modules

If a module is planned, deferred or not yet bootstrapped, Blueprint audit should report it as:

DEFERRED

not failed.

If a module is active but missing required governance files or targets, audit should report:

NEEDS_ALIGNMENT
## Required module files

Active modules should eventually have:

Makefile
forprint_module_manifest.yaml
coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/status/next_questions_for_blueprint.md
coordination/prompts/index.yaml
coordination/reports/index.yaml
## Required module Makefile targets

Active modules should eventually have:

check
check-report
status-report
coordination-sync-check
blueprint-check
blueprint-sync-directives
coordination-check
coordination-fix
module-policy-check
governance-check
## Current status extension rule

Blueprint tools must not rewrite coordination/status/current_status.yaml from scratch.

They may add or update required central keys, but must preserve module-specific blocks, including:

validation
boundaries
storage
client_account
module_specific
runtime
local_checks

This follows the Current Status Extension Policy.

## Boundary

This standard does not automatically edit all module repositories.

Module Makefile alignment must happen later through controlled module-by-module patches.

This standard only defines the protocol and enables central audit.


---


## v0.4.1 coordination freshness command

`make coordination-sync-check` supersedes module-side Blueprint pulling.

It performs explicit network read-only freshness validation. Normal governance
checks remain local and network-independent. A retained `blueprint-pull`
compatibility target must fail closed and never mutate Blueprint.
