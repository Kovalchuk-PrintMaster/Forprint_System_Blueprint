# Anomalies & Open Loops

## Anomalies

### ANOM-CP0106-0001 — direct_owner_prompt_missing (critical)
The user turn contains only `Pasted text.txt Document`; all visible substantive requirements come from the assistant's summary/proposal. Direct owner evidence is unavailable.

### ANOM-CP0106-0002 — extremely_partial_capture (high)
Only two turns survive, with no implementation follow-up, tests, commits, owner acceptance or closure evidence.

### ANOM-CP0106-0003 — control_plane_vs_blueprint_authority_overlap (critical)
The proposal distinguishes strategy from architecture but simultaneously asks whether Control Plane should be the highest machine-readable governance layer above Blueprint, leaving authority ordering unresolved.

### ANOM-CP0106-0004 — historical_priority_snapshot_stale (critical)
Telegram/Calculator P0, Accounting P1, Operational/Gateway hold is an early proposed snapshot and conflicts with later project authority such as Logistics-only H10 and Control Foundation sequencing.

### ANOM-CP0106-0005 — inspector_status_consumption_boundary_unresolved (high)
The proposal does not decide whether Control Plane reads module status directly or receives Inspector-derived factual state, risking duplicate truth/monitoring responsibilities.

### ANOM-CP0106-0006 — proposed_machine_authority_without_acceptance (high)
Machine governance files and decision rights are detailed, but the source lacks owner approval or implementation evidence, so they remain historical proposals.

## Open loops

### LOOP-CP0106-0001
Determine whether ForPrint Control Plane/Strategic Control Plane exists in current architecture and what authority it has relative to Blueprint.
**Last known:** Only a bootstrap proposal survives; later Blueprint says Strategic Control Plane should be planned separately.
**Verify:** Resolve current release/module inventory/ADRs and classify Control Plane as implemented, renamed, superseded, deferred or absorbed.

### LOOP-CP0106-0002
Reconcile Control Plane vs Project Inspector factual-state responsibilities.
**Last known:** Direct module-status consumption vs Inspector-mediated state is unresolved.
**Verify:** Check current Inspector, Blueprint and any Control Plane contracts so factual truth has one clear source.

### LOOP-CP0106-0003
Reconcile historical strategic priority map with current roadmap authority.
**Last known:** Early proposal prioritized Telegram/Calculator and held Operational/Gateway; later roadmap authority changed materially.
**Verify:** Treat historical priority map as non-executable; use current release/roadmap only.

### LOOP-CP0106-0004
Determine whether strategic change→Blueprint update request interface exists or was superseded.
**Last known:** `blueprint_update_request.yaml` is only proposed.
**Verify:** Search current contracts/roadmaps/ADRs for a successor strategy-to-architecture change-request interface.

### LOOP-CP0106-0005
Determine whether autonomy levels/decision-rights/checkpoint protocol became current governance concepts.
**Last known:** Detailed v0.1 proposal exists but no direct owner acceptance survives.
**Verify:** Compare against later owner-checkpoint/manual-phase-boundary/Control Foundation authority rules; preserve only non-conflicting retained semantics.

### LOOP-CP0106-0006
Locate or supersede the missing bootstrap prompt attachment.
**Last known:** MHTML contains only the attachment placeholder.
**Verify:** Do not reconstruct from assistant summary unless a historical prompt artifact is later recovered; current architecture should be derived from live authority instead.
