# Blueprint Implementation Knowledge & Traceability Graph

## Purpose

Replace blind repository-wide `grep` as the primary way to understand how an architectural/process concept is implemented.

Desired query experience:

```text
search concept -> candidate implementation graphs/slices
select graph -> full typed chain
optional bundle -> only relevant code/docs/contracts/tests/policies
```

## Three distinct graph families

Do not collapse all graph semantics into one ambiguous structure:

1. **Portfolio/Planning Graph** — what should exist / be built.
2. **Implementation/Traceability Graph** — how it is actually implemented/governed/tested.
3. **Execution/Runtime Graph** — what actually happened / is running.

They may reference one another but retain distinct authority and semantics.

## Candidate node types

- module;
- capability;
- process;
- policy;
- standard;
- decision;
- contract;
- schema;
- script/file;
- symbol/class/function;
- validator;
- test;
- Make/CLI target;
- generated artifact/projection;
- runtime service;
- external interface;
- work/promotion evidence reference.

## Candidate edge types

- `implements`
- `calls`
- `imports`
- `depends_on`
- `reads`
- `writes`
- `produces`
- `consumes`
- `validates`
- `tested_by`
- `governed_by`
- `constrained_by`
- `generated_by`
- `triggered_by`
- `publishes`
- `subscribes_to`
- `supersedes`
- `derived_from`
- `owned_by`

## Provenance

Each inferred relation should distinguish source/provenance, e.g.:

- static analysis;
- explicit architecture metadata;
- schema/contract linkage;
- generated evidence;
- AI semantic inference.

AI-inferred relationships must not be indistinguishable from deterministic facts.

## Search / concept layer

Support concept identities, aliases, tags, and semantic candidate search so queries can find related implementations even when exact words differ.

## Graph slices

The default user/assistant experience should be a bounded slice, not the entire repository graph. Allow depth/type filters and coherent export bundles.

## Impact analysis

Support questions such as:

- what consumes this contract?
- what tests/validators cover this capability?
- what policies govern it?
- what generated surfaces derive from it?
- what is the direct/transitive blast radius of changing it?

## Semantic consistency audit

Use the graph to build a small coherent document/policy bundle for AI-assisted semantic contradiction review. Findings are candidates requiring authority resolution, not automatic rewrites.

## Coverage audit

For a capability/process, report whether design/policy/code/tests/runtime/docs/evidence surfaces exist and identify traceability gaps.

## Bundle compiler

A future command should be able to export a narrow review package containing:

- graph slice;
- relevant source;
- policies/standards;
- contracts/schemas;
- tests/validators;
- decisions/history;
- generated human-readable views.
