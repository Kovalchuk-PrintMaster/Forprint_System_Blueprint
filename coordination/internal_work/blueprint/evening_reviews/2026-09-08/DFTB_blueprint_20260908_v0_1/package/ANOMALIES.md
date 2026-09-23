# Anomalies & Open Loops

## Anomalies

### ANOM-BP0809-0001 — new_unique_dialogue (normal)
No message IDs or normalized message texts overlap any of the eleven unique master v1.3 source dialogues.

### ANOM-BP0809-0002 — partial_conversation_capture (high)
Only 13 message blocks survive across turn numbers 1–20; turns 6, 8–12 and 14 are absent.

### ANOM-BP0809-0003 — b10_missing_part02 (high)
B10 catch-all review lacks part 02_of_05, so full catch-all coverage is not proven.

### ANOM-BP0809-0004 — generated_pass_false_confidence (critical)
PASSED reports coexist with stale current-step assumptions/broken snapshot lineage.

### ANOM-BP0809-0005 — status_dimension_collapse (critical)
Status labels mix implementation, roadmap, execution permission and dispatch eligibility.

### ANOM-BP0809-0006 — structural_vs_semantic_validation_split (critical)
Logistics passes structural checks/tests while fresh-context semantic freshness fails.

### ANOM-BP0809-0007 — collector_pass_label_bug (high)
Collector prints PASS for fresh_context_check despite rc=2 because PASS meant command capture, not check result.

### ANOM-BP0809-0008 — duplicate_live_collection (normal)
Logistics L2 is run twice; second run adds no new evidence class.

### ANOM-BP0809-0009 — prompt_lifecycle_vs_head_mismatch (high)
Prompt/control state says ready/not-started while substantial deliverables already exist and operator pause also applies.

### ANOM-BP0809-0010 — repo_identity_mislaunch (normal)
Blueprint collector is launched from Logistics root and correctly refuses to run.

### ANOM-BP0809-0011 — heuristic_coverage_metric (normal)
72% / 0.91 coverage score is historical heuristic; its calculation method is not preserved.

## Open loops

### LOOP-BP0809-0001
Find/review B10 catch-all part 02 and reconcile with existing findings.
**Last known:** Part 02_of_05 missing.
**Verify:** Locate missing batch or prove retirement/merge.

### LOOP-BP0809-0002
Verify legacy self-roadmap/queues are excluded from current selectors and stale PASSED reports are corrected.
**Last known:** Historical B10 review says stale authority/projections remain current-looking.
**Verify:** Audit live selectors, reports and derivation/effective-state links.

### LOOP-BP0809-0003
Verify portfolio forensic mega-prompt, machine schema, coverage dashboard and unresolved registry exist durably.
**Last known:** Owner defines them; construction turns are missing.
**Verify:** Search current Blueprint docs/schemas/scripts.

### LOOP-BP0809-0004
Verify Logistics freshness and prompt lifecycle mismatch were reconciled without rewriting healthy business code.
**Last known:** Structural PASS / semantic freshness FAIL.
**Verify:** Run current Logistics freshness/status checks.

### LOOP-BP0809-0005
Verify collector result semantics and evidence-class deduplication.
**Last known:** Nonzero RC printing and redundant rerun behavior were identified for correction.
**Verify:** Inspect/test current collector/reporting code.

### LOOP-BP0809-0006
Verify Blueprint Wave 1 authority/target/portfolio collector and resulting alignment model.
**Last known:** Collector prepared; no successful Blueprint W1 ZIP/result preserved.
**Verify:** Find later result or rerun bounded current collector from Blueprint root.

### LOOP-BP0809-0007
Verify current module dispositions use local plus project-course evidence.
**Last known:** Local health alone is explicitly insufficient.
**Verify:** Require cross-repo/runtime/target-course evidence before disposition.
