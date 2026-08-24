# ForPrint Coordination Data Classification and Persistence Boundary v0.1

## Status

Active v0.4.1 B2 governance standard.

Machine-readable authority:

```text
coordination/standards/governance/coordination_data_classification_and_persistence_boundary_v0_1.yaml
```

## Purpose

B2 prevents coordination state from becoming either an unqueryable file pile or
an accidental second business database.

The rule is semantic, not technology-first:

```text
declarative project truth -> Git/YAML/Markdown
high-churn coordination runtime -> future CoordinationStore
bulky evidence -> filesystem/artifact store
credentials -> dedicated secret storage
business lifecycle -> ForPrint business database
```

File count alone never changes ownership.

## Source-of-truth matrix

| Data class | Canonical owner | Examples | Runtime copy rule |
| --- | --- | --- | --- |
| Declarative governance | Blueprint Git | release authority, standards, roadmaps, released prompts, contracts, acceptance oracles, durable operator decisions, sealed reviews, module registry | A runtime store may index immutable references only; it must not become an independently mutable copy |
| Coordination runtime | Future `CoordinationStore` | event journal, executions, revalidations, questions, attention, notification delivery, worker leases, idempotency, runtime projections | Operational events are runtime truth once that runtime is separately activated |
| Bulky evidence | Filesystem/artifact store | logs, archives, diffs, reports, context packs | Store metadata/reference in runtime state; keep payload out of relational rows by default |
| Secrets | Dedicated secret storage | tokens, passwords, private credentials | Store opaque references only; secret values never belong in Git, prompts or coordination event payloads |
| Business domain | ForPrint business storage | customers, orders, products, pricing, production/logistics business lifecycle | Coordination must reference business identities through contracts, never absorb business truth |
| Generated projections | Rebuildable outputs | dashboards, derived status views, caches | Never authoritative unless explicitly promoted through reviewed governance |

## No dual mutable truth

A Git-governed object must not be copied into a database and then edited there
as a second authority.

Future runtime rows may bind a canonical Git artifact using:

```text
stable_id
git_path
git_commit
sha256
schema_version
```

Generated projections remain rebuildable. Durable project/operator decisions
that change governance are promoted to explicit Git records through reviewed
transactions.

## Migration-ready CoordinationStore boundary

Future runtime code depends on `CoordinationStore` or an equivalent service
interface, never scattered SQLite-specific calls.

The contract requires:

- stable IDs;
- UTC timestamps;
- explicit schema versions and migrations;
- versioned event payloads;
- bounded transactions;
- deterministic uniqueness/idempotency constraints;
- repository/service interfaces;
- one coordination-service write boundary;
- database-independent contract tests.

The initial single-server backend may later be SQLite with WAL, foreign keys and
safe backup primitives. That backend is **not activated by B2**.

PostgreSQL or another central store is reconsidered only when requirements such
as multi-host writes, HA, replication, write contention or richer operational
analytics justify it.

## Conceptual runtime schema families

Future storage may contain families equivalent to:

```text
event_journal
execution_runs
execution_revalidations
question_threads
question_messages
attention_events
operator_decisions
notification_deliveries
worker_leases
prompt_runtime_state
module_runtime_state
artifact_index
idempotency_keys
schema_migrations
```

This list is a semantic contract, not a current SQL schema and not an
authorization to create a database.

## Retention, backup and restore

Retention follows the data class.

- Declarative governance remains in Git history and sealed history is immutable.
- Rebuildable runtime projections may be discarded and rebuilt from durable
  sources.
- Append-only operational audit events require an explicit audit-retention rule;
  projection cleanup must not delete them implicitly.
- Large evidence may be compressed or archived while preserving required
  metadata, hashes and correlations.
- Secret lifecycle is owned by secret storage, including rotation/revocation;
  coordination backups must not become secret-value archives.
- Future SQLite backups must use SQLite-safe backup mechanisms rather than
  naive copies of a live database file.
- Restore procedures must be tested and verify schema migration state,
  idempotency constraints, pending handoffs, artifact references and canonical
  Git bindings.

A backup is recovery evidence, not a new source of truth.

## Separation from business storage

Development coordination must not depend on the future business database.

Customers, orders, pricing, products, production and logistics business truth
have different owners, security and lifecycle requirements. Coordination and
business storage may eventually share physical PostgreSQL infrastructure only
while retaining separate schemas/databases, contracts and ownership.

## B2 acceptance gates

B2 is acceptable only when all of these are true:

1. the source-of-truth matrix is explicit and machine-readable;
2. the migration-ready store contract is explicit and backend-independent;
3. retention, backup and restore rules are explicit and validated;
4. canonical Git references use stable identity/path/commit/hash/schema fields;
5. dual mutable truth is forbidden;
6. coordination storage remains separate from business storage;
7. tests prove the contract and safety boundaries;
8. live SQLite, daemon, systemd, autonomous execution and automatic ACCEPT
   remain disabled.

## Explicit non-goals

B2 does not:

- create a `.sqlite`, `.sqlite3` or `.db` runtime file;
- implement a persistent daemon or systemd service;
- authorize autonomous execution;
- authorize automatic ACCEPT;
- release a business/module prompt;
- mutate an external module repository;
- choose final SQL normalization;
- require PostgreSQL;
- move canonical Blueprint governance out of Git.
