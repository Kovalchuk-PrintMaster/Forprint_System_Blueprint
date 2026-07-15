# Blueprint Shared Dashboard Renderer Recovery Guide

## Establish state

```bash
git status -sb
git log --oneline -6
git branch -vv
```

Expected branch:

```text
feature/blueprint-shared-dashboard-renderer-v01
```

## Read

```text
docs/architecture/blueprint_shared_dashboard_renderer_architecture.md
docs/operations/blueprint_shared_dashboard_renderer_runbook.md
coordination/standards/visual_interface/boxed_table_layout_policy.md
coordination/standards/visual_interface/color_tokens_policy.md
```

## Source ownership

```text
shared core: scripts/reporting/table_renderer.py
Prompt adapter: scripts/coordination/render_prompt_dashboard.py
Roadmap adapter: scripts/coordination/module_roadmap.py
```

## Recover

Run focused tests, then color and no-color dashboards, then full `make check-report`.

Do not reintroduce local border, ANSI-width, truncation or row-rendering helpers. Preserve compatibility through narrow adapters.

Completion intake and next-work suggestion remain deferred to a separate checkpoint.
