# Stage 2 Charter — Module Knowledge Stabilization & Capability Reconciliation v0.1

## Mission

Transform selected ForPrint modules into repositories that a constrained automatic assistant can safely understand and extend without repeatedly rediscovering the entire project.

## Questions each module must answer

1. What capabilities are actually implemented now?
2. Where is each capability implemented?
3. Which tests/checks/evidence verify it?
4. Which documents accurately describe current implementation?
5. Which documents are historical, superseded, conflicting or architecturally incompatible?
6. Are multiple implementations solving the same problem?
7. Does functionality live in the wrong module under the current architecture?
8. Can an existing implementation be reused, adapted or migrated instead of recreated?
9. Which roadmap ideas are already implemented?
10. Which implemented capabilities are missing from the roadmap?
11. Which real gaps remain after reconciliation?

## Core principle

EXPAND KNOWLEDGE, NOT PERFECT ORDER.

Discovery and reconciliation come before cleanup.

Do not delete, move, rewrite or modernize historical material merely because it looks old.

## New capability rule

Before implementing a new capability, an assistant must prove that it checked for:

- current implementation;
- partial implementation;
- duplicate implementation;
- legacy implementation that can be adapted;
- cross-module implementation that can be reused or migrated.

Absence of an exact filename is not evidence of absence of capability.

## Ownership rule

Physical location does not prove correct long-term ownership. Ownership must be reconciled against current Blueprint architecture.

## Automatic vs human/review-gated decisions

Automation may derive file inventory, hashes, symbols, imports, test references and other mechanical evidence.

Automation may propose but must not independently finalize document obsolescence, architectural ownership migration, duplicate winner selection, destructive cleanup or roadmap deletion.
