# ForPrint Module Make Target Contract

Status: candidate v0.2 / new-module continuity reconciliation (2026-09-27)
Created: `2026-06-12T14:33:44.165569+00:00`

## Purpose

This standard defines canonical Make targets that active ForPrint modules should expose.

The goal is to make module assistants predictable. A module assistant should not invent unique command names for the same governance actions.


## Required baseline targets — v0.4.1

```text
make coordination-sync-check
make blueprint-check
make blueprint-sync-directives
make blueprint-prompts-list
make blueprint-prompts-check
make blueprint-prompts-sync
make prompt-notify
make prompt-next
make prompt-read-next

make coordination-check
make coordination-fix
make module-policy-check
make governance-check
make check
make check-report
make status-report

make assistant-handoff-check
make assistant-pack
make assistant-context-pack

make module-start
make module-sync
make module-validate
make module-finish
```

`coordination-sync-check` is the only standard network-read freshness gate.

`blueprint-pull` is removed from the canonical baseline. A module may retain a
fail-closed compatibility target, but it must never execute `git pull` or
`git fetch` against Blueprint.

`module-start` is freshness-gated and is the preferred prompt-driven entrypoint.

`check`, `governance-check`, and `module-validate` remain local and
network-independent.

## Reporting compatibility extension v0.1

The public target contract includes these reporting semantics:

- `check-report` - compact validation summary plus artifact references;
- `check-report-full` - explicit extended diagnostics where supported;
- `status-report` - current status visibility;
- `coordination-check` and `module-policy-check` - read-only checks;
- `coordination-fix` - explicitly mutating repair path.

`NO_COLOR=1` affects only ANSI presentation. It must not change artifacts,
schemas, warnings, failures or exit codes.

Modules keep implementation freedom behind these stable target contracts.

<!-- module-workflow-target-contract-v0-1:start -->

## Optional module workflow and self-knowledge targets

Modules may gradually adopt:

```text
module-workflow-list
module-workflow-check
module-self-audit
module-self-audit-resume
module-self-status
module-self-report-full
```

The target names remain stable. Implementation may be deferred until the module
has an approved workflow-control profile.

`module-self-audit` may create reports, temporary bundles and a generated
operator-input template. It must not stage, commit, push or write into another
module repository.

`module-self-audit-resume` must validate the exact request identity and input
schema before consuming external analysis.

<!-- module-workflow-target-contract-v0-1:end -->


## New-module assistant continuity extension — v0.2 candidate

For newly initialized ForPrint modules, the following targets are required from
the first usable bootstrap:

```text
make assistant-handoff-check
make assistant-pack
make assistant-context-pack
```

Existing modules may adopt them gradually.

### assistant-handoff-check

Read-only recovery gate. It verifies enough repository and live Blueprint
navigation state for a replacement assistant to establish:

```text
module identity;
Git branch / HEAD / worktree state;
module bootstrap navigation;
current status / reports / questions;
live Blueprint reading order and relevant policy;
module-policy availability when the module is registered.
```

It must not mutate Blueprint, Git state, runtime services or production data.

### assistant-pack

Builds an onboarding archive for the repository in which the command is run.

Semantic identity is mandatory:

```text
System Blueprint -> package_type: PROJECT_ONBOARD
module repository -> package_type: MODULE_ONBOARD
```

A module `MODULE_ONBOARD` package is authoritative only as a bounded snapshot of
module-local onboarding evidence. It does not become project-wide governance
authority.

The package must declare:

```text
package_type;
target module/scope;
purpose;
intended_use;
source Git state;
live Blueprint source references;
selection limits;
explicit zero execution/acceptance/release authority.
```

### assistant-context-pack

Builds a narrower `MODULE_CONTEXT` package. `TOPICS` or equivalent bounded
selectors may be supported. Large customer/production assets, secrets, caches,
virtualenvs and Git object data are excluded by default.

### Required repository navigation files

New modules should provide:

```text
AGENTS.md
coordination/bootstrap/START_HERE.md
coordination/bootstrap/module_bootstrap_manifest.yaml
```

`AGENTS.md` is a thin cross-agent entrypoint. It must route to the module
bootstrap document and live Blueprint sources instead of duplicating changing
governance text.

### Authority boundary

Assistant handoff/context packages are navigation/evidence. They never grant:

```text
execution authority;
dispatch authority;
Blueprint mutation authority;
roadmap mutation authority;
acceptance authority;
release authority;
cross-repository write authority.
```

### Makefile template requirement

`coordination/templates/module_makefile_standard.template.mk` must expose the
three continuity targets and a module-owned implementation entrypoint such as:

```text
scripts/coordination/module_assistant_context.py
```

When continuity target semantics change, the Make command standard, target
contract, template, implementation reference, tests and recovery documentation
must be reviewed together.
