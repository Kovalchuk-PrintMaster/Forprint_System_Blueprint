# Global Directive: Completion Intake and Acceptance Governance v0.1

## Directive ID

```text
2026-08-06__global__directive__completion-intake-and-acceptance-governance-v0-1
```

## Scope

```text
all_active_modules
```

## Status

```text
planned
```

## Priority

```text
p0
```

## Release state

```text
external_rollout: gated
module_acknowledgement_required_now: false
```

This directive is normative documentation but is not released to modules until
Blueprint records a separate activation decision.

## Purpose

Define one fail-closed, auditable protocol for module completion packets,
Blueprint intake, operator review, acceptance, return-for-fix and historical
evidence handling.

## Authority boundary

The module owns implementation code, module tests, completion reports,
completion packets, module Git history, branches, pushes and correction of
module-owned evidence.

Blueprint owns read-only intake, comparison with Blueprint control state,
findings, remediation instructions, review packets and presentation of the
decision to the project owner.

Blueprint must not repair, rewrite or commit module-owned code, packets, reports,
branches or coordination records.

## Required lifecycle

```text
module implementation
-> module-local tests and checks
-> module-side completion packet validation
-> module commit and push
-> Blueprint read-only intake
-> Blueprint evidence review
-> explicit operator decision
-> Blueprint review packet
-> Blueprint prompt and roadmap update
```

A green intake result means only `READY_FOR_OPERATOR_REVIEW`. It never means
`ACCEPTED`.

## Decision taxonomy

```text
READY_FOR_OPERATOR_REVIEW
ACCEPT
RETURN_WITH_FINDINGS
BLOCKED
INSUFFICIENT_EVIDENCE
HISTORICAL_ACCEPTANCE
HISTORICAL_EVIDENCE_UNRESOLVED
SUPERSEDED
```

`ACCEPT` requires an explicit processed Blueprint review record that identifies
the module, prompt, packet, report, implementation commit, completion commit,
decision date and acceptance evidence.

## Historical evidence policy

Historical completion packets and review records are immutable.

A historical packet is preserved as accepted only when an explicit processed
Blueprint review record exists and matches the packet identity and commits.

A historical packet without a matching processed review record must not be
silently upgraded to accepted. It is classified as
`HISTORICAL_EVIDENCE_UNRESOLVED`.

Current validators must not rewrite historical packets merely to satisfy a
newer schema. Historical reconciliation is a Blueprint evidence task unless the
project owner explicitly requests a module-side migration.

## Schema and protocol versioning

New and superseding packets must declare explicit versions:

```yaml
schema_version: module_completion_packet_v0_2
protocol_version: blueprint_completion_intake_v0_2
```

Validation rules must be selected by schema and protocol version. A current
validator must not apply new mandatory fields to accepted historical packets as
though they were new candidates.

## Superseding packet rule

A module must never overwrite or rewrite a published completion packet to fix
evidence. It must create a new packet:

```yaml
completion_id: <new-id>
supersedes_completion_id: <previous-id>
revision_reason: <reason>
schema_version: module_completion_packet_v0_2
protocol_version: blueprint_completion_intake_v0_2
```

The old packet and its Git history remain immutable.

## Boundary confirmation

New packets must carry machine-readable positive safety assertions required by
their declared schema:

```yaml
boundary_confirmation:
  no_production_api: true
  no_live_external_integrations: true
  no_real_1c_sync: true
  no_production_write: true
  no_automatic_posting: true
```

A module may set a flag to `true` only after verifying the implementation
actually preserves that boundary.

## Module-side validation contract

Before publishing a packet, a module should expose and run:

```text
make completion-packet-check PACKET=<path>
```

Required order:

```text
implementation tests
-> safety checks
-> completion report validation
-> completion packet validation
-> commit
-> push
-> Blueprint notification
```

## Commit identity rules

Packet and review records should use full 40-character Git commit IDs.
Comparisons must resolve identities through Git, such as `git rev-parse`,
rather than compare short and full SHA strings directly.

## Machine-readable intake findings

Completion intake should emit structured findings:

```yaml
result: failed
failure_class: protocol_compatibility
issues:
  - code: SAFETY_CONFIRMATION_MISSING
    field: boundary_confirmation.no_production_write
```

Until structured output is implemented, Blueprint must preserve raw checker
output and state that blocker classification is manual.

## Return-for-fix contract

`RETURN_WITH_FINDINGS` must identify the exact packet and completion commit,
every failed field, whether implementation code is implicated, module-owned
files that may require correction, required module-local checks, the
superseding-packet requirement and boundaries that remain gated.

Blueprint must not perform the correction itself.

## Dependency gate rule

A consumer module must not advance an integration dependency until the producer
contract has an explicit accepted review. Unrelated planning work may continue
under the consumer module's own authority.

## Release and automation boundaries

This directive does not authorize automatic acceptance, automatic return,
module repository writes by Blueprint, external prompt release, pilot
activation, production activity, commit, push or merge.

## Expected acknowledgement after activation

After a separate activation decision, each module should report:

```text
Completion Intake Governance Applied
```

with supported schema/protocol versions, module-side validation command,
superseding behavior, full-SHA behavior, structured blocker status, tests,
check-report evidence, commit, push status and deviations.
