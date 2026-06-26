# Third-Party Reuse Standards

This standards package defines how ForPrint may evaluate, reuse, sandbox or depend on third-party tools, frameworks and platforms.

The goal is to keep ForPrint lightweight, controllable, debuggable and locally understandable while still allowing practical reuse of commodity infrastructure.

ForPrint should build its own domain core and reuse third-party tools only where they reduce risk or operational cost without taking ownership away from ForPrint modules.

Read in this order:

1. `third_party_reuse_policy.md`

This standard is advisory by default and becomes binding only when referenced by a Blueprint prompt, directive or architecture decision.
