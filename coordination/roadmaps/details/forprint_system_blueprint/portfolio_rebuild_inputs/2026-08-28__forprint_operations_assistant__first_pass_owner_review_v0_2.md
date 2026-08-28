# ForPrint Operations Assistant — evening first-pass owner review

Module: `forprint_operations_assistant`

Status: `FIRST_PASS_OWNER_DIRECTION_RECORDED / SYNTHETIC_MICROSTEPS_PENDING_SECOND_PASS`

## AGREED_WITH_OWNER

Operations Assistant is the universal employee-facing helper for real job duties. It should make procedures
discoverable/executable through QR codes, search, indexed/RAG knowledge, guided forms, instructions, video and
context-aware actions.

It serves different staff roles with different permissions.

## Working boundary

Operations Assistant does not own material/equipment/accounting/warehouse/order truth. It resolves context and
guides the worker, then calls the owning module for state changes. QR reveals context; Identity & Access decides
what the worker may do.

## Synthetic roadmap expansion for pass 2

Everything below is `SYNTHETIC_CANDIDATE` unless explicitly described as owner direction.

### OA-R0 — Inventory roles/tasks/objects
- shop-floor/manager/supervisor roles
- machines/materials/areas/procedures
- manual instructions
- frequent support/confusion cases
### OA-R1 — Role-aware PWA shell
- phone/tablet/desktop
- shared Design System
- role/capability checks
- safe bounded offline behavior
### OA-R2 — QR entity/context model
- QR identity for machine/material/location/task
- canonical resolution
- context menu
- deep links into procedures/actions
### OA-R3 — Knowledge/RAG/search
- indexed lookup
- semantic/RAG lookup
- version-aware instructions
- clear obsolete/current labels
### OA-R4 — Instruction/media experience
- step-by-step text
- diagrams/photos/video
- checklists/warnings
- media provider may produce assets but does not own instruction semantics
### OA-R5 — Guided business actions
- inventory/count capture
- receiving/QC
- requests/write-offs/forms
- production observations/issues
### OA-R6 — Anomaly/escalation
- missing/contradictory instruction
- unsafe action confirmation
- route exceptions
- capture employee correction
### OA-R7 — Learning/maturity
- frequent unanswered searches
- procedure completion
- human help rate
- stale QR/content backlog

## Dependencies

Library, Identity & Access, Warehouse/Accounting/order/production owners, System Administration;
Marketing/media only as possible asset-production provider.

## Open questions for pass 2

Instructional media owner; first physical workflows; offline limits; QR/device security; action-initiation boundaries.

## Target milestone

Employees perform common duties safely with minimal tribal knowledge, using current canonical instructions and permissions.

## Steady state

Continue measured improvement after the target milestone; the module is not considered permanently finished.
