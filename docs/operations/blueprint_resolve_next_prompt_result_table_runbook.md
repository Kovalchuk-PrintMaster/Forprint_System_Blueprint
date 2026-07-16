# Blueprint Resolve Next Prompt Result Table Runbook

## Default summary

```bash
NO_COLOR=1 python \
  scripts/coordination/resolve_next_prompt.py \
  --module forprint_library
```

Expected:

```text
ForPrint Next Prompt
closed boxed metadata table
exit code 0
```

## Path-only contract

```bash
python \
  scripts/coordination/resolve_next_prompt.py \
  --module forprint_library \
  --path-only
```

Expected: exactly one plain relative path line.

## Read contract

```bash
NO_COLOR=1 python \
  scripts/coordination/resolve_next_prompt.py \
  --module forprint_library \
  --read
```

Expected:

```text
boxed metadata;
80-character separator;
unchanged prompt body.
```

## Focused tests

```bash
python -m pytest -q \
  tests/coordination/test_prompt_queue_navigation.py \
  tests/reporting/test_coordination_result_tables.py \
  tests/reporting/test_resolve_next_prompt_result_table.py \
  tests/reporting/test_reporting_consolidation_audit.py
```

## Ruff

```bash
python -m ruff check \
  scripts/coordination/resolve_next_prompt.py \
  scripts/reporting/coordination_result_tables.py \
  scripts/reporting/audit_consolidation.py \
  tests/reporting/test_resolve_next_prompt_result_table.py \
  tests/reporting/test_reporting_consolidation_audit.py
```

## Full verification

```bash
make reporting-consolidation-audit
python -m pytest -q
make check-report
git diff --check
```
