# Anomalies & Open Loops

## Anomalies

### ANOM-BP1709-0001 — new_unique_blueprint_continuation_root (normal)
No shared message IDs with clean master v3.5 and no substantive sequence duplicate. Opening state explicitly continues the prior u180e/CF-05 checkpoint.

### ANOM-BP1709-0002 — attachment_heavy_sparse_export (critical)
110 visible message blocks contain only 12 substantive text-bearing blocks; most intermediate prompts/results are attachment placeholders, so exact CF-05→CF-09 step lineage is incomplete.

### ANOM-BP1709-0003 — execution_advanced_beyond_visible_closeout_evidence (high)
Roadmap later shows CF-05 previous / CF-06 current and eventually CF-09 ACTIVE, but many intermediate lifecycle events are only inside unavailable attachments.

### ANOM-BP1709-0004 — cf07_candidate_test_import_defect (high)
CF-07 S2 mirror lint fails on missing ROOT/Path names in candidate test material before canonical mutation.

### ANOM-BP1709-0005 — partial_apply_detected_after_planning_failure (critical)
Transition-strategy semantic repair fails state-aware while reporting canonical mutation true because prior planning apply may already have created the target file.

### ANOM-BP1709-0006 — operator_makefile_discoverability_debt (high)
Owner explicitly reports difficulty knowing command scope/meaning and requests a comprehensive readable Makefile command map.

### ANOM-BP1709-0007 — cf09_readiness_green_project_gate_red (critical)
Dispatcher requirement readiness is 9/9 with zero gaps while the project full closure boundary gate still fails.

### ANOM-BP1709-0008 — cross_module_check_surfaces_blueprint_generator_drift (critical)
A Library-scoped non-mutating check surfaces stale Blueprint generator_inventory.yaml during CF-09 closure, requiring dependency/isolation diagnosis.

### ANOM-BP1709-0009 — source_ends_before_recovery (critical)
Final assistant delivery times out after the red 0254 result; the recovery/closure outcome is absent.

## Open loops

### LOOP-BP1709-0001
Verify exact CF-05 and CF-06 checkpoint/validation/closure lineage.
**Last known:** Opening state is CF-05 ACTIVE; later morning summary shows CF-05 previous and CF-06 current.
**Verify:** Inspect current continuity event store and immutable historical events; do not infer closure solely from roadmap projection.

### LOOP-BP1709-0002
Recover/verify CF-07 and CF-08 exact progression hidden in attachment-only turns.
**Last known:** Visible CF-07 S2 safe-fails; later planning repair around CF-08/transition strategy shows possible partial apply.
**Verify:** Use repo event history, action/result artifacts and git lineage to reconstruct only the actual accepted/closed path.

### LOOP-BP1709-0003
Resolve CF-09 closure blocker and determine whether generator inventory drift is current-tree, isolation or cross-module dependency drift.
**Last known:** 0253 readiness 9/9, but 0254 full project gate fails on stale indexes/generator_inventory.yaml; CF-09 remains ACTIVE.
**Verify:** Start from current repo/HEAD/lifecycle/roadmap, run focused generator inventory check and inspect dependency/provenance before mutation.

### LOOP-BP1709-0004
Verify whether CF-09 was later closed and whether CF-10/internal worker pilot ever started.
**Last known:** Visible endpoint has CF-09 ACTIVE, CF-10 not started and worker dispatch false.
**Verify:** Resolve current continuity state and human boundary acceptance; never resume from 0254 blindly.

### LOOP-BP1709-0005
Make the Makefile command surface operator-readable and classify legacy targets.
**Last known:** Owner requests full descriptions/grouping and explicit semantics for ambiguous targets such as assistant-handoff-check.
**Verify:** Audit current Makefile against existing style/template authority and update comments/grouping without changing command semantics unless separately authorized.

### LOOP-BP1709-0006
Decide canonical provisioning for rg and other repeatedly required developer utilities.
**Last known:** Owner wants recurring missing-rg failures eliminated.
**Verify:** Check bootstrap/environment dependency manifests and provision via the canonical environment setup rather than ad hoc per-action installs.

### LOOP-BP1709-0007
Keep zero-stage internal worker launch behind Dispatcher/project closure and human boundary acceptance.
**Last known:** Historical plan explicitly keeps worker/CF-10 off while CF-09 closure is red.
**Verify:** Use current roadmap/approval authority; do not infer worker authorization from local Dispatcher readiness.
