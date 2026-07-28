# ForPrint System Blueprint — Structure Assessment v0.1

## Decision

**COMPLETED — READY FOR FINAL BRANCH REVIEW**

The controlled structure cleanup is complete. The repository retains its governance and coordination model while metadata defects, Markdown structure debt and missing control documentation have been resolved through small, reviewable commits.

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
- Six ADR Markdown fence boundaries repaired and committed: `3e8a731`.
- Ratcheted Markdown fence validator and 63-entry baseline added: `53ad4cf`.
- Markdown fence validation integrated into the canonical Blueprint check catalog as check 24 of 24: `12a1401`.

### Current state

- Active cleanup record: this assessment.
- Completion report: `coordination/reports/completion/2026-07-28__blueprint__structure_cleanup_completion_v0_1.md`.
- Markdown fence debt is fully resolved: 69 identified defects across the cleanup sequence, a 63-entry ratchet baseline after the initial ADR repairs, and a final tracked baseline of 0.
- Final pre-closure validator state at `b85b117`: 263 Markdown files scanned, 0 current issues, 0 baseline issues, 0 new issues, 0 changed known issues and 0 stale baseline entries.
- Markdown validation is part of the canonical Blueprint check catalog as check 24 of 24.
- Full Blueprint validation passes: 24 OK, 0 warnings and 0 failed checks.
- `human/system_control_model.md` now exists as a standalone tracked control document.
- Legacy reporting-consolidation completion state remains unknown; no tracked references, live branches or accepted completion handoff evidence were identified during the internal-work audit.
- The removed source prompts remain recoverable from:
  - `../blueprint_pre_cleanup_baseline_2026-07-27/untracked-files.tar.gz`
  - `/tmp/forprint_blueprint_backups/reporting_consolidation_closeout_before_removal`

### Next controlled action

Create one documentation-only closure commit, repeat the full Blueprint checks, review the branch diff from `3f187876`, and then send the branch through the normal merge review. No additional structural changes are part of this closure wave.
