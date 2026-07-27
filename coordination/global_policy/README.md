# ForPrint Global Policy

## Purpose

This directory stores global ForPrint project policy documents.

These documents define the general strategic direction of the ecosystem and are intended to be read by all active module assistants.

This is not a place for short one-time tasks.

Use this directory for stable or semi-stable global project guidance:

```text
project doctrine;
ecosystem principles;
module role overview;
current execution focus;
global development rules;
architecture direction;
coordination expectations.
```
Difference from directives

coordination/global_policy/ contains long-lived global guidance.

coordination/directives/ contains active instructions or action-oriented tasks.

Example:

global_policy = what ForPrint is and how all modules should generally move
directives = what must be applied or checked now
Difference from standards

coordination/standards/ contains technical and structural standards.

Example:

make command standard;
repository structure baseline;
configuration policy;
reporting standard.
Module assistant rule

Each active module assistant should periodically read or refresh the global policy documents after pulling ForPrint System Blueprint.

The module assistant should use these documents to avoid drifting away from the overall ForPrint strategy.

Safety

Global policy documents must not contain:

secrets;
tokens;
passwords;
private client data;
real accounting data;
real 1C production data;
large logs;
binary files.

---
