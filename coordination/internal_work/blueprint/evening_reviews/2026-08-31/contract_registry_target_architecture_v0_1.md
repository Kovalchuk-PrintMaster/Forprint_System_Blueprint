# ForPrint Contract Registry Target Architecture v0.1

Status: conceptually agreed; detailed schemas remain future implementation work
Module: forprint_contract_registry
Date: 2026-08-31

## Purpose

ForPrint Contract Registry is the canonical registry of significant inter-module interface
agreements.

It must be able to answer:

- which modules exchange which data;
- under which contract/revision;
- who provides and consumes it;
- what semantic authorities its fields reference;
- whether a revision is compatible;
- which mandatory consumers support it;
- who is affected by a proposed change;
- when an older revision can be deprecated/retired.

## Boundary with Library and Gateway

Library defines reusable domain semantics such as `material_id`, operation IDs and canonical
reference definitions.

Contract Registry formalizes how those concepts appear in an inter-module agreement.

Gateway consumes ACTIVE contracts at runtime for validation/normalization/routing/correlation.
Gateway does not become the canonical home of contract lifecycle.

Contract Registry is not a runtime traffic router and does not own customer/order/material/
payment truth.

## Governance dependencies

Contract Registry depends conceptually on:

- Blueprint lifecycle/activation governance;
- semantic authorities such as Library/CRM/Accounting;
- provider and consumer module requirements;
- Inspector conformance evidence.

Gateway is primarily a runtime consumer of published contracts rather than the semantic owner
of the registry.

## Contract Record target

A contract record should eventually cover at least:

- contract_id / family;
- revision;
- lifecycle status;
- provider;
- consumers;
- purpose;
- request/response/event/artifact schemas as applicable;
- semantic authority references;
- compatibility / supersedes;
- supported legacy revisions;
- validators;
- examples and test vectors;
- mandatory consumer adoption;
- migration notes;
- introduction/deprecation/retirement conditions.

## Contract families

Initial synthetic family set:

- request/response;
- command;
- query;
- domain event;
- coordination event;
- file/artifact descriptor;
- batch import/export;
- webhook/callback.

The exact taxonomy may be refined by real pilots.

## Lifecycle target

Pre-activation:

- DRAFT;
- PROPOSED;
- READY_FOR_ADOPTION.

Operational lifecycle:

- ACTIVE;
- SUPPORTED_LEGACY;
- DEPRECATED;
- BLOCKED;
- REVOKED;
- RETIRED.

A breaking revision must not become ACTIVE before mandatory consumers support it and required
governance/conformance gates pass.

## Compatibility

Registry must distinguish breaking from non-breaking change.

Examples:

- add optional field: potentially non-breaking;
- remove required field, change required type or semantic meaning: breaking.

Compatibility must be explicit rather than assumed from filename/version numbers.

## Adoption matrix

Each revision should expose provider/consumer adoption state and independent conformance
evidence.

Example concept:

- Calculator: READY;
- Operations Control Registry: READY;
- Prepress: READY;
- Assistant: READY;
- Inspector: PASS;
- activation: READY.

## Examples and conformance

Contracts should include representative fixtures and edge-case test vectors, not schema text
alone.

Inspector should be able to independently execute contract conformance and compare a module's
claim of support against actual tests/evidence.

## Impact analysis

A proposed contract revision should identify direct consumers and, where possible, indirect
affected modules. Blueprint uses this to balance cross-module work and avoid one module moving
far ahead of its dependencies.

## Transport-neutral core

Business/interface meaning should remain as transport-neutral as practical. HTTP, message queue,
internal call or future transport adapters should not redefine the same business payload
semantics unless a contract revision explicitly requires it.

## Activation authority

Contract Registry records lifecycle/adoption but does not unilaterally activate breaking
ecosystem semantics.

At the current maturity level:

proposal → semantic authority review → provider/consumer implementation → Inspector evidence →
Blueprint activation decision.

Later, safe/non-breaking changes may become deterministically activatable after the governance
process is proven.

## First real contract pilot

Agreed roadmap direction: use the Calculator → Operations Control Registry Job Specification as
the first full Contract Registry lifecycle pilot.

The whole Calculator target architecture is not yet fully fixed, so the pilot contract details
remain to be refined when that implementation step approaches.

The pilot should prove:

- DRAFT/PROPOSED lifecycle;
- semantic references to Library/CRM/etc.;
- provider/consumer adoption;
- fixtures/conformance;
- compatibility classification;
- Inspector verification;
- activation;
- supported legacy behavior when a subsequent revision appears.

## Negative boundary

Contract Registry does not:

- route runtime traffic;
- invent domain semantics;
- replace Library;
- become business truth;
- modify consumer code;
- silently activate a breaking revision.
