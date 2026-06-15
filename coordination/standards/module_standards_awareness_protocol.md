# ForPrint Module Standards Awareness Protocol

Status: active standard / gradual adoption
Created: 2026-06-15T14:32:38.478269+00:00

## Purpose

This protocol defines how ForPrint modules continuously read Blueprint standards.

Standards are the long-running synchronization layer for the whole ForPrint ecosystem.

They are different from outgoing prompts.

## Core distinction

```text
outgoing_prompts = concrete work that should be done now
standards        = continuously readable guidance and target direction
directives       = mandatory rule when explicitly marked active/blocking
global_policy    = ecosystem-wide constraints and doctrine

Standards behavior

Blueprint standards are not automatically equivalent to an active prompt.

A module is not required to implement every standard immediately only because the standard exists.

However, every active module should:

1. know where Blueprint standards are located;
2. be able to list readable Blueprint standards;
3. include standards visibility in governance checks;
4. mention standards reviewed in completion reports when relevant;
5. gradually align with standards through small safe steps;
6. report conflicts instead of doing destructive rewrites.
Required module behavior

A module should expose or gradually add:

make blueprint-standards-list
make blueprint-standards-check
make blueprint-standards-sync

These targets may initially be lightweight.

They should confirm that Blueprint standards are readable and that the module can see the standards index.

Advisory default

Unless a standard is referenced by an active prompt or an active directive, it should be treated as:

read continuously
consider during implementation
apply only when safe
report conflicts
do not perform large destructive refactors automatically
Completion report expectation

Completion reports should gradually include:

standards_reviewed:
  - coordination/standards/module_governance_protocol.md
  - coordination/standards/make_command_standard.md

standards_alignment_notes:
  - "No destructive rewrite was performed."
  - "Target standard alignment deferred to future small prompt."
Governance expectation

Module governance checks should eventually confirm:

Blueprint standards path readable
standards index readable
standards list command available
standards check command available

This is a visibility and synchronization requirement first.

It is not full hard compliance with every standard.
