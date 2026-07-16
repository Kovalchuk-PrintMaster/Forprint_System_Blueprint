# Blueprint Module Governance Terminal/Artifact Split Recovery

## Backup location

The installer creates:

```text
.tmp_blueprint_backups/module_governance_terminal_artifact_split_<timestamp>/
```

## Automatic rollback triggers

Rollback occurs when any of these contracts changes:

```text
protected audit function source
CLI help output
exit code
stderr output
normalized JSON bytes
normalized Markdown bytes
JSON key order
Markdown heading order
default report state during --no-write
NO_COLOR behavior
```

## Manual recovery

Copy the affected files from the newest backup directory back to their
repository-relative paths.

## Critical files

```text
scripts/audit_module_governance.py
scripts/reporting/coordination_result_tables.py
scripts/reporting/audit_consolidation.py
tests/reporting/test_reporting_consolidation_audit.py
```

## Recovery verification

```bash
python scripts/audit_module_governance.py --no-write
python -m pytest -q tests/test_module_governance_audit_no_write.py
make module-governance-audit-check
make check-report
git diff --check
```

## Excluded unrelated files

Do not restore, stage or delete unrelated Website, risk-register, roadmap or
temporary backup files.
