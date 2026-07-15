# Blueprint Coordination Result Tables Runbook

## Completion preview

```bash
make completion-intake-preview \
  MODULE=logistics_service \
  MODULE_ROOT=../logistics_service \
  PACKET=<module-relative-packet>
```

No-color:

```bash
NO_COLOR=1 make completion-intake-preview \
  MODULE=logistics_service \
  MODULE_ROOT=../logistics_service \
  PACKET=<module-relative-packet>
```

## Next-work suggestion

```bash
make next-work-suggestion MODULE=logistics_service
NO_COLOR=1 make next-work-suggestion MODULE=logistics_service
```

## JSON contract checks

```bash
python scripts/coordination/resolve_next_module_work.py \
  --root . \
  --module logistics_service \
  --json
```

JSON output must not contain ANSI sequences or presentation-only fields.

## Focused tests

```bash
python -m pytest -q \
  tests/reporting/test_coordination_result_tables.py \
  tests/coordination/test_module_completion_finalization.py
```

## Full verification

```bash
python -m ruff check scripts tests tools
python -m pytest -q
make check-report
git diff --check
```
