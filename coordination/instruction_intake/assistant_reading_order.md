# Assistant Instruction Intake Protocol

Status: active protocol v0.1

This protocol defines how every ForPrint module assistant should read Blueprint instructions before starting work.

## Goal

All modules must develop inside one ForPrint ecosystem concept while still allowing different modules to have different roles, maturity levels, complexity, priorities and implementation depth.

This protocol is the common entry point for assistant work.

## Source of truth

ForPrint System Blueprint is the source of truth for shared ecosystem instructions.

Module-local snapshots are audit evidence only. They are not permanent sources of truth.

Before every new prompt or work session, the assistant should refresh its understanding from Blueprint source files.

## Required reading order

1. Instruction intake index.
2. Global policy and ecosystem constraints.
3. Active directives.
4. Module policy for the target module.
5. Direct outgoing prompt for the target module.
6. Standards index and relevant standards.
7. Current module status, reports and previous completion records.
8. Local implementation details.

## Priority model

Global policy and active directives can block or override a direct prompt.

Module policy defines ownership boundaries.

Direct outgoing prompt defines the current task.

Standards are advisory or target guidance by default unless activated by prompt or directive.

Local implementation details must not override Blueprint ownership boundaries.

## Conflict handling

If instructions conflict, the assistant must not guess or silently choose the convenient option.

The assistant should stop the conflicting part of work and report a question to Blueprint using the configured feedback path.

## Maturity-aware execution

Modules may be mature, young, experimental, helper-like, core, peripheral, high-complexity or low-complexity.

The assistant should not apply the same depth of refactoring or structure to every module.

Module profiles are composable traits, not rigid module classes.

A young core module may prioritize foundation functionality.

A mature module may prioritize standardization, cleanup, governance and structure.

A lightweight helper may keep a simple structure while still respecting global policy.

## Blueprint assistant bootstrap handoff entrypoint

For a fresh assistant session or context handoff, read these machine-oriented bootstrap and roadmap-enrichment surfaces before continuing the normal reading order:

1. `coordination/instruction_intake/bootstrap/assistant_bootstrap_v0_2.yaml`
2. `coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml`
3. `coordination/standards/governance/roadmap_enrichment_and_knowledge_saturation_operating_guide_v0_1.md`
4. `coordination/repository_knowledge/roadmap_enrichment/README.md`
5. `coordination/repository_knowledge/roadmap_enrichment/source_map.yaml`

The bootstrap file defines the stable operating model and routing. The current handoff file defines the latest observed coordination state and is a baseline snapshot, not a substitute for Git, roadmap, prompt, audit, release, or governance checks.

For bulk roadmap enrichment, the operating guide defines the stable method while the living field guide and source map provide reusable navigation, fast paths, pitfalls, provenance, and source-role hints. Living knowledge is advisory navigation and does not grant implementation, binding, activation, release, or publication authority.

<!-- fp-assistant-context-system-specs-route-v0-1:start -->
## Blueprint assistant operating context

After this canonical reading-order document, read:

`coordination/bootstrap/assistant_context_system_specs_v0_1.yaml`

This system-spec file is a navigation supplement for current Blueprint work.
It does not replace this document, current lifecycle/workfront authority,
canonical governance, or live repository verification.
<!-- fp-assistant-context-system-specs-route-v0-1:end -->

<!-- module-snapshot-roadmap-rebuild-analysis-mode-v0-1:start -->
## Portfolio module snapshot mode

When the task is deep module analysis, current-state reconstruction, roadmap enrichment,
knowledge saturation, or preparation for roadmap rebuild, read:

`coordination/bootstrap/module_snapshot_and_roadmap_rebuild_analysis_mode_v0_1.md`

before interpreting repository divergence.

In this mode the assistant must not assume that an old, inconsistent or strategically
misaligned module surface should be fixed during the audit. The assistant records actual
implementation, historical design, roadmap coverage, strategic divergence and future
alignment needs. Implementation remains a separate explicitly authorized task.
<!-- module-snapshot-roadmap-rebuild-analysis-mode-v0-1:end -->
