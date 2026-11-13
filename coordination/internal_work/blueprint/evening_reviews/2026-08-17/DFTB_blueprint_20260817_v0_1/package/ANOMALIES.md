# Anomalies & Open Loops

## Anomalies

### ANOM-BP1708-0001 — assistant_side_capture_gap (high)
All 142 retained conversation containers have text, but only four assistant narrative messages survive. Most intermediate reasoning is represented by owner-supplied report attachments and follow-up instructions.

### ANOM-BP1708-0002 — authority_recovery_risk (high)
The session itself begins after a context-window break and demonstrates that archived handoff state can already be stale relative to live repository state.

### ANOM-BP1708-0003 — roadmap_granularity_gap (normal)
Owner explicitly identifies that flat roadmap tasks hide partial implementation depth, motivating subtask hierarchy and dual views.

### ANOM-BP1708-0004 — legacy_compatibility_drag (high)
Old tests/scripts are seen as potential blockers even after their operating model is superseded; owner wants deprecation/isolation instead of permanent compatibility burden.

### ANOM-BP1708-0005 — module_rollout_imbalance (high)
Modules are acknowledged to be at very different maturity levels. Pulling all of them into the new model simultaneously is explicitly rejected in favor of Logistics-only validation.

### ANOM-BP1708-0006 — side_branch_scope_contamination (normal)
A substantial UI/browser styling branch appears inside a Blueprint hardening conversation. It contains real requirements but its owning module/component is not clearly named in the preserved source.

### ANOM-BP1708-0007 — historical_report_not_current_proof (normal)
Many H3–H9/B1 states survive as report filenames or historical command output. They are useful execution chronology but are not proof of today's repository state.

### ANOM-BP1708-0008 — release_goal_drift_risk (critical)
v0.4.1 hardening spans many subphases and the owner explicitly worries that another context loss could break the long idea chain before the end-to-end Logistics/Codex objective is reached.

## Open loops

### LOOP-BP1708-0001
Verify the current Makefile still represents the canonical operational surface and whether any important workflow bypasses it.
**Last known:** Owner explicitly made Make the transparency/control surface during this dialogue.
**Verify:** Audit current Make targets against runtime/coordination commands and current documentation.

### LOOP-BP1708-0002
Verify current module/Blueprint ownership around completion packet/outbox/review mutations.
**Last known:** v0.4 design separates module-owned completion evidence from Blueprint-owned review and requires explicit confirmation.
**Verify:** Inspect current schemas, validators, review transaction and runtime behavior.

### LOOP-BP1708-0003
Verify whether roadmap hierarchy/subtask dual-view design became canonical.
**Last known:** Owner accepted the concept while v0.4.1 roadmap hardening was underway.
**Verify:** Inspect current roadmap schema/renderers and module roadmaps.

### LOOP-BP1708-0004
Verify legacy test/tool retirement strategy.
**Last known:** Owner wanted deprecated mechanisms to stop blocking modern checks and later be isolated/archive-accessible.
**Verify:** Check current legacy/deprecation policy, test selection and archive strategy.

### LOOP-BP1708-0005
Identify the owner/component for the UI/browser requirements side branch.
**Last known:** Requirements were actively refined, but target module is not explicit in preserved text.
**Verify:** Search later dialogues/current UI repositories for filter browser, breadcrumb and shared button-style work.

### LOOP-BP1708-0006
Verify the final v0.4.1 zero-context bootstrap and end-to-end Logistics/Codex release objective.
**Last known:** Continuity package was reported published/current; B1 remained incomplete and work returned to B1-P2 F01–F04.
**Verify:** Compare current release/bootstrap/roadmap/runtime pilot evidence and determine what remains incomplete or has been superseded.
