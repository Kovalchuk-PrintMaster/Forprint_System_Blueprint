# Blueprint Reporting Consolidation Audit v0.1

## Date

2026-07-15

## Baseline

```text
branch: feature/blueprint-reporting-consolidation-audit-v01
commit: d073cd5
mode: read-only
```

## Evidence collected

```text
108 Python files scanned by the exploratory audit;
139 presentation/helper functions detected;
34 strong presentation signals;
JSON outputs validated;
five highest-ranked candidates inspected at source level.
```

## Corrected findings

The exploratory score was useful for discovery but overestimated migration
debt. Source-contract inspection corrected the classifications.

### Shared reporting core

```text
table_renderer.py
statuses.py
models.py
artifact_writer.py
console_summary.py
coordination_result_tables.py
document_awareness_tables.py
```

### Already consolidated

```text
run_blueprint_checks.py
render_document_awareness_dashboard.py
render_module_roadmap_dashboard.py
module_completion_intake.py
resolve_next_module_work.py
render_prompt_dashboard.py
```

### Verified partial migration

```text
scripts/coordination/module_roadmap.py
```

Residual helpers:

```text
_row
_boxed_table
_token_color
```

`_boxed_table` already delegates to `render_boxed_table_lines`, so the next
front is cleanup and contract simplification rather than renderer replacement.

## Decision

Approved next implementation front:

```text
blueprint_module_roadmap_renderer_cleanup_v0_1
```

Preserve:

```text
roadmap YAML schema;
validation behavior;
current-step derivation;
window semantics;
CLI arguments;
NO_COLOR behavior;
Makefile targets;
dashboard and modules-summary content.
```

## Deferred review queue

```text
resolve_next_prompt.py;
audit_module_governance.py;
update_document_awareness_ledger.py;
validate_module_roadmap.py;
validate_prompt_queue.py;
metadata and standards validators;
generator terminal/artifact separation.
```
