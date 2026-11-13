# Anomalies & Open Loops

## Anomalies

### ANOM-BP0508C-0001 — continuation_not_duplicate (normal)
This export is not a duplicate of the previously processed 05.08 source. It has 87 retained containers / 86 text-bearing turns, different message/turn IDs, and begins from the prior package's final mutation-builder/transparency checkpoint.

### ANOM-BP0508C-0002 — assistant_capture_gap (high)
Only three assistant message blocks survive. Most middle execution history is represented through user-pasted outputs and archive names.

### ANOM-BP0508C-0003 — temporary_repository_sync_cost (high)
Parallel work through synchronized temporary repository copies created enough repeated synchronization cost/confusion that owner explicitly prefers normal Git branch/worktree isolation.

### ANOM-BP0508C-0004 — completion_chain_not_closed (critical)
Owner explicitly says the completion/publication chain is still not working end to end before the v0.4 redesign.

### ANOM-BP0508C-0005 — roadmap_prompt_reality_drift (critical)
Owner reports roadmap, prompt state and actual implementation can be far out of sync, including roadmap remaining on old phases while implementation moved ahead.

### ANOM-BP0508C-0006 — automatic_acceptance_ambiguity (critical)
Owner explores automatic acceptance after deterministic checks but does not fully settle authority mechanics here. Later governance must distinguish evidence automation from acceptance authority.

### ANOM-BP0508C-0007 — website_scope_contamination (normal)
Website/mobile UI and hosting work appears inside the Blueprint continuation without clear ownership linkage to the governance workfront.

### ANOM-BP0508C-0008 — seal_worktree_precondition_conflict (high)
STEP26 seal builder expects a clean worktree but the exact two intended seal paths are already dirty; first attempt fails even though later read-only verification recognizes the existing seal state as valid.

### ANOM-BP0508C-0009 — historical_step_state_not_current_proof (normal)
STEP20/STEP26/STEP27 outputs are historical execution evidence and must not be treated as current release state without present-day repository verification.

## Open loops

### LOOP-BP0508C-0001
Verify current transparency control layer and Make command model.
**Last known:** This continuation begins by implementing/inspecting transparency after the prior mutation-builder checkpoint.
**Verify:** Inspect current status/transparency command, Make targets and canonical authority.

### LOOP-BP0508C-0002
Verify temp-repo synchronization was retired in favor of normal Git branch/worktree isolation.
**Last known:** Owner explicitly wanted the synchronized temporary repository removed after reconciliation.
**Verify:** Inspect current development workflow and worktree policy.

### LOOP-BP0508C-0003
Verify completion-intake/report contract and test-evidence schema.
**Last known:** Tracking Events was used as a reference case while intake hardening and standards reconciliation were underway.
**Verify:** Audit current prompt contract, completion packet/outbox, intake validator and Acceptance Oracle.

### LOOP-BP0508C-0004
Verify v0.4 planning-buffer rules and roadmap/prompt synchronization.
**Last known:** Owner set 5–8 roadmap steps and 2 draft prompts as desired minimums/warnings.
**Verify:** Inspect current roadmap standards, prompt queue health rules and generated status outputs.

### LOOP-BP0508C-0005
Verify the closed-loop completion→acceptance→roadmap→next-prompt architecture.
**Last known:** v0.4 was explicitly designed to close the loop; exact acceptance authority remained an unresolved governance detail here.
**Verify:** Run a current end-to-end module cycle and inspect operator/manual boundaries.

### LOOP-BP0508C-0006
Verify completed prompt archive lifecycle.
**Last known:** Owner required accepted prompts to leave approved/current surfaces in v0.4.
**Verify:** Inspect current prompt lifecycle directories, archive transition and validators.

### LOOP-BP0508C-0007
Determine ownership of the website/UI side branch before any promotion.
**Last known:** Website/mobile UI work appears inside this Blueprint source, but no clear Blueprint governance ownership is established.
**Verify:** Resolve against Website module history/current roadmap; do not promote from this dialogue alone.

### LOOP-BP0508C-0008
Verify STEP26 manual seal completion and historical transition into STEP27.
**Last known:** Source ends with existing seal state valid, STEP27 active/ready_for_module_pull, and seal commit pending.
**Verify:** Cross-check the later 17.08 dialogue and current release history; do not infer present-day state.

### LOOP-BP0508C-0009
Verify global v0.4 promotion remained a separate explicit decision.
**Last known:** End of source explicitly says global v0.4 promotion was not performed.
**Verify:** Inspect later promotion records/ADRs/releases and current release authority.
