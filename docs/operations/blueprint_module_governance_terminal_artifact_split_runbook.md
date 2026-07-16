# Blueprint Module Governance Terminal/Artifact Split Runbook

## Compact read-only audit

```bash
NO_COLOR=1 python scripts/audit_module_governance.py --no-write
```

Expected:

```text
boxed governance summary
Report writing: disabled
exit code 0
stderr empty
```

## Generate detailed artifacts

```bash
NO_COLOR=1 python scripts/audit_module_governance.py
```

Expected artifacts:

```text
reports/module_governance_audit.json
reports/module_governance_audit.md
```

## Generate into an isolated directory

```bash
tmp_dir="$(mktemp -d)"

NO_COLOR=1 python scripts/audit_module_governance.py \
  --report-dir "$tmp_dir"

python -m json.tool \
  "$tmp_dir/module_governance_audit.json" \
  >/dev/null

grep '^## ' \
  "$tmp_dir/module_governance_audit.md"

rm -rf "$tmp_dir"
```

## Focused verification

```bash
python -m pytest -q \
  tests/test_module_governance_audit_no_write.py \
  tests/test_module_governance_protocol.py \
  tests/reporting/test_module_governance_terminal_artifact_split.py \
  tests/reporting/test_reporting_consolidation_audit.py
```

## Static checks

```bash
python -m ruff check \
  scripts/audit_module_governance.py \
  scripts/reporting/coordination_result_tables.py \
  scripts/reporting/audit_consolidation.py \
  tests/reporting/test_module_governance_terminal_artifact_split.py \
  tests/reporting/test_reporting_consolidation_audit.py
```

## Full project verification

```bash
make reporting-consolidation-audit
python -m pytest -q
make check-report
git diff --check
```
