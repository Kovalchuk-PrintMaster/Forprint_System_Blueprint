# ForPrint Module Make Target Contract

Status: draft v0.1
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
