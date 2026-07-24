# Workflow — Blueprint Self Audit

## Identity

```yaml
workflow_id: blueprint_self_audit
module_id: forprint_system_blueprint
status: active_v0_1
```

## Purpose

Measure how deeply Blueprint understands its own repository, scripts,
entrypoints, Make targets, workflows, recovery coverage and current metadata.

## Trigger

```text
make blueprint-self-audit
make module-self-audit MODULE=forprint_system_blueprint
```

## Ordered execution

1. Validate module registry, manifest and workflow index.
2. Scan repository files without network access.
3. Parse Python files with `ast`.
4. Inventory functions, classes, CLI entrypoints and Make targets.
5. Read the latest Repository Capability Inventory when available.
6. Calculate compact self-knowledge metrics.
7. Write JSON and Markdown current reports.
8. Build one analysis bundle under `tmp/module_workflows/`.
9. Generate the exact external-input file `bsa.yaml`.
10. Pause with a meaningful terminal instruction.
11. Resume only after the validated file has `status: provided`.
12. Archive the consumed response and update reports.

## Knowledge levels

```text
0 unknown
1 indexed
2 purpose understood
3 dependencies and side effects mapped
4 tests, consumers and recovery verified
5 documented automated workflow
```

The first implementation intentionally reports low coverage honestly.

## Outputs

```text
reports/modules/forprint_system_blueprint/current/self_knowledge_summary.json
reports/modules/forprint_system_blueprint/current/self_knowledge_report.md
tmp/module_workflows/forprint_system_blueprint/<run_id>/analysis_bundle.tar.gz
operator_input/forprint_system_blueprint/bsa.yaml
```

## Side effects

Writes are restricted to:

```text
reports/modules/forprint_system_blueprint/
tmp/module_workflows/forprint_system_blueprint/
operator_input/forprint_system_blueprint/bsa.yaml
```

No Git staging, commit or push occurs.

## Recovery

See:

```text
docs/operations/blueprint_internal_workflow_foundation_recovery.md
```
