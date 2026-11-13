# Module Knowledge Stabilization — canonical entrypoint

## Purpose

This directory is the canonical Blueprint entrypoint for the second major knowledge-saturation stage of the ForPrint ecosystem.

Stage 1 enriched Blueprint with historical dialogue evidence, Human Intent recovery, module-level historical candidates, roadmap context and selected current-state reconciliation.

Stage 2 turns selected module repositories into self-explaining, assistant-safe working surfaces.

Required outcomes per selected module:

1. Module Knowledge Index;
2. Module Knowledge Base;
3. Document Authority Registry;
4. Capability Reconciliation Registry;
5. Roadmap ↔ Implementation linkage;
6. Cross-module reuse/migration candidates;
7. Technical Cleanup Work Package;
8. maintenance automation for mechanically derivable index data.

## Current program state

- Stage 1: Historical & Roadmap Knowledge Enrichment — first major phase complete.
- Stage 2: Module Knowledge Stabilization & Capability Reconciliation — current program.
- Pilot: `forprint_library`.

Normal sequence:

1. `forprint_library`
2. `forprint_operations_control_registry`
3. `forprint_accounting_registry_service`
4. `forprint_integration_gateway`
5. `forprint_logistics_service`

High-risk legacy wave after the normal methodology is proven:

- `calculator_engine`
- `telegram_bot`

## Authority rule

Historical dialogue, old README files, old prompts and archived design documents are evidence and provenance, not automatically current implementation authority.

A new assistant must not create a new capability merely because it cannot immediately find an exact filename for that capability.

Before new implementation it must check:

- Module Knowledge Index;
- Module Knowledge Base;
- capability inventory;
- Document Authority Registry;
- Capability Reconciliation Registry;
- current Blueprint architecture/governance.

## Context packages

Assistant Context Pack / Assistant Spark are projections of this canonical program.

They must tell a new assistant where authoritative records are and what stage/step is current. They are not a competing source of truth.
