# ForPrint Module Governance Audit

Generated at: `2026-06-10T10:58:41.828939+00:00`

## Summary

- `OK`: 5
- `NEEDS_ALIGNMENT`: 6
- `WARN`: 2
- `DEFERRED`: 0

## Required files

- `Makefile`
- `forprint_module_manifest.yaml`
- `coordination/status/current_status.yaml`
- `coordination/prompts/index.yaml`
- `coordination/reports/index.yaml`
- `coordination/status/next_questions_for_blueprint.md`

## Required Makefile targets

- `make check`
- `make check-report`
- `make status-report`
- `make blueprint-pull`
- `make blueprint-check`
- `make blueprint-sync-directives`
- `make coordination-check`
- `make coordination-fix`
- `make module-policy-check`
- `make governance-check`

## Module results

| Module | Status | Missing files | Missing targets | Notes |
|---|---:|---:|---:|---|
| `calculator_engine` | `OK` | - | - | - |
| `cloud_backup_manager` | `NEEDS_ALIGNMENT` | `Makefile`<br>`forprint_module_manifest.yaml`<br>`coordination/status/current_status.yaml`<br>`coordination/prompts/index.yaml`<br>`coordination/reports/index.yaml`<br>`coordination/status/next_questions_for_blueprint.md` | `check`<br>`check-report`<br>`status-report`<br>`blueprint-pull`<br>`blueprint-check`<br>`blueprint-sync-directives`<br>`coordination-check`<br>`coordination-fix`<br>`module-policy-check`<br>`governance-check` | - |
| `forprint_accounting_registry_service` | `OK` | - | - | - |
| `forprint_crm` | `NEEDS_ALIGNMENT` | `Makefile`<br>`forprint_module_manifest.yaml`<br>`coordination/status/current_status.yaml`<br>`coordination/prompts/index.yaml`<br>`coordination/reports/index.yaml`<br>`coordination/status/next_questions_for_blueprint.md` | `check`<br>`check-report`<br>`status-report`<br>`blueprint-pull`<br>`blueprint-check`<br>`blueprint-sync-directives`<br>`coordination-check`<br>`coordination-fix`<br>`module-policy-check`<br>`governance-check` | - |
| `forprint_integration_gateway` | `OK` | - | - | - |
| `forprint_library` | `OK` | - | - | - |
| `forprint_operational_registry` | `OK` | - | - | - |
| `forprint_prepress_hub` | `NEEDS_ALIGNMENT` | `Makefile`<br>`forprint_module_manifest.yaml`<br>`coordination/status/current_status.yaml`<br>`coordination/prompts/index.yaml`<br>`coordination/reports/index.yaml`<br>`coordination/status/next_questions_for_blueprint.md` | `check`<br>`check-report`<br>`status-report`<br>`blueprint-pull`<br>`blueprint-check`<br>`blueprint-sync-directives`<br>`coordination-check`<br>`coordination-fix`<br>`module-policy-check`<br>`governance-check` | - |
| `forprint_strategic_control_plane` | `NEEDS_ALIGNMENT` | `Makefile`<br>`forprint_module_manifest.yaml`<br>`coordination/status/current_status.yaml`<br>`coordination/prompts/index.yaml`<br>`coordination/reports/index.yaml`<br>`coordination/status/next_questions_for_blueprint.md` | `check`<br>`check-report`<br>`status-report`<br>`blueprint-pull`<br>`blueprint-check`<br>`blueprint-sync-directives`<br>`coordination-check`<br>`coordination-fix`<br>`module-policy-check`<br>`governance-check` | - |
| `forprint_system_blueprint` | `NEEDS_ALIGNMENT` | `forprint_module_manifest.yaml`<br>`coordination/status/current_status.yaml`<br>`coordination/prompts/index.yaml`<br>`coordination/reports/index.yaml`<br>`coordination/status/next_questions_for_blueprint.md` | `status-report`<br>`blueprint-pull`<br>`blueprint-check`<br>`blueprint-sync-directives`<br>`governance-check` | - |
| `mobile_app` | `WARN` | `Makefile`<br>`forprint_module_manifest.yaml`<br>`coordination/status/current_status.yaml`<br>`coordination/prompts/index.yaml`<br>`coordination/reports/index.yaml`<br>`coordination/status/next_questions_for_blueprint.md` | `check`<br>`check-report`<br>`status-report`<br>`blueprint-pull`<br>`blueprint-check`<br>`blueprint-sync-directives`<br>`coordination-check`<br>`coordination-fix`<br>`module-policy-check`<br>`governance-check` | No local_path declared in module sources registry. |
| `telegram_bot` | `NEEDS_ALIGNMENT` | `forprint_module_manifest.yaml`<br>`coordination/status/current_status.yaml`<br>`coordination/prompts/index.yaml`<br>`coordination/reports/index.yaml`<br>`coordination/status/next_questions_for_blueprint.md` | `check`<br>`check-report`<br>`status-report`<br>`blueprint-pull`<br>`blueprint-check`<br>`blueprint-sync-directives`<br>`coordination-check`<br>`coordination-fix`<br>`module-policy-check`<br>`governance-check` | - |
| `website` | `WARN` | `Makefile`<br>`forprint_module_manifest.yaml`<br>`coordination/status/current_status.yaml`<br>`coordination/prompts/index.yaml`<br>`coordination/reports/index.yaml`<br>`coordination/status/next_questions_for_blueprint.md` | `check`<br>`check-report`<br>`status-report`<br>`blueprint-pull`<br>`blueprint-check`<br>`blueprint-sync-directives`<br>`coordination-check`<br>`coordination-fix`<br>`module-policy-check`<br>`governance-check` | No local_path declared in module sources registry. |
