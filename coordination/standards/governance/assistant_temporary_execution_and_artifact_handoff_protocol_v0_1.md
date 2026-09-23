# Assistant Temporary Execution and Artifact Handoff Protocol v0.1

<!-- unique-assistant-action-source-identity-v0-1:start -->
### Unique assistant action source identity

- every assistant-delivered operator-side action script must use a unique filename; do not reuse a fixed `tmp.py` filename for successive delivered actions because distinct action source/hash identity must remain visible;
- `tmp.py` may exist only as a volatile/local operator convenience alias and is never the durable identity of an assistant-delivered action;
- if an operator/runtime path starts an action through `tmp.py`, the action must first materialize and preserve an exact uniquely named source copy in the current `tmp/assistant_work/<horizon_id>/` append-only workspace, using the next `NNNN__` artifact prefix, before project mutation, then continue execution from that unique copy;
- reports and execution logs remain in the same bounded horizon workspace and existing numbered artifacts must never be silently overwritten.
<!-- unique-assistant-action-source-identity-v0-1:end -->


Status: active Blueprint operational standard
Owner: `forprint_system_blueprint`
Scope: Blueprint assistant/operator temporary execution, debugging artifacts and handoff evidence
Adopted: `2026-09-05`

## 1. Purpose

This protocol defines how a Blueprint AI assistant and the human operator exchange temporary
execution scripts, reports, diagnostics and bounded context artifacts without depending on shell
history or on preservation of the operator's volatile execution file.

It specializes the existing execution-workspace cleanliness/isolation rules. It does not widen
release, implementation, acceptance, commit, push or cross-repository write authority.

## 2. Volatile operator execution surface

The operator may copy an assistant-supplied script to a volatile repository-root file such as:

```text
tmp.py
```

`tmp.py` is an execution convenience only.

It is **not**:

- durable history;
- completion evidence;
- release authority;
- a canonical script registry;
- a source that a future assistant may assume still exists.

A fresh assistant must not require the operator to reconstruct old `tmp.py` contents or shell
history when a new bounded probe can re-establish the current state safely.

## 3. Mandatory self-recording for non-trivial assistant scripts

When an assistant will need execution evidence in the next turn, the supplied script MUST create
its own scoped session directory under:

```text
tmp/assistant_work/<work_id>/
```

The script MUST NOT depend on `tee` or terminal scrollback for its primary report.

Minimum session artifact:

```text
tmp/assistant_work/<work_id>/report.txt
```

When more than one artifact is relevant, the script SHOULD also create:

```text
tmp/assistant_work/<work_id>/manifest.json
tmp/assistant_work/<work_id>/handoff_bundle.zip
```

A debugging session may additionally contain:

```text
diagnostics/
artifacts/
snapshots/
```

These are temporary work products, not canonical project surfaces.

## 4. Exact return-artifact contract

At the end of a supplied script, machine-readable output MUST identify what the operator should
return to the assistant.

Preferred markers:

```text
SESSION_DIR=tmp/assistant_work/<work_id>
REPORT=tmp/assistant_work/<work_id>/report.txt
HANDOFF_BUNDLE=tmp/assistant_work/<work_id>/handoff_bundle.zip
NEXT_EXPECTED_UPLOAD=<exact path>
TEMP_SESSION_CLEANUP_ALLOWED=false
```

If no artifact is required, the script must state that explicitly.

The assistant's chat response that supplies the script must also name the expected return artifact.

## 5. Debugging isolation

When a debugging or repair cycle needs extra files, they MUST be copied or generated inside the
current scoped session directory rather than scattered through the repository or assumed to remain
in shell history.

A debug bundle should contain only the minimum evidence required to continue, for example:

- self-written report;
- relevant current configuration or source copies;
- bounded diffs;
- validator output;
- a manifest with paths and hashes.

Do not include secrets, `.env` files, credentials, private keys, production customer data,
virtual environments, VCS internals or unrelated repository content.

## 6. Durable history boundary

`tmp/` is not a historical archive.

If a result must survive after the current cycle, promote only the required summary/evidence into
an **existing appropriate durable document class** under the Blueprint taxonomy before cleanup.

Do not create a new durable document class merely to preserve every debug artifact.

Examples:

- governance decision -> existing governance decision surface;
- execution/review evidence -> existing report/review/evidence surface;
- active standard -> `coordination/standards/...`;
- derived navigation -> regenerated `indexes/...`.

Raw temporary diagnostics normally remain temporary.

## 7. Cleanup lifecycle

A session directory follows:

```text
ACTIVE
-> RETURNED_FOR_REVIEW
-> CLOSED
-> CLEANUP_ALLOWED
-> REMOVED
```

While a debugging/task cycle is unresolved:

```text
TEMP_SESSION_CLEANUP_ALLOWED=false
```

After the assistant and operator close the cycle and any required durable evidence has been
promoted:

```text
TEMP_SESSION_CLEANUP_ALLOWED=true
```

Cleanup must be scoped to the exact completed session directory.

No assistant/tool may run broad `rm -rf tmp`, repository `git clean`, automatic reset, stash or
other unrelated cleanup to manufacture cleanliness.

## 8. Safety and ownership

Temporary assistant artifacts:

- may be written only under the current repository's `tmp/` workspace;
- must not mutate another module repository;
- must not imply release/acceptance/commit/push authority;
- must not silently auto-fix project state during a read-only check;
- should be bounded by task/work ID to avoid cross-session collisions.

A mutation script may of course perform the explicit Blueprint mutation that the operator asked
for, but its diagnostics/handoff products still follow this protocol.

## 9. Front-door onboarding rule

`AGENTS.md` is the stable assistant entry point and MUST point to this protocol.

A fresh Blueprint assistant should therefore know immediately that:

1. `tmp.py` may be overwritten or absent;
2. missing temporary execution history is normal;
3. if evidence is needed, generate a new scoped session artifact;
4. non-trivial scripts must self-record the artifact needed for the next turn;
5. temporary session directories are removed after the work cycle is closed.

## 10. Relationship to existing architecture

This protocol complements, and does not replace:

- `coordination/standards/governance/assistant_bootstrap_governance_and_process_contract_direction_v0_1.md`;
- `coordination/standards/governance/module_prompt_execution_and_reporting_protocol.md`;
- `coordination/standards/governance/project_cleanliness_and_machine_surface_normalization_standard_v0_1.md`;
- `coordination/internal_work/blueprint/governance/2026-08-24__blueprint__execution_workspace_cleanliness_and_isolation_policy_clarification_v0_1.yaml`.

The existing `scripts/coordination/build_context_bundle.py` primitive remains available.
A future architecture discussion should evaluate how that primitive can evolve into a richer
task-aware/fresh-worker context bundle contract. This sentence records a discussion target only;
it does **not** authorize that implementation.

## 11. Adoption evidence

Human/operator adoption and the exact operating intent are preserved in:

`coordination/internal_work/blueprint/governance/2026-09-05__blueprint__assistant_temporary_execution_and_artifact_handoff_protocol_adoption_v0_1.yaml`

## 12. Semantic unique artifact naming and retention

Every user-facing temporary artifact generated for assistant/operator handoff MUST have a
semantic, unique, non-overwriting filename.

Generic primary filenames such as:

```text
report.txt
manifest.json
handoff_bundle.zip
archive.zip
output.txt
```

MUST NOT be used for newly generated handoff artifacts.

The filename MUST remain understandable when copied outside its original session directory.
At minimum it must encode:

```text
work/task identity
artifact role
state or stage when material
UTC timestamp or another collision-resistant unique identity
```

Preferred grammar:

```text
<work_id>__<task_slug>__<artifact_role>__<state_or_stage>__<utc_timestamp>.<ext>
```

Equivalent ordering is allowed when the same information remains obvious.

Examples:

```text
u128__semantic_unique_artifact_naming__pass_report__20260905T180000Z.txt
u128__semantic_unique_artifact_naming__pass_handoff__20260905T180000Z.zip
logistics_h10_bootstrap__fresh_context__candidate__20260905T180000Z.md
```

Artifact creation MUST be non-overwriting. If a target path already exists, the producer must
fail safely or generate a new collision-resistant identity; it must not silently replace the
older artifact.

A unique session directory alone is not sufficient justification for a generic archive name:
the archive/report/manifest itself should remain identifiable if the operator copies it to
another folder for later independent review.

Tree-preserving rollback backups and internal implementation files inside an already unique
session directory may retain source filenames when preserving the original relative path is
necessary for restoration. They are not handoff artifacts.

`CLEANUP_ALLOWED=true` means deletion is permitted, not required. The operator may retain a
closed session or its artifacts for later analysis. Retention by operator choice does not make
the temporary artifact canonical project authority.

When a retained temporary artifact matters to a later project decision, promote the required
conclusion/evidence into the appropriate durable Blueprint surface rather than treating the
retained ZIP/report as authority.

Adoption evidence for this naming extension:
`coordination/internal_work/blueprint/governance/2026-09-05__blueprint__semantic_unique_temporary_artifact_naming_policy_adoption_v0_1.yaml`

<!-- semantic-unique-artifact-naming-v0-1:start -->
## Semantic unique artifact naming and retention

Every user-facing temporary artifact generated for assistant/operator handoff MUST
have a semantic, unique, non-overwriting filename.

New primary handoff artifacts MUST NOT use generic names such as:

```text
report.txt
manifest.json
handoff_bundle.zip
archive.zip
output.txt
```

A filename must remain understandable even after the operator copies it outside
its original session directory.

At minimum encode:

```text
work/task identity
artifact role
state or stage when material
UTC timestamp or another collision-resistant identity
```

Preferred grammar:

```text
<work_id>__<task_slug>__<artifact_role>__<state_or_stage>__<utc_timestamp>.<ext>
```

Creation is non-overwriting. Existing artifacts must never be silently replaced.

`CLEANUP_ALLOWED=true` means deletion is permitted, not required. The operator may
retain a closed session or its artifacts for later independent analysis. Retained
temporary artifacts do not become canonical project authority.

Internal rollback backups may preserve original source filenames when exact
relative paths are required for restoration.
<!-- semantic-unique-artifact-naming-v0-1:end -->
