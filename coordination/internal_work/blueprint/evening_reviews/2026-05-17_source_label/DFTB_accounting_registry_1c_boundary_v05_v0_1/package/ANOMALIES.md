# Anomalies & Open Loops

## Anomalies

### ANOM-ACC1705-0001 — new_unique_cross_module_source (normal)
No shared message IDs with prior loaded Blueprint/module sources. This is a distinct Accounting Registry history.

### ANOM-ACC1705-0002 — partial_attachment_heavy_capture (high)
Only 22 visible message blocks survive; most intermediate implementation steps are attachment placeholders and cannot be reconstructed literally.

### ANOM-ACC1705-0003 — early_inventory_design_owner_ambiguity (critical)
The opening architecture proposes `inventory_core/materials_ledger` inside the Accounting conversation, but later module boundaries indicate operational/warehouse truth should not belong to Accounting Registry. Treat it as early system design, not Accounting ownership.

### ANOM-ACC1705-0004 — historical_acceptance_not_current_authority (normal)
Owner pastes a v0.5 accepted status, but this historical acceptance is not current implementation/architecture proof.

### ANOM-ACC1705-0005 — sandbox_ready_not_live_ready (critical)
`sandbox_1c_import_export_ready` is explicitly not live-1C/write/posting readiness. These status dimensions must not be collapsed.

### ANOM-ACC1705-0006 — v06_blocked_on_real_sanitized_samples (high)
Further parser work is blocked on real sanitized exports; inventing profiles from synthetic fixtures would violate the accepted gate.

### ANOM-ACC1705-0007 — accounting_vs_operational_registry_historical_overlap (critical)
This source clarifies accounting/1C vs production operational truth, while later Blueprint history records Accounting-vs-Operational Registry ambiguity. Current architecture must reconcile exact ownership without merging the two authorities.

## Open loops

### LOOP-ACC1705-0001
Verify current Accounting Registry vs Operational Registry/1C ownership boundary.
**Last known:** Historical source separates production operational truth from accounting/1C concerns; later Blueprint history still contains naming/ownership ambiguity.
**Verify:** Resolve current release/ADRs/module manifests and assign accounting truth, operational truth, inventory/warehouse movement and 1C adapter ownership exactly once.

### LOOP-ACC1705-0002
Verify v0.5 sanitized 1C pipeline and safety boundaries in current repo.
**Last known:** Historical v0.5 reports offline sanitized parsers/staging/mapping issue pipeline and production-source rejection.
**Verify:** Inspect current code/tests/config with current HEAD; ensure no live/write/posting capability was silently added.

### LOOP-ACC1705-0003
Verify historical v0.5 acceptance and commit lineage.
**Last known:** 117 tests green; commit 95d4a55 pushed; owner supplies accepted status.
**Verify:** Trace live Git history and Blueprint coordination/acceptance record; do not infer current state from historical report.

### LOOP-ACC1705-0004
Verify v0.6 remains gated on real sanitized sample categories.
**Last known:** No v0.6 parser hardening until sanitized counterparties/nomenclature/invoices/payments/balances samples exist.
**Verify:** Check current roadmap/status and whether qualifying sanitized samples were ever provided.

### LOOP-ACC1705-0005
Verify Accounting Registry never became canonical client/order/product/material owner.
**Last known:** Historical maintenance boundary explicitly forbids these ownerships/live integrations.
**Verify:** Audit current manifest/models/repositories against Operational Registry, Library, Warehouse and Gateway boundaries.

### LOOP-ACC1705-0006
Locate or supersede missing intermediate implementation attachments.
**Last known:** Most v0.1–v0.5 intermediate steps are attachment-only in this MHTML.
**Verify:** Use repository history and current artifacts rather than reconstructing missing turns from guesswork.
