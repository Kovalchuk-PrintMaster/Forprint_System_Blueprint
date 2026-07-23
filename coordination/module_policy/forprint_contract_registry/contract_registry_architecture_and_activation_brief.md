# ForPrint Contract Registry — Architecture and Activation Brief

> **Document role:** hand-authored architecture, boundaries and activation rationale.
>
> Canonical generated module-policy summary:
> `coordination/module_policy/forprint_contract_registry/module_policy.md`
>
> Machine-readable source of truth:
> `coordination/module_policy/module_policy_index.yaml`


## Module ID

```text
forprint_contract_registry
```

## Module name

```text
ForPrint Contract Registry
```

## Priority

```text
deferred
```

## Development status

```text
planned_placeholder_contract_foundation_pending
```

## Strategic role

Canonical registry and lifecycle authority for versioned inter-module interface
contracts used across the ForPrint ecosystem.

The module is planned now so that API, command, event and shared-envelope
contracts do not grow independently inside Gateway, Library, Telegram,
Logistics, Calculator or other modules.

Initial implementation is intentionally deferred. The first stage is a
Git-backed contract catalog and validation toolchain, not a network service.

## Why this module exists

Without a dedicated contract registry, different modules may independently
define similar request, response, command or event structures. That creates
risks of:

- incompatible payloads;
- duplicated schemas;
- hidden point-to-point agreements;
- unclear producer and consumer ownership;
- breaking changes without migration;
- Gateway-specific contracts that other transports cannot reuse;
- lost historical rationale;
- difficult compatibility and recovery checks.

The registry provides one place to discover which contracts exist, who owns
them, who consumes them, which version is active and whether a change remains
compatible.

## Core boundary

```text
Blueprint
  approves governance, ownership rules and strategic direction

ForPrint Contract Registry
  stores and validates canonical inter-module interface contract packages

ForPrint Library
  owns product, material, service and operation semantics

ForPrint Integration Gateway
  enforces approved contracts at runtime and routes validated traffic

Producer modules
  implement and publish data according to approved contracts

Consumer modules
  consume only declared compatible contract versions

Project Inspector
  later audits drift, duplication and stale contract references
```

## Main goals

- Maintain a discoverable catalog of inter-module contracts.
- Maintain contract IDs, versions, owners and declared consumers.
- Maintain request, response, command, event and common-envelope schemas.
- Record contract lifecycle states: draft, proposed, active, deprecated,
  retired and rejected.
- Validate contract manifests and examples.
- Compare contract revisions against an accepted baseline.
- Detect potentially breaking changes before release.
- Preserve migration, deprecation and recovery metadata.
- Publish read-only artifacts that Gateway and modules can consume.
- Prevent modules from creating incompatible private contracts for shared
  interactions.
- Support future OpenAPI, AsyncAPI, JSON Schema, CloudEvents-compatible and CUE
  validation artifacts without requiring all formats immediately.

## Owns

- `inter_module_contract_registry`
- `contract_manifest_schema`
- `contract_id_namespace`
- `interface_contract_version_history`
- `producer_consumer_registration`
- `contract_lifecycle_metadata`
- `contract_compatibility_baselines`
- `contract_compatibility_results`
- `contract_examples_and_fixtures`
- `contract_release_metadata`
- `contract_deprecation_and_migration_metadata`
- `generated_read_only_contract_catalog`

## Must not own

- `business_workflow_decisions`
- `runtime_request_routing`
- `runtime_transport_execution`
- `runtime_authentication`
- `runtime_authorization_enforcement`
- `customer_or_order_truth`
- `catalog_business_semantics`
- `product_or_material_definitions`
- `pricing_logic`
- `module_internal_data_models`
- `module_implementation_code`
- `production_or_logistics_execution`
- `prompt_governance`
- `project_priority_decisions`
- `deployment_or_kubernetes_packaging`

## Boundary with ForPrint Library

ForPrint Library owns domain and catalog semantics, including canonical product,
material, service, operation and template definitions.

ForPrint Contract Registry owns only the inter-module representation and
lifecycle of interfaces that carry data between modules.

Example:

```text
Library owns:
  what `product.business_card` means

Contract Registry owns:
  the versioned interface contract through which another module receives
  a business-card calculator input envelope
```

The registry must reference Library-owned semantic IDs. It must not redefine
their meaning.

Before active implementation, Blueprint must review the current Library policy
term `contract_definitions` and clarify it as domain-semantic definitions so
that it does not overlap with inter-module interface contracts.

## Boundary with Integration Gateway

Gateway is a deterministic runtime enforcement and transport layer.

Gateway may:

- load approved contract releases;
- validate incoming and outgoing payloads;
- reject unsupported versions;
- attach correlation metadata;
- route valid requests;
- emit technical validation failures and alerts.

Gateway must not:

- invent contracts;
- silently modify contract semantics;
- approve a breaking change;
- become the canonical contract source;
- decide business workflow outcomes.

The Contract Registry is the source of approved interface definitions.
The Gateway is a consumer and runtime enforcer of those definitions.

## Initial lifecycle phases

### Phase 0 — planned placeholder

Current phase.

Allowed:

- module registration;
- placeholder directory;
- module policy;
- architecture discussion;
- interaction inventory;
- contract ownership analysis.

Not allowed:

- runtime service;
- database;
- network API;
- broad schema migration;
- moving existing module contracts;
- changing Gateway runtime behavior.

### Phase 1 — Contract Foundation pilot

Activation requires Blueprint approval.

Expected scope:

- Git-backed contract registry structure;
- contract manifest v0.1;
- ownership and consumer declarations;
- common envelope definition;
- schema examples;
- CUE or equivalent cross-file validation pilot;
- Library-to-Calculator contract pilot;
- compatibility report against the accepted baseline.

No runtime server is required.

### Phase 2 — CI compatibility gate

Expected scope:

- producer example validation;
- consumer fixture validation;
- backward-compatibility checks;
- deprecation and migration checks;
- contract release packet.

### Phase 3 — read-only catalog interface

Only when multiple modules need machine discovery.

Possible scope:

- generated static catalog;
- read-only CLI;
- read-only HTTP catalog;
- signed or checksummed release bundle.

### Phase 4 — optional service capabilities

Consider only if Git-backed artifacts and generated catalogs are insufficient.

A runtime service is not guaranteed and must be justified separately.

## Activation gates

Active development must not begin until Blueprint confirms:

1. The contract-driven communication ADR is accepted.
2. The ownership boundary between Library, Registry, Gateway and modules is
   explicit.
3. At least one real producer-consumer pilot is ready.
4. The first pilot has no live external writes.
5. Contract IDs and version rules are defined.
6. Compatibility policy is selected.
7. Source-of-truth formats are selected.
8. Recovery and deprecation rules are documented.
9. Gateway is not treated as the contract author.
10. The scope can be completed without building a premature platform.

## Planned first pilot

```text
forprint_library
  → versioned Calculator input contract
  → calculator_engine
```

Why:

- the flow is already on the critical path;
- it is read-only;
- it does not require external provider calls;
- Library owns semantics;
- Calculator is a clear consumer;
- compatibility behavior can be tested safely.

## Planned second pilot

```text
order or Gateway boundary
  → shipment preview request
  → logistics_service
```

The pilot must remain preview-only until explicit live-write governance exists.

## Contract package concept

A future contract package may contain:

```text
contract manifest
request schema
response schema
command or event schema
examples
owner and consumers
version and lifecycle
compatibility mode
security classification
side-effect classification
migration notes
recovery notes
generated validation artifacts
```

The exact directory and source formats are deliberately not fixed by this
placeholder policy.

## Safety rules

- No contract may authorize external writes by implication.
- Side effects must be declared explicitly.
- Credentials must never appear in contract examples.
- Personal data classification must be explicit.
- Breaking changes require a new major version or an approved migration.
- Contract IDs must not be reused for different semantics.
- Deprecated contracts must preserve replacement or retirement rationale.
- Generated artifacts must identify their source of truth.
- Registry validation must be deterministic and reproducible.
- Unknown compatibility must block release rather than silently pass.

## Dependencies

Planned dependencies:

- ForPrint System Blueprint for governance and approval.
- ForPrint Library for domain-semantic references.
- Calculator Engine for the first consumer pilot.
- Integration Gateway as a future runtime consumer.
- Project Inspector as a future audit consumer.
- Module test suites for producer and consumer validation.

The module must not depend on Gateway runtime availability during Phase 1.

## Next focus

```text
Keep placeholder only.
Do not begin implementation.
Prepare Contract Foundation ADR and interaction inventory first.
Reassess activation when Library-to-Calculator contract pilot is ready.
```

## Adoption rule

This module policy is strategic guidance. It does not authorize implementation,
repository initialization, dependency installation, contract migration,
Gateway changes or active module prompts.

Any activation requires a separate Blueprint decision and an approved,
bounded prompt.
