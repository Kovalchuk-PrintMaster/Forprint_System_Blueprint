# Open gaps / deferred decisions after 2026-08-30/31 review

Status: current review-closure projection
Authority note: this file preserves unresolved/deferred questions; it does not create
implementation authority. Evidence references show that a topic is represented in current
planning, not that the decision is fully resolved.

## GAP-1 — Job Specification detailed schema

**State:** OPEN / DEFERRED; current planning evidence present.

Pilot chosen, schema not finalized. Do not invent the full field set before Calculator
target modeling.

Current evidence:
- `coordination/internal_work/blueprint/evening_reviews/2026-08-31/contract_registry_target_architecture_v0_1.md`
- `coordination/human_intent/modules/calculator_engine.yaml`
- `coordination/human_intent/modules/forprint_contract_registry.yaml`

## GAP-2 — Legacy filename grammar completeness

**State:** OPEN / DEFERRED; current planning evidence present.

The current discussion covers major Ricoh/Epson patterns and known markers, but the full
corpus contains more historical variants. Need a corpus-driven inventory and token
classification.

Current evidence:
- `coordination/internal_work/blueprint/roadmap_amendments/2026-08-31__evening_review__roadmap_amendments_v0_1.yaml`
- `coordination/internal_work/blueprint/prompt_planning/2026-08-31__evening_review__implementation_prompt_plan_v0_1.yaml`

## GAP-3 — PDF-to-physical-sheet validation convention

**State:** OPEN / DEFERRED; current planning evidence present.

The owner clarified that the filename quantity means physical sheets. Implementation still
needs a deterministic rule for how each prepress/profile maps PDF sides/pages/imposition to
physical sheets.

Current evidence:
- `coordination/human_intent/modules/forprint_prepress_hub.yaml`
- `coordination/human_intent/modules/calculator_engine.yaml`

## GAP-4 — Final device capability taxonomy

**State:** OPEN / DEFERRED; current planning evidence present.

Capability/group/instance model is agreed direction; actual capability IDs and device
inventory are not yet defined.

Current evidence:
- `coordination/internal_work/blueprint/evening_reviews/2026-08-31/file_and_production_artifact_governance_v0_1.md`
- `coordination/human_intent/modules/forprint_system_administration.yaml`

## GAP-5 — Cross-module invariant registry canonical location/schema

**State:** OPEN / DEFERRED; current planning evidence present.

Concept is useful and accepted as part of Inspector/Blueprint strengthening; final
repository schema/location should follow existing governance conventions.

Current evidence:
- `coordination/internal_work/blueprint/evening_reviews/2026-08-31/project_inspector_semantic_consistency_audit_v0_1.md`
- `coordination/internal_work/blueprint/roadmap_amendments/2026-08-31__evening_review__roadmap_amendments_v0_1.yaml`

## GAP-6 — Exact Calculator external visual-configurator reference resources/URLs

**State:** OPEN / EXACT DETAIL UNRECOVERED.

Previously discussed resources remain unrecovered. **Do not invent replacements.**

No exact current URL/resource evidence was found during the v1.0 → integrated-v1.1
residual audit on 2026-08-31.

## GAP-7 — Contract Registry final contract-family taxonomy

**State:** OPEN / DEFERRED; current planning evidence present.

Synthetic list exists; exact final lifecycle/family vocabulary should be reconciled with
existing Blueprint revision governance during implementation.

Current evidence:
- `coordination/internal_work/blueprint/evening_reviews/2026-08-31/contract_registry_target_architecture_v0_1.md`
- `coordination/human_intent/modules/forprint_contract_registry.yaml`

## GAP-8 — Full legal-review policy

**State:** OPEN / SEPARATE GOVERNANCE DECISION.

Inspector LLM may issue-spot and escalate. The final company legal-review/retention policy
remains a separate governance decision.

Current evidence:
- `coordination/internal_work/blueprint/evening_reviews/2026-08-31/project_inspector_semantic_consistency_audit_v0_1.md`
- `coordination/human_intent/modules/forprint_project_inspector.yaml`

## GAP-9 — JDF/XJDF/PDF metadata adoption point

**State:** OPEN / FUTURE INTEROPERABILITY DIRECTION.

Keep as future interoperability direction; no active implementation commitment until a
concrete RIP/device/workflow integration justifies it.

Current evidence:
- `coordination/internal_work/blueprint/evening_reviews/2026-08-31/file_and_production_artifact_governance_v0_1.md`
- `coordination/human_intent/modules/forprint_prepress_hub.yaml`

## Closure note

This explicit GAP list closes the *review documentation requirement*, not the gaps
themselves. GAPs remain open/deferred until separate evidence proves a decision or
implementation closure.
