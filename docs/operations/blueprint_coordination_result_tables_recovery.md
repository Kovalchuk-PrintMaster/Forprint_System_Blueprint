# Blueprint Coordination Result Tables Recovery Guide

## Establish state

```bash
git status -sb
git log --oneline -6
git branch -vv
```

Expected branch:

```text
feature/blueprint-coordination-result-tables-v01
```

## Source of truth

```text
scripts/coordination/module_completion_intake.py
scripts/coordination/resolve_next_module_work.py
scripts/reporting/coordination_result_tables.py
scripts/reporting/table_renderer.py
docs/architecture/blueprint_coordination_result_tables_architecture.md
```

## Recovery sequence

```bash
python -m pytest -q \
  tests/reporting/test_coordination_result_tables.py \
  tests/coordination/test_module_completion_finalization.py
make next-work-suggestion MODULE=logistics_service
NO_COLOR=1 make next-work-suggestion MODULE=logistics_service
python -m pytest -q
make check-report
git diff --check
```

## Boundary rule

Do not move validation, roadmap selection, queue mutation or atomic write logic
into the reporting package. Do not restore local table-border or ANSI helpers.
