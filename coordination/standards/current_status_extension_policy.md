# Current Status Extension Policy

## Status

Active standard

## Purpose

This document defines how ForPrint modules may extend:


```text
coordination/status/current_status.yaml
```

without breaking the central Blueprint coordination metadata contract.

The goal is to prevent accidental loss of module-specific validation and safety fields when central fixer/normalizer tools update standard metadata.

## Core rule

Central Blueprint tools may add or update required standard keys.

Central Blueprint tools must not delete unknown or module-specific keys.

In particular, tools must preserve blocks such as:

```text
validation
boundaries
storage
client_account
module_specific
runtime
local_checks
```

unless a future explicit migration says otherwise.

## Standard Blueprint boundary block

The canonical Blueprint coordination contract uses:

```yaml
boundary:
  no_foreign_ownership: true
  no_production_api: true
  no_live_write: true
  no_real_integrations: true
```

Meaning:

```text
boundary = general Blueprint coordination contract.
```

This block is used by Blueprint-level validators and coordination snapshots.

It describes high-level ownership and safety boundaries.

## Module-specific boundaries block

A module may also define local safety assertions:

```yaml
boundaries:
  production_api_added: false
  real_integrations_added: false
  production_db_migrations_added: false
  real_1c_sync_added: false
  crm_dashboard_added: false
  telegram_runtime_ui_added: false
  calculator_integration_added: false
  library_integration_added: false
  warehouse_stock_truth_added: false
```

Meaning:

```text
boundaries = module-specific safety assertions.
```

These fields may be used by module-local tests.

They should not be treated as duplicates of the Blueprint `boundary` block.

They answer a different question:

```text
Did this module accidentally add forbidden implementation scope?
```

## Module-specific validation block

A module may define a local validation/status block:

```yaml
validation:
  make_check: ok
  make_check_report: ok
  client_card_preview: ok
  coordination_metadata: ok
```

Meaning:

```text
validation = module-local validation/status evidence.
```

This block may contain module-specific commands and outputs.

Examples:

```text
client_card_preview
data_foundation_preview
library_catalog_seed_check
calculator_contract_check
gateway_smoke_check
```

Blueprint tools must preserve this block.

## Difference between boundary / boundaries / validation

```text
boundary
  General Blueprint coordination contract.
  Required by central coordination metadata validation.

boundaries
  Local module-specific safety assertions.
  Usually checked by module-local tests.

validation
  Local module-specific validation/status evidence.
  Usually checked by module-local tests and status reports.
```

## Safe fixer / normalizer behavior

Central fixer or normalizer tools must follow this rule:

```text
Do not rewrite current_status.yaml from scratch.
Only add or update required standard keys.
Preserve all module-specific blocks and unknown keys.
```

Allowed:

```text
add missing module_name;
add missing module_status;
normalize priority high -> p0;
update last_commit;
update pushed/commit metadata;
add missing boundary block if absent.
```

Not allowed:

```text
delete validation;
delete boundaries;
delete storage;
delete module_specific;
delete local module check outputs;
replace the entire YAML with only central standard fields.
```

## Merge strategy

Recommended strategy for tools:

```text
1. Load existing current_status.yaml as mapping.
2. Validate it is a mapping.
3. Update only known central keys.
4. Preserve every unknown key.
5. Write the merged mapping back.
```

## Required central keys

Blueprint coordination metadata expects these keys:

```text
module_name
module_status
priority
last_commit
checks
boundary
recommended_next_step
updated_at
```

Other keys are allowed.

## Module-local extension examples

Operational Registry may use:

```yaml
validation:
  make_check: ok
  make_check_report: ok
  client_card_preview: ok
  coordination_metadata: ok

boundaries:
  production_api_added: false
  real_integrations_added: false
  production_db_migrations_added: false
  real_1c_sync_added: false
  crm_dashboard_added: false
  telegram_runtime_ui_added: false
  calculator_integration_added: false
  library_integration_added: false
  warehouse_stock_truth_added: false
```

Calculator Engine may use:

```yaml
validation:
  make_check: ok
  blueprint_pull: ok
  blueprint_check: ok
  blueprint_sync_directives: ok

boundaries:
  production_write_added: false
  live_accounting_sync_added: false
  warehouse_stock_truth_added: false
```

Library may use:

```yaml
validation:
  make_check: ok
  catalog_seed_check: ok
  alias_policy_check: ok
  coordination_metadata: ok

boundaries:
  operational_orders_added: false
  client_registry_added: false
  payment_registry_added: false
```

## Test expectation

Module-local tests may require module-specific keys.

Blueprint central tests should not forbid them.

Blueprint fixer tests should verify that module-specific keys survive metadata normalization.

## Operational rule

If a module-local test requires a block such as `validation` or `boundaries`, do not remove that block to satisfy Blueprint.

Instead:

```text
keep module-local block;
add Blueprint-required standard block;
make both pass.
```
