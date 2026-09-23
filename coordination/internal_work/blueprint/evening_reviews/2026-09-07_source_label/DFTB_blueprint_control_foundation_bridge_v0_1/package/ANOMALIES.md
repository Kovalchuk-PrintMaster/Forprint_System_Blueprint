# Anomalies & Open Loops

## Anomalies

### ANOM-BP0709CF-0001 — filename_date_conflicts_with_internal_lineage (high)
Filename says 07.09.26, but source opens with `forprint_evening_strategy_2026-09-12_v0_1.zip` and already-closed u180a/CF-01 state. Filename date is not reliable chronology authority.

### ANOM-BP0709CF-0002 — stale_handoff_would_duplicate_closed_work (critical)
Opening handoff says perform B1-P2 F01–F04 next, but exact current-state reconciliation reports those items already CLOSED/sealed/published. Blind handoff execution would regress or duplicate work.

### ANOM-BP0709CF-0003 — partial_capture_attachment_gap (high)
Turns 5, 7, 9 and 11 are only pasted-text/archive labels; detailed probe/candidate package contents are not embedded in the MHTML transcript.

### ANOM-BP0709CF-0004 — tests_compile_green_but_semantic_review_blocks (critical)
Candidate focused tests/compilation can pass while semantic/adversarial review still finds seven architecture/governance blockers.

### ANOM-BP0709CF-0005 — hidden_dependency_registry_gap (critical)
Candidate adds/changes operational command surfaces without corresponding execution-dependency registry updates.

### ANOM-BP0709CF-0006 — derivation_registry_gap (high)
Persistent generated roadmap reconciliation output lacks generator-derivation registry registration.

### ANOM-BP0709CF-0007 — unauthorized_future_work_identity_preallocation (critical)
Candidate assigns future u180b…u180s identities without explicit authority, widening scope beyond current CF-02.

### ANOM-BP0709CF-0008 — projection_bootstrap_order_gap (high)
After source apply, roadmap-sync-check would see PROJECTION_MISSING until explicit first roadmap-sync is run; bootstrap/apply ordering was not formalized.

### ANOM-BP0709CF-0009 — ambient_projection_dependency_breaks_test_isolation (critical)
Control Plane candidate implicitly depends on repository-root projections, creating hidden ambient state in unit tests.

### ANOM-BP0709CF-0010 — coarse_legacy_migration_boundary (critical)
Legacy migration uses `through_order: 7` instead of binding exact pre-migration roadmap SHA, accepted step IDs and immutable evidence.

## Open loops

### LOOP-BP0709CF-0001
Verify B1-P2 F01–F04 closure/seal/publication in current history and ensure stale handoff does not remain executable.
**Last known:** Historical reconciliation says already closed; stale handoff still contained next-action wording.
**Verify:** Check current handoff/index selectors and archived B1 acceptance/seal/publication evidence.

### LOOP-BP0709CF-0002
Verify the seven CF-02 candidate v0.1 findings were closed in v0.2/current implementation.
**Last known:** Candidate v0.1 RETURN_FOR_CORRECTION / FINDING_COUNT=7; no activation/apply allowed.
**Verify:** Trace v0.2/later candidate and compare all seven review findings against current code/config/tests.

### LOOP-BP0709CF-0003
Verify CF-02 dependency and generator registries are complete and deterministic.
**Last known:** Missing registry entries and bootstrap-order contract blocked v0.1.
**Verify:** Run current execution-dependency-check, generator-contract-check and roadmap-sync bootstrap tests.

### LOOP-BP0709CF-0004
Verify no future Control Foundation work IDs are pre-authorized by planning artifacts.
**Last known:** v0.1 candidate attempted u180b…u180s preallocation and was rejected.
**Verify:** Inspect current roadmap/lifecycle identity generation and authority boundaries.

### LOOP-BP0709CF-0005
Verify Control Plane tests have no ambient repository-root projection dependency.
**Last known:** v0.1 review found hidden ambient projection dependence.
**Verify:** Run tests in sterile/clean-room context with explicit projection inputs.

### LOOP-BP0709CF-0006
Verify legacy Continuity migration is bound to immutable exact evidence.
**Last known:** through_order:7 migration was rejected as too coarse.
**Verify:** Inspect current migration contract for pre-migration SHA, accepted step IDs and immutable evidence.
