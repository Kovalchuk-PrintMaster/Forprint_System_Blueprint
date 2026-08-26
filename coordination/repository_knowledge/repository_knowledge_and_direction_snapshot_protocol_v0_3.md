# ForPrint Repository Knowledge & Direction Protocol v0.3

## Purpose

v0.3 preserves the proven v0.2 RCI / REDM / SDRS evidence model while expanding it from a periodic
manual snapshot exercise into the foundation of continuously maintained project self-knowledge.

It exists to prevent forgotten implementations, hidden duplication, unexplained dependencies,
assistant-memory-only operational chains, loss of rationale, invisible stale rules, cross-module
dependency gaps, unsafe structural cleanup and autonomous executors inventing local standards.

## Core artifacts retained

### RCI — Repository Capability Inventory
What important paths/capabilities exist, what they do, evidence/confidence, ownership, consumers,
side effects and usage state.

### REDM — Repository Execution & Dependency Map
How meaningful operations flow from entrypoint through contracts/functions/dependencies, including
inputs, outputs, side effects, failures and recovery.

### SDRS — State, Direction & Rationale Snapshot
Current state, goals, rationale, completed work, workstreams, blockers, drift and recommended
attention.

Blueprint keeps separate coordination and portfolio views. Module self-view remains a proposal, not
portfolio authority.

## Evidence honesty

Substantive claims retain `verified`, `inferred`, `unknown`, `conflicting` and confidence
`high`, `medium`, `low`, `none`. A filename is not proof.

## Broader knowledge model

The maintained system may include RCI/REDM/SDRS, charters/target states, capability catalogs,
standards, public contracts, symbol/artifact indexes, dependencies, roadmap/design intent,
decisions/rationale, evidence and explicit unknown/stale/conflict queues.

Historical snapshots are never overwritten.

## Deterministic and semantic facts

Collectors derive tracked paths, hashes/Git deltas, symbols/signatures/classes,
imports/references where available, headings/anchors, Make targets and path/history facts.

Semantic owners maintain purpose, intent, owner, authority/lifecycle, reusable capability meaning,
dependency meaning, rationale and limitations.

Do not require manual descriptions for every private helper merely to satisfy a count.

## Inspector boundary

Project Inspector detects and reports structural/knowledge inconsistency; it does not author domain
semantic truth.

Preferred loop:

`Inspector detects -> module executor interprets/updates -> Inspector rechecks -> Blueprint governs`

Findings enter a severity-aware local queue and do not automatically interrupt active work.

## First full inventory

Use:

`deterministic structural map -> parallel semantic review -> reducer -> conflict/unknown queue -> targeted second review -> canonicalization`

Review assistants are read-only. Large refactors happen after semantic reconciliation.

## Incremental maintenance

After a trusted baseline, routine maintenance should be change-driven.

Candidate hierarchy:
- repository baseline = Git commit;
- file fingerprint = Git/blob/content identity;
- semantic-unit fingerprint = normalized function/class/document-section identity where useful.

Unchanged artifacts should not require full semantic re-review.

## Knowledge health

Completeness is risk-weighted. Critical classes include current authority, standards, active
roadmap, public contracts, major capabilities, active dependency paths and execution entrypoints.

Old low-risk historical artifacts may remain explicitly unresolved.

**Unknown is acceptable. Invisible unknown is not.**

## Search and projection

Canonical truth remains governed Git-readable artifacts.

A rebuildable SQLite/FTS or other index may later provide fast lookup/joins but must not become
second authority.

Prefer structured registry, symbol/reference search, full text, then semantic/vector retrieval when
justified. Semantic retrieval finds candidates; authority comes from canonical metadata.

## Module distribution

Every module should eventually receive local knowledge responsibilities, START_HERE navigation,
central standards lookup, semantic maintenance and Inspector-finding resolution.

Blueprint is the reference implementation before broad rollout.

## Readiness and cadence

Broad autonomous module execution requires Knowledge Foundation readiness, not 100% documentation.

Use incremental refresh around meaningful changes and deep reconciliation before major refactors,
major phase/release checkpoints, substantial drift or knowledge-health threshold breach.

## Rationale

Important decisions retain id/date, problem, decision, rationale, alternatives, affected modules,
expected result, prompt/report/commit evidence and current validity.

## Prohibited behavior

Do not hide unknowns, let generated indexes become authority, let Inspector invent module
semantics, refactor broadly before reconciliation, copy code merely because search found it,
overwrite snapshots, turn module proposals into Blueprint decisions, or activate autonomy merely
because this protocol exists.

Existing v0.2 snapshots remain valid historical evidence. Full v0.3 automation is a separate
roadmap workstream.
