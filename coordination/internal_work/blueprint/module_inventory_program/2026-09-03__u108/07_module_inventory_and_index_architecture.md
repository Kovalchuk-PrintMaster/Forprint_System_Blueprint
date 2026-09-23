# Module Inventory & Index Architecture

## Goal
Give each module a compact deterministic knowledge surface before an assistant searches the repository broadly.

## Logical surfaces
Exact paths may vary:
- inventory/repository_inventory.yaml
- inventory/capability_inventory.yaml
- inventory/documentation_authority.yaml
- inventory/legacy_implementation_map.yaml
- inventory/ownership_conflicts.yaml
- inventory/evidence_registry.yaml
- indexes/knowledge_summary.yaml
- indexes/documents.yaml
- indexes/entrypoints.yaml
- indexes/tests.yaml
- indexes/contracts.yaml
- indexes/dependencies.yaml
- indexes/deprecated_and_historical.yaml
- AGENTS.md
- deterministic build/check/validate scripts

Indexes are derived, not truth. Entries point back to evidence.

## Tooling
Future module-local tooling should support equivalents of:
- build inventory/index;
- check drift;
- validate structure;
- render compact summary.

Collection is read-only by default. Canonical mutation goes through safe mutation.
Do not blindly copy Blueprint-specific paths; reuse the contract and pattern.
