# Directive Index Schema Standard

## Status

Active standard

## Purpose

This document defines the canonical structure for Blueprint directive indexes.

Module assistants and sync scripts must not guess directive index structure.

## Canonical module directive index structure

The canonical structure for module-specific directive indexes is:

```yaml
module_directives:
  version: "0.1"
  module_id: "<module_id>"
  active:
    - directive_id: "<directive_id>"
      status: active
      priority: p0
      created_at: "YYYY-MM-DD"
      file: "coordination/directives/modules/<module_id>/active/<directive_id>.md"
      summary: >
        Short directive summary.
      requires_acknowledgement: true
      expected_report_id: "<expected_report_id>"
      expected_module_action: >
        Expected module action.
  archived: []
```

Canonical active directive path

Active directives must be read from:

module_directives.active
Canonical archived directive path

Archived directives must be read from:

module_directives.archived
Required parser behavior

Directive sync scripts should:

1. read module_directives.active;
2. import active directives that are not yet present locally;
3. skip already imported directives;
4. avoid duplicate prompt_id/directive_id entries;
5. preserve directive_id as prompt_id when imported into local module coordination;
6. copy the directive markdown file into coordination/prompts/received/ or another approved local inbox;
7. update local coordination/prompts/index.yaml.
Backward compatibility

Sync scripts may optionally support fallback structures:

directives
prompts

But these are not canonical.

They should only be used for compatibility with older or temporary files.

Standardization rule

New Blueprint directive indexes must use:

module_directives.active
module_directives.archived

Any module sync implementation that reads another structure first must be corrected.

Operational note

Blueprint freshness, local readability, and directive import are separate actions.

These are separate actions:

coordination-sync-check = explicit remote read-only freshness gate used by module-start
blueprint-check = verify expected Blueprint paths exist locally
blueprint-sync-directives = import active module directives into local module coordination inbox

blueprint-pull is deprecated and must not update Blueprint from a module repository.
CWD safety rule

Module Makefile targets should be runnable from the module root.

Scripts should avoid relying on accidental current working directory.

Where possible, paths should be resolved from:

module_root
blueprint_root
coordination/blueprint_source.yaml

---
