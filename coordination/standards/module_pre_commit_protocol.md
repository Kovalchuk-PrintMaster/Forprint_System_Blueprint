# Module Pre-Commit Protocol

## Status

Active Blueprint standard / gradual adoption

## Purpose

Before any module commit, the assistant must prove that the module is aligned with Blueprint and locally healthy.

## Required pre-commit commands

```bash
make blueprint-check
make blueprint-sync-directives
make module-policy-check
make coordination-check
make check
make check-report
git status --short
```
Optional preview commands

If the module has preview targets, run relevant ones.

Examples:

make client-card-preview
make data-foundation-preview
make order-preview
make dictionary-preview
make dictionary-mapping-preview
Commit is blocked if

The assistant must not commit if:

tests fail;
lint fails;
check-report fails;
coordination metadata fails;
active directives are not synced;
current_status.yaml is invalid;
coordination/reports/index.yaml has missing report_file;
module-specific validation or boundaries blocks are removed;
accidental cache/generated garbage is staged.
Required post-commit evidence

After commit and push, the assistant must report:

Commit hash.
Push status.
Working tree status.
Check result.
Check-report result.
Coordination update.
Open questions.
Recommended next step.

---
