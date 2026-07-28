# Prompt: Align ForPrint Library with ForPrint System Blueprint

## Target module

`forprint_library`

## Purpose

This prompt aligns ForPrint Library with the current ForPrint System Blueprint.

ForPrint Library is the canonical knowledge, catalog, template, semantic registry, and contract-definition layer. It must not become an operational database for orders, clients, payments, or production runtime.

## Current architectural role

ForPrint Library should own:

- material catalog;
- product catalog;
- machine capabilities;
- print modes;
- templates;
- technical cards;
- semantic registry;
- aliases;
- contract definitions;
- versioning;
- migration graph;
- reusable canonical definitions.

## Library may provide

Library may provide canonical data to:

- Calculator Engine;
- Prepress Hub;
- Warehouse Service;
- CRM;
- Integration Gateway;
- Project Inspector;
- future mobile app / website / bot through approved layers.

## Library must not own

Library must not become canonical owner of:

- client orders;
- customer interaction history;
- payments;
- invoices;
- production queue;
- actual warehouse stock;
- runtime delivery status;
- real client uploaded file lifecycle.

## Key architectural risks

1. Library becomes “storage for everything.”
2. Library starts owning operational data.
3. Library duplicates Operational Registry.
4. Library duplicates Accounting Registry.
5. Library becomes hard to use because it mixes catalogs, files, orders, payments, and logs.
6. Library changes canonical names without impact rules.

## Required alignment actions

Please review the current ForPrint Library direction and answer:

1. Which current parts are true canonical catalogs?
2. Which parts are templates or technical cards?
3. Which parts are contract definitions?
4. Which parts are semantic registry / aliases?
5. Are there any operational entities that should not be in Library?
6. How should Library expose data to Calculator?
7. How should Library expose data to Prepress?
8. Which changes in Library should trigger impact rules for other modules?

## Expected deliverable from module assistant

Return a short alignment report:

```text
1. Current Library scope
2. Correct canonical ownership zones
3. Potential overreach zones
4. Data/objects that should move elsewhere
5. Contracts Library should provide
6. Impact rules needed
7. Open questions for Blueprint
```

Important rule

Library is a source of canonical knowledge, not a warehouse for all runtime business data.

The correct direction is:

catalogs + templates + contracts + semantic registry + versioning

not:

clients + orders + payments + all files + all logs.
