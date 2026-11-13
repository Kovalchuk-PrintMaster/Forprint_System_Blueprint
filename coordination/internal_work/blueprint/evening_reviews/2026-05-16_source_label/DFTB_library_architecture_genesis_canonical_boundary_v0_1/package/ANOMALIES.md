# Anomalies & Open Loops

## Anomalies

### ANOM-LIB1605-0001 — new_unique_cross_module_source (normal)
No SHA/message-ID/meaningful sequence match exists against prior loaded Blueprint/Logistics sources. This is a distinct Library module history.

### ANOM-LIB1605-0002 — partial_conversation_capture (high)
Only turns 1–2 and 23–28 survive. The implementation steps between initial design and Stage 2 are missing from the export.

### ANOM-LIB1605-0003 — early_scope_overreach_corrected (critical)
Initial owner vision includes operational employee/availability and broad 'everything' data, while later Blueprint alignment explicitly narrows Library to canonical definitions. Treat later boundary as refinement/supersession, not parallel authority.

### ANOM-LIB1605-0004 — contract_registry_role_evolution (critical)
Early alignment makes Library a contract registry/definition layer, but later Blueprint architecture creates a separate Contract Registry/Gateway/domain-owner model. Current architecture must reconcile which contract responsibilities remain in Library.

### ANOM-LIB1605-0005 — sync_manager_future_role_uncertain (normal)
Early alignment proposes `forprint_sync_manager` as a separate first-class module; later architecture may have redistributed this responsibility across Blueprint, Gateway, runtime or standards-adoption mechanisms.

### ANOM-LIB1605-0006 — historical_implementation_not_current_proof (normal)
Health endpoint and seven passing tests establish historical bootstrap evidence only; they do not prove current Library implementation/state.

## Open loops

### LOOP-LIB1605-0001
Verify current Library canonical ownership boundary against later Blueprint/Contract Registry architecture.
**Last known:** Early alignment says Library owns canonical catalogs/semantics/contracts but no runtime state; later Blueprint introduces separate Contract Registry/Gateway/domain-owner semantics.
**Verify:** Resolve current release/ADRs and assign each contract/catalog/semantic responsibility to exactly one current authority.

### LOOP-LIB1605-0002
Verify semantic ID stability aliases and migration graph in current Library.
**Last known:** Historical Stage 2 and alignment make semantic IDs/aliases/migration graph foundational.
**Verify:** Audit current schemas/registry/tests for stable IDs, alias history, blocked/deprecated versions and migration-path validation.

### LOOP-LIB1605-0003
Verify Library change-impact and activation lifecycle.
**Last known:** Historical alignment recommends draft→approved→staged→syncing→active and impact triggers across contracts/semantics/catalogs/templates/migrations.
**Verify:** Inspect current change manifest, adoption/impact analysis and activation gates; determine whether later standards/Contract Registry superseded this mechanism.

### LOOP-LIB1605-0004
Verify admin tooling is present without operational scope creep.
**Last known:** Owner required strong human-facing administration for canonical definitions.
**Verify:** Audit current admin surfaces, permissions, publish validation and ensure runtime orders/payments/stock are not administered as Library-owned data.

### LOOP-LIB1605-0005
Verify current Library Git/repository hygiene and test gates.
**Last known:** Historical process required test→commit→push and cleaning backup/cache artifacts.
**Verify:** Inspect live repo branch/HEAD, CI/make gates, gitignore and generated/local artifact policy.

### LOOP-LIB1605-0006
Determine whether proposed Sync Manager still exists as a current architecture concept.
**Last known:** Early alignment recommends a first-class `forprint_sync_manager`.
**Verify:** Search current Blueprint/module inventory and ADRs for Sync Manager or successor responsibilities; classify implemented/superseded/deferred.
