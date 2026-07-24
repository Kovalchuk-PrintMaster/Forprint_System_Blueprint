# Workflow — <title>

## Identity

```yaml
workflow_id: <id>
module_id: <module_id>
status: draft
```

## Purpose

Describe why this workflow exists.

## Trigger

Describe the Make target, operator action or accepted module event.

## Inputs

List canonical files, external input and required preconditions.

## Ordered execution

1. First step.
2. Second step.
3. Final step.

## Outputs

List terminal result, machine artifact and human report.

## Side effects

List every allowed write.

## External-input handshake

Describe exact filename, schema, waiting state and resume command.

## Failure modes

List blocking conditions and non-blocking unknowns.

## Recovery

Provide exact restoration or rerun steps.

## Verification

List tests, checks and expected terminal result.
