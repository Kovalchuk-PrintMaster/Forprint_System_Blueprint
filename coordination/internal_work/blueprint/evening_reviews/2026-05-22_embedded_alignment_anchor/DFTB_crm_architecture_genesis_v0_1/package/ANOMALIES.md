# Anomalies & Open Loops

## Anomalies

### ANOM-CRM1605-0001 — new_unique_cross_module_source (normal)
No shared message IDs or exact normalized message text with previously loaded MHTML sources. This is a distinct CRM/architecture-genesis dialogue.

### ANOM-CRM1605-0002 — partial_conversation_capture (high)
Only 11 message blocks survive across turns 1–30; intermediate turns 3–25 are absent, so the transition from Prepress discussion to CRM governance cannot be fully reconstructed.

### ANOM-CRM1605-0003 — crm_ownership_corrected_inside_source (critical)
An early Blueprint example assigns `client` and `order` ownership to CRM, while the later direct CRM alignment prompt moves clients/orders/tasks/statuses to Operational Registry. The later alignment must win.

### ANOM-CRM1605-0004 — project_control_name_collision (high)
Early `ForPrint Project Control Plane` is explicitly renamed/reframed by owner as Project Inspector. It must not be merged by name with the later Strategic Control Plane proposal.

### ANOM-CRM1605-0005 — crm_business_orchestration_vs_canonical_truth (critical)
CRM is a visible business-management surface, creating persistent risk that UI prominence is mistaken for canonical data ownership.

### ANOM-CRM1605-0006 — order_creation_command_boundary_unresolved (critical)
The source aligns canonical orders to Operational Registry but leaves open whether CRM creates orders directly or commands Operational Registry through Gateway.

### ANOM-CRM1605-0007 — historical_prepress_architecture_not_current_implementation_proof (normal)
The Prepress Hub/Python/web/preset design is a historical proposal in a CRM-labelled conversation and does not prove current Prepress implementation or ownership.

## Open loops

### LOOP-CRM1605-0001
Verify current CRM canonical ownership boundary.
**Last known:** Historical alignment says CRM coordinates/displays while specialized registries own canonical truth.
**Verify:** Audit current CRM manifest/models/contracts and current Blueprint ownership map; flag canonical Client/Order/Invoice/Material duplication.

### LOOP-CRM1605-0002
Resolve current order-creation/manual-decision command path.
**Last known:** Historical source leaves CRM direct-create vs Gateway→Operational Registry command path open.
**Verify:** Use current Contract Registry/Gateway/Operational Registry authority to define the command and event contracts.

### LOOP-CRM1605-0003
Verify Blueprint/Inspector/CRM separation remains explicit.
**Last known:** Blueprint plans architecture, Inspector checks, CRM presents business/health views.
**Verify:** Audit current module manifests/ADRs for duplicated architecture checking or architecture truth inside CRM.

### LOOP-CRM1605-0004
Verify early Project Control Plane lineage is archived as Inspector, not conflated with Strategic Control Plane.
**Last known:** Owner renamed early project-control verification concept to Project Inspector; later Control Plane source is strategic/governance concept.
**Verify:** Keep identity/history indexes explicit and prevent name-based merging.

### LOOP-CRM1605-0005
Verify current Prepress automation architecture and ownership.
**Last known:** Historical proposal recommends local backend + UI + declarative presets/adapters/hot folders.
**Verify:** Audit current Prepress module before promoting any of these early design choices.

### LOOP-CRM1605-0006
Reconcile historical proposed CRM contracts with current Contract Registry.
**Last known:** Source proposes six/seven direct contract names before later dedicated Contract Registry governance.
**Verify:** Map proposed contracts to current versioned agreements; classify retained/renamed/superseded.
