# forprint_integration_gateway — Evening Architecture Amendment v0.2

Status: Proposed mature-state expansion grounded in operator direction.

Gateway is the controlled narrow waist for inter-module transport.

Provide canonical message envelope, sender/recipient identity, root/correlation IDs, contract ID/version, schema validation, routing, idempotency, bounded retries, dead-letter/quarantine, TTL/hop metadata, transport/rate controls and administrative failure observability.

A malformed/incompatible payload must not be silently guessed, coerced, reordered or ignored. Return structured evidence of source, destination, schema/contract version, validation failure, correlation and retry/escalation state.

Contract Registry owns contract lifecycle, Gateway owns transport/boundary validation, domain owners own semantics, IAM owns access, Runtime Inspector observes execution and Project Inspector audits design/conformance.
