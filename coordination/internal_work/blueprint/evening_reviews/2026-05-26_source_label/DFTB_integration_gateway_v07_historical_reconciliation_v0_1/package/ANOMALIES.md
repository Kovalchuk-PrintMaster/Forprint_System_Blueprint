# Anomalies & Open Loops

## Anomalies

### ANOM-GW2605-0001 — new_unique_cross_module_source (normal)
No shared message IDs or meaningful normalized sequence overlap with previously loaded sources. This is a distinct Integration Gateway history.

### ANOM-GW2605-0002 — attachment_heavy_partial_capture (high)
Only 34 visible message blocks survive across turns 1–144; most intermediate user turns are attachment placeholders, so v0.2–v0.6 implementation details cannot be reconstructed literally.

### ANOM-GW2605-0003 — filename_date_terminal_ambiguity (high)
Filename says 26.05, but the same conversation reaches v0.7 Blueprint standards visibility with no embedded terminal date. Chronology must use causal project lineage rather than filename alone.

### ANOM-GW2605-0004 — early_contract_authority_unresolved (critical)
Bootstrap asks whether contract_id should point at a future Library registry or local placeholders. Later Blueprint creates a dedicated Contract Registry, so early Gateway contract assumptions are not current authority.

### ANOM-GW2605-0005 — standards_sync_repo_boundary_ambiguity (high)
v0.7 includes standards-sync/snapshots, but the visible transcript does not fully prove whether Gateway only consumes/caches Blueprint standards or can mutate foreign Blueprint sources.

### ANOM-GW2605-0006 — ignored_canonical_report_friction (normal)
The v0.7 completion report/index needs force-add under an ignored reports path, suggesting canonical report tracking conflicts with ignore policy.

### ANOM-GW2605-0007 — local_completion_not_blueprint_acceptance (critical)
v0.7 is locally complete and pushed, but the final handoff still asks Blueprint to mark the prompt completed/accepted and issue the next allowed prompt.

## Open loops

### LOOP-GW2605-0001
Verify current Gateway boundary and must-not-own contracts.
**Last known:** Historical Gateway is validation/routing/idempotency/audit only and remains offline/contract-only through v0.7.
**Verify:** Audit current manifest/code/contracts for business-logic, domain-truth, live-adapter or pricing/accounting creep.

### LOOP-GW2605-0002
Reconcile Gateway with the later dedicated Contract Registry architecture.
**Last known:** Early bootstrap leaves contract_id authority open; later Blueprint says Contract Registry owns versioned agreements and Gateway validates/routes them at runtime.
**Verify:** Resolve current Contract Registry/Gateway/domain-owner contracts and ensure Gateway does not become contract semantic authority.

### LOOP-GW2605-0003
Verify current Blueprint standards visibility/sync is read-only with respect to Blueprint authority.
**Last known:** Historical v0.7 has standards list/check/sync and a local standards snapshot.
**Verify:** Inspect current scripts/path ownership; prove sync only materializes module-local projections and cannot rewrite Blueprint standards.

### LOOP-GW2605-0004
Verify preview-first readiness remains separated from live capability enablement.
**Last known:** Historical v0.7 preview surfaces are green while live/1C/posting/final-price flags remain disabled.
**Verify:** Run current readiness/live-flag gates and inspect adapter/runtime boundaries.

### LOOP-GW2605-0005
Verify v0.7 implementation/report commits and Blueprint acceptance history.
**Last known:** Historical module reports implementation `9f792a3`, report `2f36256`, locally complete but awaiting Blueprint acceptance.
**Verify:** Resolve current Gateway Git ancestry and Blueprint intake/acceptance records; do not infer acceptance from local push.

### LOOP-GW2605-0006
Resolve canonical coordination-report tracking vs ignore policy.
**Last known:** Historical v0.7 uses `git add -f` for canonical coordination report/index under ignored reports tree.
**Verify:** Inspect current repository policy so authoritative reports do not require accidental-force-add behavior.
