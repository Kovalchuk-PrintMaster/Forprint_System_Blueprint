# Blueprint Reporting Consolidation Closeout Runbook

## Routine verification

```bash
make reporting-consolidation-audit

python -m pytest -q \
  tests/reporting/test_reporting_consolidation_audit.py \
  tests/reporting/test_reporting_consolidation_closeout.py \
  tests/test_module_makefile_standard_template.py \
  tests/test_make_command_standard.py \
  tests/test_module_governance_protocol.py \
  tests/test_completion_packet_template.py \
  tests/test_module_policy_and_docs_snapshots.py

python -m ruff check \
  scripts/reporting/audit_consolidation.py \
  tests/reporting/test_reporting_consolidation_audit.py \
  tests/reporting/test_reporting_consolidation_closeout.py

make check-report
git diff --check
```

## Expected state

- registry total: 16;
- shared core: 7;
- consumers: 9;
- action: 0;
- review: 0;
- failed: 0;
- decision id: `reporting_consolidation_closed_v0_1`;
- Blueprint checks: all green.

## Module adoption

New or updated module prompts should require:

- `make check-report`;
- `make check-report-full` when extended diagnostics exist;
- `NO_COLOR=1` verification when color exists;
- stable artifact paths when report artifacts exist;
- read-only verification for check/audit commands;
- recovery documentation for substantial changes;
- completion packet reporting evidence.

Do not require nonexistent artifacts or fake completion evidence.

## Adding a reporting consumer

Update the registry, focused tests and source-of-truth documentation in one
change. Do not place a consumer in both `SHARED_CORE` and
`CONSOLIDATED_CONSUMERS`.
