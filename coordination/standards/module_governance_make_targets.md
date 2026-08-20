# Module Governance Make Targets

## Status

Target standard / gradual adoption

## Required target

Every active module should eventually provide:

```bash
make governance-check
```
## Expected governance-check behavior

Recommended implementation:

make blueprint-check
make blueprint-sync-directives
make module-policy-check
make coordination-check
make status-report
## Required standard targets

Active modules should eventually expose:

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
## Target meaning
check
  Runs core lint/tests/validation for the module.

check-report
  Produces readable terminal report and machine-readable JSON/Markdown reports.

status-report
  Prints or updates the current module coordination status.

coordination-sync-check
  Verifies Blueprint remote freshness with a network read-only check.

blueprint-check
  Verifies that required Blueprint paths, global policy, standards and module policy are readable.

blueprint-sync-directives
  Imports or acknowledges active Blueprint directives for the module.

coordination-check
  Validates module coordination metadata.

coordination-fix
  Safely fixes known coordination metadata issues without deleting module-specific blocks.

module-policy-check
  Checks module policy and local compliance.

governance-check
  Umbrella assistant-start/governance readiness command.
## Deferred implementation

If a target cannot be fully implemented yet, the module may print a clear deferred message.

It must not fake success for broken behavior.


---

## Outgoing prompt pull targets

Active modules that receive Blueprint-driven work prompts should also provide:

```text
make blueprint-prompts-list
make blueprint-prompt
```

These targets are defined by:

coordination/standards/module_outgoing_prompt_pull_protocol.md

They are part of the push-pull module coordination loop, but they are rolled out gradually and are not yet part of the base governance audit requirement for every module.

## Reporting closeout contract v0.1

The canonical module Make source is
`coordination/templates/module_makefile_standard.template.mk`.

Reporting targets follow these rules:

- `make check-report` is the compact operator-facing validation entrypoint.
- `make check-report-full` is the explicit extended-diagnostics entrypoint
  when a module has detailed terminal diagnostics.
- `make status-report` prints or exports current module status and must not
  silently change implementation state.
- `NO_COLOR=1` disables ANSI color without changing data, artifacts or exit
  codes.
- JSON and Markdown report artifacts remain the detailed evidence source when
  a module produces them.
- artifact paths and check results belong in the completion packet.
- `coordination-check` and `module-policy-check` are read-only.
- `coordination-fix`, module-local synchronization targets and composite
  workflows that invoke them may mutate documented module coordination state.
- `coordination-sync-check` is network read-only; retained `blueprint-pull`
  compatibility guards must fail closed without mutation.
- modules preserve existing target names and exit-code semantics.

The standard defines behavior, not implementation language. Modules are not
required to import the Blueprint Python reporting package.


## v0.4.1 coordination freshness command

`make coordination-sync-check` supersedes module-side Blueprint pulling.

It performs explicit network read-only freshness validation. Normal governance
checks remain local and network-independent. A retained `blueprint-pull`
compatibility target must fail closed and never mutate Blueprint.
