# Blueprint Module Roadmap Renderer Cleanup Recovery Guide

Backups are stored under:

```text
.tmp_blueprint_backups/module_roadmap_renderer_cleanup_<timestamp>/
```

Restore the changed files from the newest matching directory, then run:

```bash
make roadmap-dashboard MODULE=forprint_library NO_COLOR=1
make roadmap-summary ROADMAP_SUMMARY_MODULES=forprint_library NO_COLOR=1
python -m pytest -q tests/coordination/test_module_roadmap_dashboard.py
make check-report
```

Do not modify roadmap YAML, prompt queues, awareness ledgers or module
repositories during recovery.
