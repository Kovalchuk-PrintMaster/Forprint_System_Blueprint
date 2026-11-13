# High-Risk Legacy Reconciliation — Calculator Engine & Telegram Bot v0.1

## Why these modules are special

Calculator Engine and Telegram Bot predate the mature ForPrint ecosystem architecture.

Their histories include active development, pauses, restarts with different assumptions, autonomous/local-module design and later integration into the wider ecosystem.

These modules must not use a naive "newest file wins" rule.

## Architecture-generation dimension

Important documents and implementations should be assigned one of:

- `GENERATION_1_STANDALONE`
- `GENERATION_2_STANDALONE_WITH_EXTERNAL_INTEGRATIONS`
- `GENERATION_3_EARLY_FORPRINT_ECOSYSTEM`
- `GENERATION_4_BLUEPRINT_ALIGNED`
- `GENERATION_UNKNOWN`

Generation is historical context, not an automatic quality judgment.

## Document analysis

Identify:
- contradictory instructions;
- standalone assumptions;
- local database ownership assumptions;
- duplicated integration responsibilities;
- old direct-client integration assumptions;
- material superseded by Blueprint governance.

Do not physically delete documents during discovery.

## Implementation analysis

Identify:
- duplicate scripts/services/adapters;
- old dictionaries/reference stores;
- competing database layers;
- multiple implementations of equivalent behavior;
- code no longer required by current architecture;
- useful code that should belong to another module.

## Cross-module opportunity

When valuable implementation exists in the wrong repository, record:
- `REUSE_CANDIDATE`;
- `ADAPT_CANDIDATE`;
- `MIGRATION_CANDIDATE`;
- `SHARED_SERVICE_CANDIDATE`.

Do not discard useful code merely because its current owner is wrong.

## Acceptance criterion

Before either module is knowledge-stabilized, a new assistant must be protected from accidentally selecting an old standalone architecture document as current execution authority.
