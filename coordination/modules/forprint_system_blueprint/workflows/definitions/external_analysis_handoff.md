# Workflow — External Analysis Handoff

## Purpose

Allow a deterministic workflow to request structured analysis that cannot be
reliably completed from local automation alone.

## Exact input file

```text
operator_input/forprint_system_blueprint/bsa.yaml
```

The filename is short. The schema and request identity are not optional.

## Waiting state

The prepare phase writes:

```yaml
status: awaiting_input
```

and exits successfully with the workflow result:

```text
AWAITING_EXTERNAL_INPUT
```

This means the local preparation phase succeeded. It does not mean the audit
is finalized.

## Required operator action

1. Send the generated `analysis_bundle.tar.gz` for analysis.
2. Receive one YAML response in the generated format.
3. Place the response at the exact path above.
4. Set `status: provided`.
5. Run:

```text
make blueprint-self-audit-resume
```

## Validation

Resume rejects:

- a different schema;
- another module id;
- another workflow id;
- another request id;
- an empty summary;
- an unsupported confidence;
- malformed list fields.

The consumed response is copied into the run workspace with a checksum.
