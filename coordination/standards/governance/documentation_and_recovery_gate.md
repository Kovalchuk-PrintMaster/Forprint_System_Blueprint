# ForPrint Documentation and Recovery Gate

## Status

Active standard / gradual alignment v0.1

## Purpose

This standard ensures that important ForPrint coordination and automation work remains transparent, reviewable and recoverable after a long interruption, assistant replacement or chat-context loss.

## Core rule

A meaningful coordination mechanism is not complete when only the code works.

It is complete when another qualified assistant can understand, verify, operate and recover it from repository evidence.

## Required documentation layers

For substantial automation or architecture work, maintain:

```text
architecture document;
operator runbook;
recovery guide;
applicable standards;
automated tests;
completion report;
current prompt and roadmap evidence.
```

Small changes may update existing documents instead of creating new ones.

## Seven required questions

Documentation must answer:

```text
What changed?
Why did it change?
Where is the source of truth?
Which commands should an operator use?
Which artifacts are generated?
How is correctness verified?
How is context recovered after interruption?
```

## Recovery requirements

A recovery guide should allow a new assistant to establish:

```text
current Git branch and working-tree state;
latest accepted and active prompts;
current roadmap step;
relevant architecture and standards;
last green checks;
warnings, blockers and decisions;
stable report and diagnostic paths;
next safe action.
```

## No chat-only decisions

Important decisions, constraints and workflow rules must not exist only in chat history.

They must be transferred to repository documentation, prompt metadata, roadmap evidence, standards, review packets or completion reports.

## Durable history without document noise

Repository history should preserve meaningful control points, not every
intermediate attempt.

A significant completed implementation, architectural choice, governance
change, module/path decision or milestone closeout should leave durable evidence
that makes clear:

```text
what changed;
why the decision was taken;
which prior rule or assumption was retained, revised or superseded;
what is authoritative now;
which tests, evidence or commit establish the result;
which roadmap, prompt or release state is affected;
what is intentionally deferred.
```

Tiny fixes, failed intermediate mutations and temporary experiments do not each
require permanent records unless they materially explain the final architecture.

When the same concern continues, update the existing authoritative document.
Create a new revision only when semantics or authority materially change, and
make supersession/deprecation explicit. Prefer one meaningful final closeout
record over a long chain of near-identical intermediate documents.

## Operator-facing script delivery contract

The normal operator interface intentionally uses a small terminal paste surface.

Commands supplied for direct terminal paste must stay short: no more than about
15 lines, and preferably 1-3 lines.

Multi-step collectors, mutation transactions, archive builders, diagnostics or
other longer procedures must be delivered as a downloadable, versioned Python
file intended to be placed in the repository root as `tmp.py`.

Do not require long shell heredocs or long pasted shell programs.

A delivered helper should print an explicit `SCRIPT_ID`, a clear final result
and, when it creates an artifact, the artifact path and hash.

Temporary evidence and generated diagnostic bundles belong under repository
`tmp/` or another explicitly temporary output location. Durable decisions and
project history belong in tracked project documents.

This interface is part of recovery continuity: a replacement assistant should
be able to follow it without asking the operator to explain the workflow again.

## Definition of done

A substantial workflow change is ready to close when:

```text
implementation exists;
tests pass;
routine and diagnostic commands are documented;
architecture and ownership boundaries are documented;
recovery steps are documented;
completion evidence is stored;
the next documented action is visible.
```
