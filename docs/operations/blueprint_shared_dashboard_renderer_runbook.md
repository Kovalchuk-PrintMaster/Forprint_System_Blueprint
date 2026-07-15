# Blueprint Shared Dashboard Renderer Runbook

## Routine commands

```bash
make prompt-dashboard MODULE=logistics_service
make roadmap-dashboard MODULE=logistics_service
make roadmap-summary MODULES="forprint_library logistics_service"
```

## No-color commands

```bash
NO_COLOR=1 make prompt-dashboard MODULE=logistics_service
NO_COLOR=1 make roadmap-dashboard MODULE=logistics_service
```

## Focused tests

```bash
python -m pytest -q \
  tests/reporting/test_shared_dashboard_renderer.py \
  tests/coordination/test_prompt_queue_navigation.py \
  tests/coordination/test_module_roadmap_dashboard.py
```

## Duplication check

```bash
grep -RIn \
  -E '^def _boxed_border|^def _boxed_row|^def _format_visible_cell|^def _strip_ansi' \
  scripts/coordination/render_prompt_dashboard.py \
  scripts/coordination/module_roadmap.py
```

Expected: no matches.

## Full verification

```bash
python -m ruff check scripts tests tools
python -m pytest -q
make check-report
git diff --check
```

Fix generic formatting in the shared renderer. Fix domain-specific behavior in the dashboard adapter. Never restore a copied local renderer.
