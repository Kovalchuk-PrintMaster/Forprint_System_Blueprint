# Anomalies & Open Loops

## Anomalies

### ANOM-BP2109-0001 — new_unique_blueprint_continuation (normal)
No shared message IDs or exact substantive message-block overlap with clean master v3.6. The source continues after the 17.09 endpoint and adds new 18–20.09 state.

### ANOM-BP2109-0002 — attachment_heavy_sparse_export (critical)
114 visible message blocks contain 101 short attachment/archive placeholders; most intermediate action/result bodies are unavailable and are not reconstructed.

### ANOM-BP2109-0003 — prior_red_cf09_endpoint_later_seen_complete_without_visible_repair_lineage (critical)
17.09 ended with CF-09 ACTIVE and red project closure; this source later reports CF-07/08/09 complete and CF-10 READY_UNBOUND, but exact CF-09 recovery/closure events are hidden in attachments.

### ANOM-BP2109-0004 — packaging_scope_drift_toward_roadmap (critical)
Owner explicitly questions why assistant instruction/package work is entangled with roadmap reconstruction that was not part of the task.

### ANOM-BP2109-0005 — package_semantic_identity_mismatch (high)
A generated assistant-handoff package passes machinery but owner says it appears not to be the intended package.

### ANOM-BP2109-0006 — cf10_work_id_collision (critical)
Prospective u180j is already referenced while no allocator exists, so the assumed first CF-10 work_id cannot be bound safely without current authority.

### ANOM-BP2109-0007 — handoff_v2_stale_hardcoded_work_id (critical)
Handoff v2 runtime still hardcodes u180h after the system has progressed to CF-10 readiness, creating a launch-critical resume/binding defect.

### ANOM-BP2109-0008 — pass_label_not_launch_readiness (critical)
0172 returns PASS because the read-only audit completed correctly, while simultaneously reporting two blockers. PASS must not be interpreted as authorization to launch.

### ANOM-BP2109-0009 — unexpected_library_context_package (critical)
A `forprint_project_context__forprint_library__...zip` appears during Blueprint CF-10 preparation even though owner says Library work is not planned.

### ANOM-BP2109-0010 — source_ends_before_resolution (critical)
No visible response resolves the Library package question or the two CF-10 launch blockers.

## Open loops

### LOOP-BP2109-0001
Reconstruct exact CF-09 repair/checkpoint/closure lineage after the 17.09 red 0254 gate.
**Last known:** Later source says CF-07/08/09 dependencies complete and CF-10 READY_UNBOUND.
**Verify:** Use live continuity event store/Git artifacts; do not infer missing closure steps from assistant narrative.

### LOOP-BP2109-0002
Verify current project-constitution precedence and whether all active control-plane surfaces enforce it.
**Last known:** Historical check reports Constitution > Module Policy > Execution Profile > Work Front; lower layers may narrow only.
**Verify:** Run current constitution validator and inspect dispatcher/profile/work-front enforcement.

### LOOP-BP2109-0003
Resolve packaging/bootstrap boundary so knowledge publication never mutates roadmap accidentally.
**Last known:** Owner wants durable living-knowledge/assistant packages but explicitly rejects unintended roadmap redesign.
**Verify:** Classify each package builder's inputs/outputs/allowed mutations and bind generated artifacts to their canonical owner.

### LOOP-BP2109-0004
Design scalable roadmap/dependency rebuild for frequent large project changes.
**Last known:** Owner expects many future roadmap/dependency edits across modules and wants conflict-resistant automated handling.
**Verify:** Reconcile with current roadmap event sourcing, dependency registries, derivation graph and mutation compiler before assigning to worker.

### LOOP-BP2109-0005
Repair/replace the stale Handoff v2 u180h hardcode with current dynamic work binding.
**Last known:** 0172 confirms dynamic binding false and u180h literals active.
**Verify:** Inspect current script; implement only if still present, then prove no-write manifest binding against an unbound test work item.

### LOOP-BP2109-0006
Resolve current work-id allocation/uniqueness authority before CF-10 binding.
**Last known:** u180j is already referenced and no allocator is found.
**Verify:** Check current continuity/work-id registry and operator policy; choose/bind no work_id from historical assumptions.

### LOOP-BP2109-0007
Audit project-context/assistant-pack module routing after unexpected Library-named package.
**Last known:** Owner says no Library task is planned but a Library project-context archive is produced.
**Verify:** Trace package builder target-selection logic and manifest module identity before using or distributing the archive.

### LOOP-BP2109-0008
Determine whether first CF-10 worker pilot was ever subsequently bound/planned/approved/launched.
**Last known:** Visible endpoint is READY_UNBOUND with two blockers and all launch/mutation flags false.
**Verify:** Resolve current roadmap/lifecycle/head first; do not resume historical 0172 directly.
