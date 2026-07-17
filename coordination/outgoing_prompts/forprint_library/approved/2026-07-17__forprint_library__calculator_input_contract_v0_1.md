# ForPrint Library Calculator Input Contract v0.1

## Coordination metadata

```yaml
prompt_id: forprint_library_calculator_input_contract_v0_1
module: forprint_library
status: ready
priority: critical
issued_by: forprint_system_blueprint
issued_date: 2026-07-17
previous_front: configurable_product_workbench_business_card_skeleton_v0_1
target_branch: feature/library-calculator-input-contract-v01
scope_class: library_read_contract
pricing_formula_scope_allowed: false
integration_write_scope_allowed: false
```

## 1. Purpose

Create a stable, deterministic, versioned, read-only Library contract that converts a validated configurable product selection into Calculator-ready reference input.

The first covered product is:

```text
product.business_card
```

This front unblocks the Library → Calculator critical path. It does not implement prices, production formulas, order creation, Telegram behavior, Logistics behavior, or external writes.

## 2. Preconditions

Start only after the previous business-card skeleton front is fully accepted and merged, including:

```text
docs/operations/business_card_skeleton_runbook.md
docs/operations/business_card_skeleton_recovery.md
```

Record:

- Library `main` commit;
- Blueprint `main` commit;
- active prompt ID;
- clean working tree;
- previous completion report path;
- previous recovery evidence.

## 3. Ownership boundary

Library owns:

- product identity;
- configurable parameter definitions;
- validation and normalization rules;
- reference identifiers;
- deterministic product-configuration projection;
- schema/version metadata.

Calculator owns:

- price formulas;
- pricing policy;
- numerical calculations;
- costs and margins;
- quote totals.

The Library contract must not contain monetary values, pricing coefficients, hidden formulas, vendor prices, production costs, discounts, taxes, or delivery prices.

## 4. Required public contract

Provide a typed, versioned contract equivalent in meaning to:

```python
CalculatorInputEnvelope(
    schema_version: str,
    product_id: str,
    configuration_id: str,
    normalized_parameters: Mapping[str, object],
    reference_ids: CalculatorReferenceIds,
    validation_snapshot: ValidationSnapshot,
)
```

Exact Python names may follow existing Library conventions, but semantics must remain stable and documented.

Required business-card projection:

```text
product_id
size
sides
material_ref
print_mode_ref
quantity
finishing_refs
artwork_source when supplied
```

Requirements:

- deterministic field ordering in serialized artifacts;
- stable normalization;
- no locale-dependent values;
- no database-object leakage;
- no mutable internal-model leakage;
- no implicit defaults hidden from Calculator;
- explicit schema version;
- explicit validation result;
- explicit error taxonomy.

## 5. Error taxonomy

At minimum distinguish:

```text
unknown_product
invalid_configuration
missing_required_parameter
invalid_reference
unsupported_projection_version
internal_contract_error
```

Errors must be typed or structurally stable and safe for Calculator consumption.

Do not expose stack traces or internal persistence details as public contract data.

## 6. API behavior

Provide a read-only entry point equivalent in meaning to:

```python
build_calculator_input(
    product_id: str,
    configuration: Mapping[str, object],
    *,
    schema_version: str | None = None,
) -> CalculatorInputEnvelope
```

Rules:

- the same valid input produces semantically identical output;
- input mappings are not mutated;
- finishing references are normalized deterministically;
- quantity validation remains owned by Library;
- references remain identifiers, not expanded pricing records;
- unsupported products fail explicitly;
- no network calls;
- no writes;
- no Calculator import dependency inside Library.

## 7. Serialization fixtures

Add canonical fixtures for:

- minimal valid business card;
- business card with finishing;
- business card with artwork source;
- invalid missing material;
- invalid print-mode reference;
- invalid quantity.

Machine-readable fixture output must have a documented stable path.

## 8. Compatibility

Preserve:

- existing `product.business_card` behavior;
- current configurable-product workbench API;
- current validation behavior unless a documented defect is found;
- all existing public imports;
- current tests and fixtures;
- module policy and reporting contracts.

Any unavoidable public change requires:

- compatibility adapter;
- migration note;
- contract test;
- Blueprint review before merge.

## 9. Documentation and recovery gate

Create or update:

```text
docs/architecture/library_calculator_input_contract.md
docs/operations/library_calculator_input_contract_runbook.md
docs/operations/library_calculator_input_contract_recovery.md
coordination/reports/completion/forprint_library_calculator_input_contract_v0_1_completion.md
```

Documentation must explain:

- ownership boundary;
- schema versioning;
- normalization;
- deterministic serialization;
- error taxonomy;
- Calculator consumption example;
- verification commands;
- rollback;
- recovery from incompatible schema or fixture regressions.

## 10. Required tests

Add focused tests for:

1. valid minimal business-card projection;
2. valid full business-card projection;
3. deterministic output for semantically equal input;
4. input mapping is not mutated;
5. finishing references normalize deterministically;
6. optional artwork-source behavior;
7. missing required parameter;
8. invalid material reference;
9. invalid print-mode reference;
10. invalid quantity;
11. unknown product;
12. unsupported schema version;
13. stable serialized fixture;
14. no monetary fields in contract output;
15. no network or write side effects;
16. backward compatibility with existing business-card tests.

Preserve the complete existing Library test suite.

## 11. Forbidden scope

Do not implement:

- price formulas;
- quote totals;
- cost, margin, discount, tax, or currency calculations;
- Calculator internals;
- canonical-order creation;
- Telegram Bot changes;
- Logistics changes;
- CRM, Gateway, 1C, payment, stock, or production writes;
- production deployment.

Do not merge to `main` before Blueprint acceptance.

## 12. Required validation

Run and report exact exit codes and counts:

```bash
make lint
make format-check
make check
make governance-check
make module-validate
make check-report
make check-report-full
git diff --check
git status -sb
```

Also run focused Calculator-input contract tests separately.

Human-facing reports must be colored by default. Use `NO_COLOR=1` only for machine-readable evidence.

## 13. Completion response

Return:

- repository;
- branch;
- base commit;
- final commit;
- Blueprint commit consumed;
- changed files grouped by area;
- public contract summary;
- schema version;
- fixture paths;
- focused test counts;
- full-suite count;
- governance/report results;
- docs/runbook/recovery paths;
- compatibility confirmation;
- forbidden-scope confirmation;
- blockers and deferred work;
- clean `git status -sb`;
- readiness for Blueprint review.

Final line:

```text
RESULT: READY_FOR_BLUEPRINT_REVIEW | BLOCKED | INCOMPLETE
```
