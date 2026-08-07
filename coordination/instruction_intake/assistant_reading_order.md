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

For a fresh assistant session or context handoff, read these two machine-oriented files before continuing the normal reading order:

1. `coordination/instruction_intake/bootstrap/assistant_bootstrap_v0_1.yaml`
2. `coordination/instruction_intake/bootstrap/current_handoff_v0_1.yaml`

The bootstrap file defines the stable operating model. The current handoff file defines the latest observed coordination state and is a baseline snapshot, not a substitute for Git, roadmap, prompt, audit, or governance checks.
