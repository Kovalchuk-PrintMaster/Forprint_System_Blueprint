# ForPrint Module Policy

## Purpose

This directory stores Blueprint-owned strategic policy for each ForPrint module.

It complements:

```text
coordination/global_policy/
coordination/directives/
coordination/standards/
coordination/module_docs_snapshots/
Difference from global policy

coordination/global_policy/ defines the strategy for the whole ForPrint ecosystem.

coordination/module_policy/<module_id>/ defines the strategic role, goals, boundaries and development focus for one specific module.

Difference from directives

coordination/directives/ contains active instructions or action-oriented tasks.

coordination/module_policy/ contains longer-lived module-specific strategy.

Example:

module_policy = what this module is supposed to become
directives = what this module should do now or next
Difference from module docs snapshots

coordination/module_docs_snapshots/ stores reviewed or collected documentation snapshots from module repositories.

coordination/module_policy/ stores Blueprint/owner expectations for the module.

These two views should be compared during architecture reviews:

Blueprint module policy
vs.
module self-declared documentation
Required module policy structure

Recommended structure:

coordination/module_policy/<module_id>/
├── module_goals.md
├── role_boundaries.md
└── development_focus.md
Adoption mode

Module policy is strategic guidance.

It does not automatically authorize large refactors or broad rewrites.

Module assistants should:

read module policy;
compare it with current module status;
report what already matches;
report what conflicts;
ask Blueprint before large restructuring.
Safety

Module policy files must not contain:

secrets;
tokens;
passwords;
private client data;
real accounting data;
real 1C production data;
large logs;
binary files.

---
