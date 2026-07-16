# Blueprint Resolve Next Prompt Result Table Recovery Guide

## Source of truth

```text
scripts/coordination/resolve_next_prompt.py
scripts/reporting/coordination_result_tables.py
```

## Installer backup

Backups are stored under:

```text
.tmp_blueprint_backups/resolve_next_prompt_result_table_<timestamp>/
```

## Critical contracts to restore

```text
--path-only stdout must be byte-identical;
invalid-module stdout and exit code must be byte-identical;
prompt body after the read separator must be byte-identical;
the command must remain read-only.
```

## Verification

```bash
python -m pytest -q \
  tests/reporting/test_resolve_next_prompt_result_table.py

NO_COLOR=1 python \
  scripts/coordination/resolve_next_prompt.py \
  --module forprint_library

python \
  scripts/coordination/resolve_next_prompt.py \
  --module forprint_library \
  --path-only
```

## Recovery boundary

Do not restore or modify unrelated files under:

```text
coordination/outgoing_prompts/website/
coordination/risk_registers/
coordination/roadmaps/website.yaml
```
