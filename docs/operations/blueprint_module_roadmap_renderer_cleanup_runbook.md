# Blueprint Module Roadmap Renderer Cleanup Runbook

```bash
python -m pytest -q \
  tests/coordination/test_module_roadmap_dashboard.py \
  tests/reporting/test_shared_dashboard_renderer.py \
  tests/reporting/test_reporting_consolidation_audit.py \
  tests/reporting/test_module_roadmap_renderer_cleanup.py

python -m ruff check \
  scripts/coordination/module_roadmap.py \
  scripts/reporting/audit_consolidation.py \
  tests/reporting/test_reporting_consolidation_audit.py \
  tests/reporting/test_module_roadmap_renderer_cleanup.py

make reporting-consolidation-audit
make roadmap-dashboard MODULE=forprint_library NO_COLOR=1
make roadmap-summary ROADMAP_SUMMARY_MODULES=forprint_library NO_COLOR=1
python -m pytest -q
make check-report
git diff --check
```

Expected audit classification:

```text
scripts/coordination/module_roadmap.py
classification: consolidated_consumer
status: OK
```
