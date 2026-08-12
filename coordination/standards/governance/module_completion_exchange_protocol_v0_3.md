# ForPrint Module Completion Exchange Protocol v0.3

Status: candidate for reference validation
Revision: `v0.3`
Updated: `2026-08-12`

## Purpose

This document defines the candidate next ForPrint contract for issuing module work and receiving completion evidence. It is designed so Blueprint can determine, without manual prose interpretation, what was required, what the module claims was completed, which implementation/test artifacts support each requirement, which commands were required, which commands passed, what Git range belongs to the work, and whether the evidence is safe enough to reach operator review.

`READY_FOR_OPERATOR_REVIEW` is never `ACCEPTED`. Acceptance and return remain explicit operator decisions.

The authoritative revision state is:

```text
coordination/revisions/current.yaml
```

During reference validation, v0.2 remains operational current and v0.3 may be exercised only with the explicit read-only candidate-reference flag.

## Design principles

1. One operational current revision.
2. A candidate revision may exist only for bounded reference validation.
3. Historical revisions are recognized for migration/forensics, not maintained as parallel normal runtime interfaces.
4. Historical completion/review evidence is immutable.
5. New prompt and completion revisions explicitly supersede prior revisions.
6. Revision upgrades are normal project evolution.
7. Every functional or behavioral requirement must have test evidence.
8. Documentation/architecture requirements must have artifact evidence.
9. Safety requirements must have explicit machine-readable boundary confirmations.
10. Required commands must be identified in the prompt contract and answered one-for-one in the completion packet.
11. The implementation work is a Git range, not one isolated commit.
12. Blueprint intake is read-only toward the module repository.
13. Module completion is distinct from Blueprint review and acceptance.

## End-to-end flow

```text
Blueprint human-readable prompt
        +
module_prompt_contract_v0_3
        ↓
module executes requirement IDs
        ↓
module tests functional/behavioral requirements
        ↓
module runs required check IDs
        ↓
module_completion_packet_v0_3
        +
completion report frontmatter
        ↓
Blueprint read-only intake
        ↓
schema/protocol
safety
Blueprint control state
Git publication
prompt source binding
implementation range
requirement coverage
test/artifact evidence
required check coverage
packet/report consistency
superseding chain
        ↓
REFERENCE_VALIDATION_READY (candidate only)
or
READY_FOR_OPERATOR_REVIEW (after v0.3 promotion)
        ↓
explicit operator ACCEPT / RETURN / KEEP_PENDING
```

## Prompt contract

The canonical machine-readable prompt contract lives at:

```text
coordination/prompt_contracts/<module_id>/<prompt_id>.yaml
```

Required top-level fields:

```yaml
schema_version: module_prompt_contract_v0_3
contract_id: ...
module_id: ...
prompt_id: ...
phase: ...
source_prompt:
  path: ...
  sha256: ...
implementation_base_commit: <40-char SHA>
requirements: []
required_checks: []
```

The source prompt hash prevents a contract from silently drifting away from the approved human-readable prompt.

### Requirement IDs

Every required unit of work has a stable ID.

Supported candidate evidence policies:

```text
paths_and_tests
artifacts
boundary
```

`paths_and_tests` requires both implementation and test paths. Unless explicitly disabled by the contract, at least one supplied evidence path must be changed inside the implementation range.

`artifacts` requires committed artifact paths, normally documentation, architecture, runbook, recovery, schema, or other non-runtime deliverables.

`boundary` requires explicit `boundary_confirmation` flags in the completion packet.

A requirement result cannot be inferred from prose. It must appear in `requirement_results`.

## Required check IDs

Every command that Blueprint requires must have an ID and exact command string:

```yaml
required_checks:
  - id: CHECK-001
    command: make check
```

The completion packet responds:

```yaml
check_results:
  - check_id: CHECK-001
    command: make check
    status: passed
```

A missing check ID, command mismatch, or failed status blocks intake.

Additional module-local checks may be reported, but they do not substitute for required check IDs.

## Implementation range

v0.3 replaces the ambiguous single implementation SHA with:

```yaml
implementation_range:
  base_commit: <40-char SHA>
  tip_commit: <40-char SHA>
```

The base is defined by the prompt contract. Usually it is the accepted dependency/foundation tip from which the task starts.

Blueprint verifies:

```text
base exists
tip exists
base is ancestor of tip
tip is ancestor of completion commit
requirement evidence paths exist at tip
required changed-path evidence belongs to base..tip
```

The publication/completion commit remains external CLI evidence because a commit cannot recursively contain its own final hash.

## Completion packet v0.3

Required control fields include the existing module/prompt/report identity fields plus:

```yaml
schema_version: module_completion_packet_v0_3
protocol_version: blueprint_completion_intake_v0_3

prompt_contract:
  contract_id: ...
  revision: module_prompt_contract_v0_3
  source_prompt_sha256: ...

implementation_range:
  base_commit: ...
  tip_commit: ...

requirement_results:
  - requirement_id: ...
    status: completed
    implementation_paths: []
    test_paths: []

check_results:
  - check_id: ...
    command: ...
    status: passed
```

`implemented` and the old free-form check map are not canonical proof in v0.3. They may exist as human summaries, but Blueprint readiness is determined from `requirement_results` and `check_results`.

## Completion report consistency

The completion report must start with YAML frontmatter and repeat the control facts that a reviewer needs to bind prose to the packet:

```yaml
schema_version: module_completion_packet_v0_3
protocol_version: blueprint_completion_intake_v0_3
prompt_contract_id: ...
prompt_id: ...
target_module: ...
phase: ...
implementation_base_commit: ...
implementation_tip_commit: ...
```

Blueprint verifies these values against the packet and prompt contract.

Human-readable report sections remain useful for explanation, but they do not replace machine-readable evidence.

## Superseding evidence

When a new completion packet revises historical evidence it must provide all of:

```yaml
supersedes_completion_id: ...
supersedes_packet_path: coordination/completion_packets/records/...
revision_reason: ...
```

Blueprint resolves the referenced committed packet and verifies that its `completion_id` matches.

Historical packets are never rewritten.

## Current outputs

Every v0.3 `current_outputs` entry must be a repository-relative committed path at the supplied completion commit.

Temporary diagnostics under ignored paths are not completion outputs.

## Candidate activation gate

Until v0.3 is promoted in `coordination/revisions/current.yaml`, normal acceptance must not use it.

Read-only reference validation is explicit:

```text
completion_intake_check.py ... --allow-candidate-reference
```

A green candidate result is:

```text
REFERENCE_VALIDATION_READY
```

It does not authorize acceptance.

Promotion requires a green Tracking Events reference run, documentation review, and a separate operator-approved Blueprint promotion slice.

## Revision evolution

A future v0.4/v0.5 is expected.

For every breaking revision:

1. record the new revision in `coordination/revisions/history.yaml`;
2. identify what it supersedes;
3. document breaking changes;
4. define migration instructions;
5. audit active consumers before retirement;
6. promote exactly one operational current revision;
7. classify prior revisions as migration/reference only when safe.

Do not preserve old behavior in the normal runtime path merely because an old artifact exists.

## Reference implementation

The first v0.3 reference prompt contract is:

```text
coordination/prompt_contracts/logistics_service/logistics_service_tracking_events_v0_1.yaml
```

Tracking Events must not be accepted from v0.3 until the candidate reference run reaches `REFERENCE_VALIDATION_READY` and the revision is separately promoted.
