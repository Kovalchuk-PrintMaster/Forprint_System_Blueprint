# Anomalies & Open Loops

## Anomalies

### ANOM-BP2708-0001 — assistant_side_capture_gap (high)
All 72 retained turn containers contain text, but only four assistant narrative messages survive. Many middle decisions are represented only through owner instructions and pasted reports.

### ANOM-BP2708-0002 — stale_artifact_identity (high)
The owner encounters stale/old versions, and late in the dialogue v194 is executed instead of v195. Artifact identity/version selection is a recurring operational failure mode.

### ANOM-BP2708-0003 — global_clean_tree_incompatibility (critical)
A strict global clean-tree prerequisite conflicts with intended semi-automatic parallel, multi-module development and could block workers indefinitely.

### ANOM-BP2708-0004 — governance_rule_obsolescence (high)
Owner explicitly allows outdated rules to be revised/deprecated; validators that treat historical rules as immutable may block legitimate evolution.

### ANOM-BP2708-0005 — chat_only_history_risk (critical)
Owner says significant decisions/rationale must not remain only in chat; this MHTML itself illustrates the danger because most assistant reasoning is absent.

### ANOM-BP2708-0006 — progression_policy_change (high)
Owner changes progression semantics to manual gates only at major phase boundaries; older artifacts may still encode manual confirmation at every Q step and require supersession.

### ANOM-BP2708-0007 — ui_side_branch_scope_contamination (normal)
Product-editor/filter UI requirements appear inside Blueprint governance/hardening work without an explicit owning module in the preserved source.

### ANOM-BP2708-0008 — historical_phase_not_current_proof (normal)
B2/Q2/H10 transitions are historical evidence only and must not be treated as today's current phase without current release verification.

## Open loops

### LOOP-BP2708-0001
Verify current parallel-work / dirty-tree execution contract.
**Last known:** Owner requires bounded baseline/scope semantics instead of global clean-tree blocking.
**Verify:** Inspect current execution preflight, baseline identity, ownership and conflict/freshness guards.

### LOOP-BP2708-0002
Verify significant-decision/rationale capture as canonical closeout governance.
**Last known:** Owner made repository-local history/rationale mandatory.
**Verify:** Inspect current doctrine/ADRs/governance closeout records.

### LOOP-BP2708-0003
Verify current same-phase progression policy and supersession of old step-level approvals.
**Last known:** Owner changed policy to manual confirmation only at major phase boundaries.
**Verify:** Inspect current phase-boundary standard, release and validators.

### LOOP-BP2708-0004
Verify artifact/script identity safeguards.
**Last known:** Wrong/stale revisions were repeatedly selected.
**Verify:** Check unique script IDs, immutable filenames/hashes and pre-mutation guards.

### LOOP-BP2708-0005
Identify owner of the product-editor UI branch.
**Last known:** Concrete UI requirements agreed; owning module not explicit.
**Verify:** Search later dialogues/current UI repositories for matching screens/terms.

### LOOP-BP2708-0006
Verify Logistics-only pilot and expansion gate against current runtime.
**Last known:** Historical publication fixed Logistics as sole pilot with 2-run gate and separate expansion decision.
**Verify:** Inspect current release, pilot authority and actual automatic-run evidence.

### LOOP-BP2708-0007
Verify portfolio/Blueprint knowledge snapshots and self-analysis continuation.
**Last known:** Two knowledge snapshots were requested/produced; module snapshot was historically verified.
**Verify:** Locate current self-knowledge/repository-knowledge artifacts and roadmap integration.
