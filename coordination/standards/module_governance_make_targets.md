# Module Governance Make Targets

## Status

Target standard / gradual adoption

## Required target

Every active module should eventually provide:

```bash
make governance-check
Expected governance-check behavior

Recommended implementation:

make blueprint-pull
make blueprint-check
make blueprint-sync-directives
make module-policy-check
make coordination-check
make status-report
Required standard targets

Active modules should eventually expose:

check
check-report
status-report
blueprint-pull
blueprint-check
blueprint-sync-directives
coordination-check
coordination-fix
module-policy-check
governance-check
Target meaning
check
  Runs core lint/tests/validation for the module.

check-report
  Produces readable terminal report and machine-readable JSON/Markdown reports.

status-report
  Prints or updates the current module coordination status.

blueprint-pull
  Pulls the current ForPrint System Blueprint repository.

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
Deferred implementation

If a target cannot be fully implemented yet, the module may print a clear deferred message.

It must not fake success for broken behavior.


---

## Outgoing prompt pull targets

Active modules that receive Blueprint-driven work prompts should also provide:

```text
make blueprint-prompts-list
make blueprint-prompt

These targets are defined by:

coordination/standards/module_outgoing_prompt_pull_protocol.md

They are part of the push-pull module coordination loop, but they are rolled out gradually and are not yet part of the base governance audit requirement for every module.

