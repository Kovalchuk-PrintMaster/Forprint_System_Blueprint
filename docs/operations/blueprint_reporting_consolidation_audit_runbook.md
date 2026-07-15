# Blueprint Reporting Consolidation Audit Runbook

## Compact audit

```bash
make reporting-consolidation-audit
```

## No-color audit

```bash
NO_COLOR=1 make reporting-consolidation-audit
```

## JSON audit

```bash
make reporting-consolidation-audit-json \
  > /tmp/blueprint_reporting_consolidation_audit.json

python -m json.tool \
  /tmp/blueprint_reporting_consolidation_audit.json \
  > /dev/null
```

## Direct invocation

```bash
python scripts/reporting/audit_consolidation.py
python scripts/reporting/audit_consolidation.py --no-color
python scripts/reporting/audit_consolidation.py --json
```

## Expected decision

```text
scripts/coordination/module_roadmap.py
classification: partial_migration
status: ACTION
```

The expected next implementation front is:

```text
blueprint_module_roadmap_renderer_cleanup_v0_1
```

## Verification

```bash
python -m pytest -q \
  tests/reporting/test_reporting_consolidation_audit.py

python -m ruff check \
  scripts/reporting/audit_consolidation.py \
  tests/reporting/test_reporting_consolidation_audit.py

make reporting-consolidation-audit
make check-report
git diff --check
```
