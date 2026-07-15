# Blueprint Reporting Consolidation Audit Recovery Guide

## Source of truth

```text
scripts/reporting/audit_consolidation.py
docs/architecture/blueprint_reporting_consolidation_map.md
coordination/reports/audits/2026-07-15__blueprint__reporting_consolidation_audit_v0_1.md
```

## Restore verification

```bash
python -m pytest -q \
  tests/reporting/test_reporting_consolidation_audit.py

make reporting-consolidation-audit

python scripts/reporting/audit_consolidation.py --json \
  > /tmp/reporting_audit.json

python -m json.tool /tmp/reporting_audit.json > /dev/null
```

## Recovery boundaries

The audit is read-only. It must never:

```text
write coordination state;
update prompt queues;
modify roadmaps;
write generated reports;
change awareness ledgers;
alter module repositories.
```

## Known classification rules

```text
console_summary.py is shared reporting core;
run_blueprint_checks.py is a consolidated consumer;
render_document_awareness_dashboard.py is a consolidated consumer;
render_module_roadmap_dashboard.py is a CLI wrapper;
module_roadmap.py is the verified partial migration.
```

## Backup

Installer backups are created under:

```text
.tmp_blueprint_backups/reporting_consolidation_audit_<timestamp>/
```
