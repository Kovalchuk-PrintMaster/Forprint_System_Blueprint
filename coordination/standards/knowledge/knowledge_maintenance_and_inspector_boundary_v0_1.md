# ForPrint Knowledge Maintenance and Project Inspector Boundary v0.1

## Project Inspector

Inspector detects, measures, correlates and reports:
- changed but unindexed artifacts;
- stale knowledge records;
- missing metadata;
- broken references;
- new public symbols/contracts;
- removed/moved artifacts;
- dependency drift;
- standards-discoverability drift;
- knowledge-health threshold changes;
- structural anomalies.

Inspector does **not** own module semantic truth and does not autonomously author semantic inventory
for business modules.

## Local module executor

The local executor is semantic maintainer for its repository under Blueprint standards. It explains
purpose/intent, updates capability records, resolves knowledge findings, records rationale when
required, and preserves uncertainty instead of inventing facts.

## Blueprint

Blueprint owns central standards, readiness rules, severity/blocking classification, exceptions and
portfolio dependency/priority decisions.

## Deterministic collector

Inspector may consume a deterministic collector/indexer for Git deltas, hashes, AST symbols,
imports, headings, Make targets and path existence. Deterministic collection should remain separate
from semantic authorship.

## Finding lifecycle

`DETECTED -> CLASSIFIED -> LOCAL_MAINTENANCE_QUEUE -> RESOLVED -> RECHECKED -> CLOSED/ESCALATED`

A finding does not automatically interrupt active work.

Suggested classes:
- `BLOCKING` — dependent work is unsafe/ambiguous;
- `HIGH` — nearest maintenance checkpoint;
- `NORMAL` — scheduled local knowledge refresh;
- `LOW_HISTORICAL` — deep reconciliation later.

Candidate checkpoints include significant Work Package completion, roadmap-step close,
phase/release boundary, major API/contract/standard change, and knowledge-health threshold breach.

## Resolution evidence

Preserve finding id, resolver, semantic artifacts updated, rationale, checks/evidence and resulting
status. Inspector then rechecks the objective inconsistency.

Safe deterministic/generated repairs may later be automated under an explicit safe-repair class.
Semantic rewrites, architecture decisions, destructive actions and cross-repository changes remain
governed separately.
