# Blueprint Internal Workflow Foundation Runbook

## Validate foundation

```bash
make module-workflow-check
make module-workflow-list
```

## Start Blueprint Self Audit

```bash
make blueprint-self-audit
```

The command:

1. scans current repository evidence;
2. writes compact and detailed reports;
3. builds one analysis bundle;
4. creates `operator_input/forprint_system_blueprint/bsa.yaml`;
5. prints a meaningful waiting instruction.

Expected result:

```text
RESULT: AWAITING_EXTERNAL_INPUT
```

This is a successful pause, not final workflow completion.

## Provide external analysis

Use the generated YAML structure.

Required values:

```text
status: provided
analysis.summary: non-empty
analysis.confidence: high | medium | low
structured list fields: YAML lists of strings
```

Do not change request identity or bundle checksum.

## Resume

```bash
make blueprint-self-audit-resume
```

Expected result:

```text
RESULT: COMPLETED
```

## View current status

```bash
make blueprint-self-status
```

## View full report

```bash
make blueprint-self-report-full
```

## Generic module targets

```bash
make module-self-audit MODULE=forprint_system_blueprint
make module-self-audit-resume MODULE=forprint_system_blueprint
make module-self-status MODULE=forprint_system_blueprint
```

Only Blueprint is implemented in v0.1.
