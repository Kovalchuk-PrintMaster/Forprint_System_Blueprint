# Anomalies & Open Loops

## Anomalies

### ANOM-BP0509-0001 — assistant_side_capture_gap (high)
102/103 retained turn containers have text, but only three assistant narrative messages survive; most intermediate execution reasoning is represented by uploaded reports/archives rather than direct assistant prose.

### ANOM-BP0509-0002 — memory_package_duplication_risk (high)
v1.0 and v1.1 describe overlapping prior dialogue using different Human Intent IDs; blind merge would create semantic duplication and obscure provenance.

### ANOM-BP0509-0003 — document_schema_fragmentation (high)
Different module/roadmap documents use inconsistent headings, structures and equivalent state vocabulary, repeatedly slowing information distribution and tooling.

### ANOM-BP0509-0004 — infrastructure_entropy (high)
Without a stale-artifact registry and active self-cleaning policy, old scripts/docs/modules can continue accumulating and participating in checks long after they stop being useful.

### ANOM-BP0509-0005 — foreign_scope_contamination (normal)
A UI/system-settings task appears inside the dialogue but is immediately identified by the owner as not belonging to this module. It must not be promoted into Blueprint requirements.

### ANOM-BP0509-0006 — direct_push_vs_pull_drift_risk (critical)
Owner explicitly reasserts pull-based module execution. Any runtime path that tries to push prompts directly into a module repository would violate this intended ownership model.

### ANOM-BP0509-0007 — post_release_set_semantics (high)
After release, prepared-draft membership and Acceptance-Oracle binding are different concepts. A regression test incorrectly treated them as the same set.

### ANOM-BP0509-0008 — semantic_reference_orphan (high)
A one-shot authorization decision may remain a current governance document without durable inbound reference after release policy resets, triggering `GENUINE_NO_INBOUND_CURRENT_DOCUMENTS`.

## Open loops

### LOOP-BP0509-0001
Verify final v1.1 Human Intent integration and residual v1.0 audit.
**Last known:** Initial integration safe-failed on Ruff; assistant intended v1.1 primary + residual v1.0 review.
**Verify:** Inspect current Human Intent registry/history and integration decisions.

### LOOP-BP0509-0002
Verify project-wide document/roadmap normalization and canonical vocabulary.
**Last known:** Bulk review packages were exchanged and SYNTHETIC→PROPOSED normalization was selected.
**Verify:** Audit current schemas, roadmap files and validators for remaining structural variants.

### LOOP-BP0509-0003
Verify self-cleaning/deprecation governance and automated conformance checks.
**Last known:** Owner required portfolio-wide cleanup policy, stale-candidate handling and indexing; implementation status is not proven by the dialogue.
**Verify:** Inspect current standards, index/catalog, deprecation registry and health validators.

### LOOP-BP0509-0004
Verify pull-based prompt execution end to end.
**Last known:** Owner restated Blueprint-publish/module-pull/fresh-worker architecture; later u123 work reached ready_for_module_pull but module-side pickup was not yet proven in retained assistant prose.
**Verify:** Inspect current release/listener/module-start runtime and one real Logistics prompt cycle.

### LOOP-BP0509-0005
Verify post-release Acceptance Oracle binding semantics.
**Last known:** u123a/b fixed generic health and acceptance-binding tests conceptually; current code state not verified here.
**Verify:** Audit prompt queue/drafts/roadmap oracle binding after a real release.

### LOOP-BP0509-0006
Verify durable inbound binding for one-shot authorization evidence.
**Last known:** u123b ended on `GENUINE_NO_INBOUND_CURRENT_DOCUMENTS`; u123c was prepared as read-only discovery before u124 repair.
**Verify:** Inspect current governance decision references and semantic validator results.

### LOOP-BP0509-0007
Verify knowledge/context snapshot workflow is current and integrated.
**Last known:** Read-only self-inventory and portfolio/roadmap context packages were generated successfully.
**Verify:** Locate current snapshot tooling and determine whether it feeds startup/planning without becoming authority.
