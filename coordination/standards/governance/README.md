# Standards Governance

This directory contains standards about how ForPrint Blueprint standards are organized, indexed, grouped and maintained.

These documents do not define business module behavior directly.

They define how standards themselves should be structured so the project remains readable, navigable and maintainable as the number of standards grows.

## Module prompt execution and reporting

`module_prompt_execution_and_reporting_protocol.md` defines the global end-to-end workflow for module assistants that receive prompts from Blueprint.

It clarifies that modules may read Blueprint prompts and standards, but must write only inside their own repositories.

Blueprint-side incoming reports, review records and prompt queue acceptance metadata are created only from the Blueprint context.

<!-- module-workflow-policy-v0-1:start -->

## Module workflow automation

The governance group includes:

```text
module_workflow_automation_and_external_input_policy.md
```

It defines module-scoped workflow control, reusable Make/script automation,
external-input handshakes and compact/full reporting.

<!-- module-workflow-policy-v0-1:end -->

<!-- mutation-builder-contract-v0-1:start -->

## Mutation builder governance

The governance group includes the normative human-readable standard:

```text
mutation_builder_contract_v0_1.md
```

Its machine-readable validation authority is:

```text
mutation_builder_contract_v0_1.yaml
```

Together they require preflight-before-write, typed exact path sets, no-op
rejection, atomic bounded writes, file-mode preservation, focused tests before
the canonical gate, and verified clean rollback after any failure.

<!-- mutation-builder-contract-v0-1:end -->
