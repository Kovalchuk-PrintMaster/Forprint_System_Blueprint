# ForPrint Module Policy

## Purpose

This directory stores Blueprint-owned strategic policy for each ForPrint module.

It complements:

```text
coordination/global_policy/
coordination/directives/
coordination/standards/
coordination/module_docs_snapshots/
```
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

## Reporting and completion obligations

These obligations apply to module assistants when the module exposes reporting,
audit or status commands.

### Required

Module assistants must:

- preserve public Make target names, CLI flags, machine schemas, artifact
  filenames, stdout/stderr ownership and exit-code semantics;
- keep commands documented as read-only free of coordination-state mutation;
- keep warning and failure information visible;
- document source-of-truth files and stable artifact paths;
- create architecture, runbook, recovery and completion documentation for
  substantial reporting or orchestration changes;
- report deviations explicitly instead of silently changing contracts;
- keep important implementation decisions in repository documentation rather
  than only in assistant chat.

### Conditional

When ANSI color exists, `NO_COLOR=1` must disable it without changing data,
artifacts or exit codes.

When detailed JSON or Markdown report artifacts exist, routine terminal output
should remain compact and the completion packet should reference those
artifacts. Modules without report artifacts must not invent them.

When a full diagnostic renderer exists, expose it through the documented
extended target rather than overloading routine compact output.

### Completion evidence

Completion packets should conditionally record focused tests, full tests, lint,
`make check-report`, `git diff --check`, artifact validation, read-only
verification, `NO_COLOR=1` verification, recovery documentation and known
deviations.

Target definitions remain owned by:

- `coordination/standards/module_governance_make_targets.md`;
- `coordination/standards/make_command_standard.md`;
- `coordination/standards/module_make_target_contract.md`.

Module policy references these standards and does not duplicate the complete
target list. Existing generated per-module policies are not bulk-rewritten by
this closeout.

<!-- theory-target-state-discovery-20260826:start -->
## Provisional target-state addenda — 2026-08-26

`module_policy.md` files in module subdirectories are generated from
`coordination/module_policy/module_policy_index.yaml` and must remain generator-consistent.

The following non-generated target-state addenda preserve owner/theory direction for the portfolio
roadmap rebuild without claiming current implementation:

- `forprint_accounting_registry_service/goods_receipt_automation_target_state_v0_1_20260826.md`
- `forprint_operations_assistant/physical_quantity_estimation_target_state_v0_1_20260826.md`
- `forprint_library/canonical_catalog_and_external_ingestion_target_state_v0_1_20260826.md`
- `calculator_engine/calculator_target_state_v0_1_20260826.md`
- `telegram_bot/telegram_conversational_operating_interface_target_state_v0_1_20260826.md`

Project Inspector knowledge responsibility is governed centrally by:

`coordination/standards/knowledge/knowledge_maintenance_and_inspector_boundary_v0_1.md`

These addenda are `PROVISIONAL / SYNTHETIC` planning inputs. They do not override generated module
policy authority or prove that the described capability already exists.
<!-- theory-target-state-discovery-20260826:end -->
