# Deferred governance issue — non-roadmap maintenance work

Status: DEFERRED / NON-BLOCKING

## Context

During validation of the Assistant Bootstrap v0.2 / Living Knowledge
package integration, the package runtime and archive contracts passed,
but `module_continuity_transfer` rejected the changed
`build_assistant_handoff_archive.py` SHA because the current continuity
governance model requires an explicit owning work item for every change
to the validated transfer core.

## Diagnosis

- The package change is not a strategic roadmap-semantic change.
- It changes no roadmap source.
- It creates no lifecycle event.
- It changes no execution projection.
- The project currently has no dedicated non-roadmap maintenance/repair
  work lifecycle.
- Creating CF-21 solely to satisfy this maintenance bookkeeping would
  mix technical maintenance with the strategic Control Foundation roadmap.

## Decision for current work

Do not create CF-21.
Do not create u180j.
Do not bind or activate CF-10.
Do not block Assistant Bootstrap package validation.

Keep this issue for later architectural review. It may be handled either
by the primary Blueprint assistant or delegated to the future internal
Blueprint assistant after its controlled launch.

## Future question

Define whether Blueprint needs an explicit bounded maintenance/governance
repair work mechanism outside strategic roadmap steps, and then reconcile
the `module_continuity_transfer` current-core ownership contract with that
mechanism.
