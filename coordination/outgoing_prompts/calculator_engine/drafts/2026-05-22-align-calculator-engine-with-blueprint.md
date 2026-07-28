# Prompt: Align Calculator Engine with ForPrint System Blueprint

## Target module

`calculator_engine`

## Purpose

This prompt aligns the Calculator Engine with the current ForPrint System Blueprint.

The Calculator Engine must remain a calculation-focused service. It should calculate quotes, price breakdowns, product configurations, and material consumption estimates. It must not become CRM, Warehouse, Accounting, or Library.

## Current architectural role

Calculator Engine is responsible for:

- quote drafts;
- price breakdowns;
- product configuration calculations;
- material consumption estimates;
- calculation profiles;
- reusable calculation logic.

## Must own

Calculator Engine may own:

- `quote_draft`
- `price_breakdown`
- `material_consumption_estimate`
- `product_configuration`
- calculation rules specific to price computation

## Must consume

Calculator Engine should consume canonical information from other modules:

- product catalog from `forprint_library`;
- material catalog from `forprint_library`;
- machine capabilities from `forprint_library`;
- print modes from `forprint_library`;
- client/order context from CRM / Operational Registry through approved contracts;
- validated external requests through `forprint_integration_gateway`.

## Must not own

Calculator Engine must not become owner of:

- client registry;
- order registry;
- payment status;
- invoice;
- warehouse stock;
- material catalog as canonical source;
- product catalog as canonical source;
- prepress files;
- logistics status.

If local tables or local data structures for materials/products exist, they must be treated as:

```text
cache / calculation snapshot / imported calculation input
not as canonical truth.
```

Key architectural risks
Calculator starts owning material/product catalogs.
Calculator becomes mini-CRM because it receives customer requests.
Calculator starts reserving stock directly instead of requesting Warehouse.
Calculator starts creating invoices directly instead of requesting Accounting.
Calculator exposes too broad API and becomes general backend.
Required alignment actions

Please review the current Calculator Engine implementation and answer:

Which current entities/tables/configs are canonical and which are only calculation snapshots?
Does the module currently store materials/products as canonical data?
Which outputs are currently produced by the calculator?
Is there a clear quote_draft output structure?
Is there a clear material_consumption_estimate output structure?
Which parts of the module should later be connected to Integration Gateway?
Which parts should later consume catalogs from ForPrint Library?
What should be moved out of Calculator if it already looks like CRM/Warehouse/Accounting?
Expected deliverable from module assistant

Return a short alignment report:

1. Current state
2. Detected architecture drift
3. Data owned by Calculator
4. Data consumed from other modules
5. Data provided to other modules
6. Immediate safe corrections
7. Open questions for ForPrint System Blueprint

Important rule

Do not redesign the whole module now. Do not perform large refactoring without approval.

The immediate goal is:

understand current drift risk and align future development direction.
