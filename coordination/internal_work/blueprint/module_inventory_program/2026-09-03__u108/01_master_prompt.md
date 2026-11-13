# MASTER PROMPT — Portfolio Inventory, Reconciliation, Indexing, and Module Bootstrap

## Role
Continue the ForPrint System Blueprint portfolio-governance project. Do not begin by implementing module features. First make the portfolio understandable, internally consistent, indexed, governable, and safe for later autonomous work.

## Current operating constraints
Unless the human explicitly changes them:
- ASSISTANT_DISTRIBUTION_ALLOWED=false
- MODULE_IMPLEMENTATION_STARTED=false
- PROMPT_ACTIVATION=false
- AUTOMATIC_ACCEPTANCE=false
- AUTOMATIC_RELEASE_NEXT_PROMPT=false
- H10_WIDENED=false
- COMMIT_PERFORMED=false
- PUSH_PERFORMED=false

## Primary objective
Before a module receives normal autonomous work, establish durable evidence of:
1. module purpose;
2. owned semantics;
3. forbidden semantics;
4. current implementation;
5. planned-only work;
6. legacy/abandoned/duplicate implementation;
7. dependencies;
8. current Blueprint architectural obligations;
9. canonical instruction path;
10. prompt intake and completion-report flow;
11. local inventory/index maintenance;
12. next approved roadmap steps.

## Repository analysis method
For large repositories, do not repeatedly scan the whole tree in one chat turn. Partition into logical archive batches. The human uploads one archive at a time. Analyze every batch using the same schema, return a durable report, and let the human store it in the module inventory working directory.

After all batches:
- consolidate findings;
- resolve or surface contradictions;
- build capability inventory;
- build implementation-lineage map;
- build documentation-authority map;
- build ownership-conflict map;
- map tests/evidence;
- reconcile roadmap;
- enrich Blueprint;
- only then design/build module-local index, AGENTS.md, coordination v0.4.1 support, and inventory tooling.

## Evidence labels
Use:
- VERIFIED_LOCAL_REPOSITORY
- VERIFIED_RUNTIME
- BLUEPRINT_CANONICAL_DOCUMENTATION
- HUMAN_CONFIRMED
- PROPOSED
- UNKNOWN
- HISTORICAL_ONLY
- DEPRECATED
- CONFLICTING_EVIDENCE

A repository file proves presence, not necessarily active production use or canonical authority.

## Legacy-code rule
Older modules, especially Calculator and Telegram Bot, may contain multiple implementation generations created under different architectural assumptions.

For each competing implementation family:
- identify paths and likely lineage;
- identify entrypoints/importers/tests/usages;
- determine active / partial / dead / unknown;
- compare with current Blueprint ownership;
- identify useful reusable logic;
- identify functionality that belongs to another module;
- propose disposition.

Disposition vocabulary:
KEEP_CURRENT / KEEP_BUT_ISOLATE / DEPRECATE / HISTORICAL_ONLY /
REWRITE / MERGE / MOVE_OWNERSHIP_CANDIDATE / REMOVE_CANDIDATE /
NEEDS_OWNER_REVIEW / UNKNOWN

Do not auto-delete.

## Documentation reconciliation
Conflicting documentation is a first-class defect because future autonomous assistants may follow incompatible instructions.

Classify important documents:
CANONICAL_CURRENT / CURRENT_SUPPORTING / NEEDS_REWRITE / DEPRECATED /
HISTORICAL_ONLY / CONFLICTING / DUPLICATE / REMOVE_CANDIDATE / UNKNOWN

Compare:
- code vs docs;
- docs vs docs;
- docs vs Blueprint;
- old prompt/report flows vs current v0.4.1;
- old ownership vs current ownership.

Prefer deprecation/archive/isolation over destructive removal until authority is clear.

## Cross-module ownership
If useful code no longer belongs to the current module, do not silently preserve wrong semantic ownership and do not move code during inventory. Record:
- current location;
- behavior;
- likely target owner;
- consumers;
- extraction risk;
- temporary isolation;
- required contract;
- migration prerequisites.

## Roadmap enrichment
After consolidation:
1. compare evidence with roadmap;
2. mark implemented only when evidence supports intended semantics;
3. identify partial implementation;
4. add useful discovered capabilities as PROPOSED;
5. add cleanup/migration/contract/test work;
6. preserve AGREED/HUMAN-CONFIRMED vs PROPOSED;
7. maintain approximately ten meaningful forward steps;
8. expose dependencies so one module cannot run far ahead of prerequisites.

Every mature module needs: “At mature state, this module ...”

## Required module bootstrap substrate
Before real autonomous work, each module should have:
- repository inventory/index;
- clear AGENTS.md;
- coordination/reporting v0.4.1 compatibility;
- local deterministic inventory/index maintenance tooling;
- known validation commands;
- explicit stop/escalation conditions.

## Fresh-context continuity
The process must survive context reset. A new assistant should be able to continue from durable Blueprint files without reconstructing the project from long chat history.

Minimum durable handoff:
- AGENTS.md/bootstrap;
- current release/gates;
- module identity registry;
- portfolio roadmap state;
- inventory-program state;
- per-module inventory progress;
- unresolved conflicts;
- current module/batch;
- completed/pending archive reports;
- exact next action.

## Stop conditions
Stop for human/Blueprint review if:
- sources claim incompatible canonical authority;
- moving functionality changes semantic ownership;
- destructive cleanup touches potentially live behavior;
- implementation lineage remains ambiguous;
- secrets/prod data appear;
- contract activation would be required;
- a roadmap change widens execution authority;
- implementation would start before readiness.

## Output for each archive
Return a structured batch report using the provided template, with explicit VERIFIED / PROPOSED / HISTORICAL_ONLY / UNKNOWN labels.
