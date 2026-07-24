# ForPrint Module Make Target Contract

Status: draft v0.1
Created: `2026-06-12T14:33:44.165569+00:00`

## Purpose

This standard defines canonical Make targets that active ForPrint modules should expose.

The goal is to make module assistants predictable. A module assistant should not invent unique command names for the same governance actions.

## Required baseline targets

```text
make blueprint-pull
make blueprint-check
make blueprint-sync-directives
make blueprint-prompts-list
make blueprint-prompt
make blueprint-prompt-check

make coordination-check
make coordination-fix
make coordination-records-refresh
make coordination-records-check

make prompt-completion-apply REPORT=<path>
make prompt-completion-check

make module-policy-check
make governance-check
make check
make check-report
make status-report

Target meaning
make blueprint-pull

Updates the local ForPrint System Blueprint checkout.

Expected default implementation:

git -C /srv/software_development/forprint-project/forprint_system_blueprint pull --ff-only
make blueprint-prompts-list

Lists outgoing Blueprint prompts for the current module.

make blueprint-prompt

Prints the active ready_for_module_pull prompt for the current module.

make blueprint-prompt-check

Validates that the module can read its outgoing prompt index and active prompt file.

make coordination-records-refresh

Refreshes machine-readable module coordination records.

make coordination-records-check

Validates machine-readable module coordination records.

make prompt-completion-apply REPORT=<path>

Reads a completion report with YAML frontmatter and updates related coordination files.

make prompt-completion-check

Validates that completion report, status, prompts index and reports index are consistent.

Rule

Module-specific extra targets are allowed, but the canonical targets above must keep the same names and basic meaning across all active ForPrint modules.

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
