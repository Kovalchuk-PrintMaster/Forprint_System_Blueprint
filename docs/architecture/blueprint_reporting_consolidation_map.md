# Blueprint Reporting Consolidation Map

## Status

Verified architecture map v0.1.

## Shared reporting core

The following files are the canonical presentation layer:

```text
scripts/reporting/table_renderer.py
scripts/reporting/statuses.py
scripts/reporting/models.py
scripts/reporting/artifact_writer.py
scripts/reporting/console_summary.py
scripts/reporting/coordination_result_tables.py
scripts/reporting/document_awareness_tables.py
```

They own:

```text
closed terminal tables;
visible-width and ANSI-safe truncation;
semantic status tokens;
compact Blueprint check summaries;
coordination result tables;
document-awareness result tables;
report artifact writing.
```

## Verified consolidated consumers

```text
scripts/run_blueprint_checks.py
scripts/coordination/render_document_awareness_dashboard.py
scripts/coordination/render_module_roadmap_dashboard.py
scripts/coordination/module_completion_intake.py
scripts/coordination/resolve_next_module_work.py
scripts/coordination/render_prompt_dashboard.py
```

`render_module_roadmap_dashboard.py` is a CLI wrapper. It must not absorb table
construction logic.

The awareness dashboard retains semantic color selection, but its tables are
owned by `document_awareness_tables.py`.

`run_blueprint_checks.py` retains compatibility helpers and delegates compact
console output and JSON/Markdown artifact generation to the reporting package.

## Verified residual debt

```text
scripts/coordination/module_roadmap.py
```

It already delegates border rendering to the shared renderer but retains:

```text
_row
_boxed_table
_token_color
```

This is a partial migration, not a separate renderer implementation.

## Artifact boundaries

Do not convert these outputs into terminal box tables:

```text
JSON reports;
Markdown reports;
context-bundle Markdown;
document-manifest Markdown;
generated policy and guide documents.
```

Terminal presentation may be consolidated only after it is separated from
artifact generation.

## Planning horizon

1. `blueprint_module_roadmap_renderer_cleanup_v0_1`
2. `blueprint_resolve_next_prompt_result_table_v0_1`
3. `blueprint_module_governance_terminal_artifact_split_v0_1`
4. `blueprint_document_ledger_result_table_v0_1`
5. `blueprint_module_roadmap_validation_result_table_v0_1`
6. `blueprint_prompt_queue_validation_result_table_v0_1`
7. `blueprint_metadata_validation_result_tables_v0_1`
8. `blueprint_standards_validation_result_tables_v0_1`
9. `blueprint_generator_terminal_artifact_split_v0_1`
10. `blueprint_reporting_consolidation_reaudit_v0_2`

Only step 1 is approved for immediate implementation. Later steps require
their own source-contract audit.
