# Makefile Operator Functional Map Policy v0.1

## Status

Active Blueprint governance standard.

## Purpose

For ForPrint projects, `Makefile` is not only a command launcher. It is an
operator-facing functional map of the supported project workflows.

## Required invariant

When a supported implementation exposes a meaningful operator workflow, the
corresponding command surface must be represented in the appropriate Makefile
section with clear operator semantics.

The inverse is also required: when functionality is retired, removed, or no
longer supported, obsolete Make targets that advertise that functionality must
be removed or explicitly reclassified. Stale targets are governance defects.

## Closeout rule

Any bounded implementation or reconciliation task that:

- creates a new supported operator workflow;
- materially changes an existing operator workflow;
- discovers an already-implemented operator workflow that is missing from
  Makefile; or
- removes/retires functionality represented by Makefile

must include a Makefile coverage review before the task is considered fully
closed.

## Command semantics

Operator-facing Make targets should make their purpose, safety, inputs/scope,
and expected result understandable from the project Makefile structure and
associated command documentation.

Read-only checks must remain read-only. Mutation, activation, acceptance,
release, commit, push, merge, or other authority-bearing actions must not be
hidden behind targets presented as status/check commands.

## Coverage audit rule

A Makefile functional coverage audit compares the live supported capability /
operator-workflow inventory against the Makefile surface.

Classify findings as:

- `COVERED` — supported workflow is represented correctly;
- `MISSING_TARGET_OR_ROUTE` — supported operator workflow exists but Makefile
  does not expose it;
- `STALE_TARGET` — Makefile advertises functionality that no longer exists;
- `SEMANTIC_DRIFT` — target exists but its name/purpose/safety contract no
  longer matches the implementation;
- `INTERNAL_ONLY_NOT_OPERATOR_SURFACE` — implementation exists but is
  intentionally not an operator command;
- `DEFERRED_WITH_REASON` — coverage is intentionally deferred with an explicit
  bounded reason.

Historical target names must not be recreated solely because they appear in old
dialogues or reports. Live implementation and current authority determine the
current functional map.

## Authority

This policy governs discoverability and operator workflow coverage. It does not
grant execution, lifecycle, dispatch, roadmap, acceptance, release, commit,
push, or merge authority.
