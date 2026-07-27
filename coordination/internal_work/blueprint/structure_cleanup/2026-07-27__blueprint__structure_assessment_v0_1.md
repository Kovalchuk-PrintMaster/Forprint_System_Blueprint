# ForPrint System Blueprint — Structure Assessment v0.1

## Decision

**READY FOR CONTROLLED STRUCTURE CLEANUP**

The repository already contains a meaningful governance and coordination system. The next phase should improve information architecture and consistency rather than introduce another layer or perform a broad rewrite.

## Highest-priority findings

- Fix two duplicate YAML-key defects before trusting all loaded metadata.
- Repair and lint Markdown fenced-code structure.
- Establish one canonical module-ID registry with legacy aliases.
- Reconcile prompt queues, roadmaps, current focus and completion evidence.
- Classify repository roots as canonical, operational, generated, historical or temporary.
- Reorganize the Makefile around operator workflows while preserving stable target names.
- Add automated structure and metadata-consistency audits.
- Refresh stale reports only after the metadata cleanup.
- Complete the current Blueprint self-audit handoff.
- Begin assistant documentation alignment only after Blueprint's own control surface is consistent.

## Recommended information layers

- **Canonical architecture:** `machine/`, accepted ADRs, global policy and module policy.
- **Operational coordination:** prompt queues, roadmaps, incoming requests, review packets and active directives.
- **Generated views:** module guides, diagrams, current dashboards and generated policy documents.
- **Historical evidence:** immutable repository snapshots, accepted completion records and archived prompts.
- **Working state:** `operator_input/`, `tmp/`, diagnostics and local caches.

## Recommended Make workflow layer

Keep the current atomic targets. Add composite operator targets such as:

```text
blueprint-start
blueprint-status
blueprint-docs-check
coordination-status
module-review MODULE=<id>
completion-review MODULE=<id> PACKET=<path>
repository-knowledge-audit
blueprint-maintenance
```

Each composite target should call existing targets through `$(MAKE)`, document Purpose and Result, and avoid hidden writes.

## Safety rule

Do not mass-move or delete files until automated reference checks, source-of-truth classification and compatibility aliases are in place.

## Cleanup progress

### Completed

- Duplicate YAML keys repaired and verified: commit `87d51fe`.
- Gateway prompt compliance restored; full Blueprint check is green.
- Website roadmap and legacy risk controls normalized and committed: `474521e`.
- Legacy untracked reporting-consolidation prompts removed from the working tree after verification that all three exist in the pre-cleanup baseline archive.

### Current state

- Active cleanup record: this assessment.
- Legacy reporting-consolidation completion state: unknown; no tracked references, live branches, or accepted completion handoff evidence were identified during the internal-work audit.
- The removed source prompts remain recoverable from:
  - `../blueprint_pre_cleanup_baseline_2026-07-27/untracked-files.tar.gz`
  - `/tmp/forprint_blueprint_backups/reporting_consolidation_closeout_before_removal`

### Next controlled action

Run a repository-wide Markdown fence audit, then add it as a permanent read-only Make validation target.
