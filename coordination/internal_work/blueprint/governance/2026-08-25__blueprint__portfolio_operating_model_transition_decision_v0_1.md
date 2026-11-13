# Blueprint decision — transition to portfolio-operated module development

## Decision

ForPrint development is transitioning from a model in which the owner manually carries most module
roadmaps in memory to a **portfolio operating model** in which module intent, capabilities, roadmaps,
dependencies, progress, executor attribution and evidence are durable project artifacts.

This is a governance/operating-model change, not a claim that autonomous development is already safe.

## Stage relationship

The current Q-series remains the present "stage 0" and must be finished under its current authority.
It is not replaced by this package.

After stage 0:

- next program step 1 is intentionally left for the owner to define at the next working session;
- program step 2 is the portfolio execution/dashboard foundation discussed in this decision;
- no broad module automation starts before the portfolio foundation is sufficiently defined.

## Roadmap reset

Except for the Blueprint's own current execution roadmap, existing module roadmaps are not considered
sufficient planning authority for the new operating model.

They remain evidence of previous work and must be consulted during reconstruction, but they must be
rebuilt into a common structure that covers the route from current state to intended finish.

## Required module planning objects

Every module should converge on the following conceptual set:

1. Module Charter — why the module exists, role, ownership and boundaries.
2. Capability Catalog — what the module can or may eventually do, including deferred capability.
3. Target Scope — what is intended for the current product horizon.
4. Delivery Roadmap — ordered meaningful outcomes from current state to target finish.
5. Dependency Placement — what the module needs, provides, and at which stage dependencies matter.
6. Baseline Assessment — current estimated completion against the rebuilt roadmap, with confidence.
7. Portfolio Priority — current importance to system progress, separate from work complexity.
8. Execution Eligibility — whether the module is ready to receive systematic work packages.

## Blocking classes

Module existence does not imply immediate activation.

The portfolio must distinguish:

- currently blocking;
- phase-gate blocking;
- dependency-critical later;
- non-blocking/supporting;
- deferred/optional.

A module can be non-blocking now and become mandatory before a later operational or release gate.

## Continuous roadmap governance

Roadmaps are living control artifacts. Blueprint must continuously review them until final project
delivery because technologies, materials, providers, production processes, costs and project
dependencies change.

Roadmap maintenance must therefore include:

- stale assumption detection;
- dependency re-evaluation;
- new technology/opportunity review;
- scope and capability discovery;
- end-to-end business-chain completeness review;
- priority/budget rebalance;
- explicit supersession when plans change.

## Portfolio optimization objective

Blueprint should optimize the ecosystem, not individual module speed in isolation.

The main balancing dimensions are:

- time;
- budget;
- dependency criticality;
- business/project value;
- technical risk;
- executor quality and efficiency;
- readiness of upstream/downstream modules.

## Executor experimentation

Different AI/code executors or providers may eventually be assigned to different modules.
Executor/provider/model attribution must be recorded so later evidence can compare:

- delivery velocity;
- cost;
- weighted work delivered;
- acceptance quality;
- rework;
- report quality;
- stability by module type.

No provider/model should be assumed globally best without evidence.

## Explicit non-goals

This decision does not authorize:

- background autonomous commits/pushes;
- automatic business/module ACCEPT decisions;
- destructive/production actions;
- credentials changes;
- cross-repository writes without explicit scope;
- immediate full automation of all modules.
