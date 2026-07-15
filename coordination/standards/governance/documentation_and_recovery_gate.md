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
