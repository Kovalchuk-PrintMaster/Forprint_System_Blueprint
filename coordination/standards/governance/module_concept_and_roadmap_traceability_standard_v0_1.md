# Module Concept and Roadmap Traceability Standard v0.1

## Normative intent

A roadmap must remain understandable when the original conversation and original assistant no longer
exist.

**A roadmap step without recoverable design intent is a governance defect.**

No future Blueprint assistant may rely on "the owner once said this was important" as sufficient
meaning.

## Canonical module knowledge layers

Each module SHOULD have distinct, linkable knowledge layers:

### 1. Module Charter

Defines:

- purpose and business/system value;
- strategic role;
- ownership and must-not-own boundaries;
- users/actors;
- primary inputs and outputs;
- integration/dependency position;
- expected final outcome.

### 2. Capability Catalog

Defines the universe of known capabilities, including:

- currently required;
- planned;
- deferred;
- optional;
- experimental/future.

The capability catalog is intentionally broader than the delivery roadmap so useful future capability
is not forgotten simply because it is not scheduled now.

### 3. Delivery Roadmap

Defines the ordered route from current state to target state.

It is not a list of vague verbs. A step must represent a meaningful outcome.

### 4. Design/Requirement Detail

Explains the intent behind roadmap items that would otherwise become ambiguous over time.

## Minimum roadmap-step schema

Every meaningful roadmap step MUST be recoverable through fields equivalent to:

- `step_id`
- `title`
- `phase`
- `intent`
- `expected_outcome`
- `capability_refs`
- `dependency_refs`
- `work_weight`
- `portfolio_value`
- `blocking_class`
- `acceptance_criteria`
- `design_reference`
- `decision_or_source_refs`
- `open_questions`
- `status`
- `confidence`

The physical schema may evolve, but the information must remain available.

## Prohibited orphan intent

The following is insufficient:

`R88 — Administration`

The following is acceptable in principle:

`R88 — Operations Assistant: Knowledge & Guided Forms`

with linked intent describing:

- why employees need a universal information entry point;
- guided corporate forms with field-level explanation;
- text/video procedural knowledge;
- export to approved corporate document format;
- role-specific discovery;
- dependencies and open UX decisions.

## Conversation-to-project rule

Important design information may arrive chaotically in conversation.

Blueprint MUST synthesize it into durable project artifacts containing enough of:

- WHAT;
- WHY;
- HOW THE BEHAVIOUR IS ENVISIONED;
- EXAMPLES;
- BOUNDARIES;
- DEPENDENCIES;
- OPEN QUESTIONS;
- DECISION/SOURCE CONTEXT.

The goal is not verbatim chat archival. The goal is intent recovery with high fidelity.

## Status of uncertainty

Uncertainty is allowed but must be explicit.

Recommended states:

- `DECIDED`
- `PLANNED`
- `DEFERRED`
- `TBD`
- `OPEN_QUESTION`
- `OUT_OF_SCOPE`

An unknown fact must not be silently presented as decided.

## Roadmap versus execution package

A roadmap step and an executor work package are **not required to be 1:1**.

A meaningful roadmap outcome may:

- fit one work package;
- require several bounded work packages;
- later be split or merged without losing the original outcome identity.

Roadmap architecture must not be distorted to match the speed of one specific AI model.

## Continuous maintenance

Until final project delivery, Blueprint MUST continuously:

- reconcile new design knowledge into charter/capabilities/roadmap;
- detect stale steps;
- preserve superseded intent and rationale;
- detect missing links;
- re-check dependency timing;
- update acceptance criteria when the target legitimately changes.

## Handoff requirement

Continuity/START_HERE should point to this standard or its successor.
START_HERE itself should remain a navigation/authority document rather than accumulating the entire
standard inline.
