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

know where Blueprint standards are located;
be able to list readable Blueprint standards;
include standards visibility in governance checks;
mention standards reviewed in completion reports when relevant;
gradually align with standards through small safe steps;
report conflicts instead of doing destructive rewrites.
Standards location

The global standards entry point is:

coordination/standards/index.yaml

The human overview is:

coordination/standards/README.md

Root-level standards and grouped standards are both valid.

Current standards groups include:

coordination/standards/governance/
coordination/standards/modular_topology_and_resilience/
coordination/standards/third_party_reuse/
Required module behavior

A module should expose or gradually add:

make blueprint-standards-list
make blueprint-standards-check
make blueprint-standards-sync

These targets may initially be lightweight.

They should confirm that Blueprint standards are readable and that the module can see the standards index.

They should list standards recursively enough to include thematic standards groups.

Important packages for mature modules

Modules that touch cross-module integration, databases, durable handoff, Gateway, external services, queues, reporting, authentication or runtime behavior should review:

coordination/standards/modular_topology_and_resilience/
coordination/standards/third_party_reuse/

Modules that work on standards layout or Blueprint internal organization should review:

coordination/standards/governance/
Advisory default

Unless a standard is referenced by an active prompt or an active directive, it should be treated as:

read continuously;
consider during implementation;
apply only when safe;
report conflicts;
do not perform large destructive refactors automatically.
Completion report expectation

Completion reports should gradually include:

standards_reviewed:
  - coordination/standards/index.yaml
  - coordination/standards/module_standards_awareness_protocol.md
  - coordination/standards/modular_topology_and_resilience/
  - coordination/standards/third_party_reuse/

standards_alignment_notes:
  - "No destructive rewrite was performed."
  - "Target standard alignment deferred to future small prompt."

When a module reviewed a specific standard, it may list the exact file:

standards_reviewed:
  - coordination/standards/modular_topology_and_resilience/module_interaction_reliability_policy.md
  - coordination/standards/third_party_reuse/third_party_reuse_policy.md
Governance expectation

Module governance checks should eventually confirm:

Blueprint standards path readable;
standards index readable;
standards list command available;
standards check command available;
standards sync command available;
thematic standards groups visible.

This is a visibility and synchronization requirement first.

It is not full hard compliance with every standard.

Forbidden behavior

A module must not:

treat every standard as immediate permission for large rewrites;
ignore standards groups because they are in subdirectories;
introduce a third-party production dependency without classifying reuse mode;
change cross-module data ownership locally;
silently hide standards conflicts from Blueprint.
Boundary

This protocol defines standards visibility and awareness.

It does not define every standard's content.

Specific policies remain in their own files and packages.
