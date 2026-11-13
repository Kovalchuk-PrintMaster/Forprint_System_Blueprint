# Far-Horizon Methods & External Reference Catalog

Status of this entire document: `STRATEGIC_REFERENCE_ONLY`

No item below grants implementation authority. These are mechanisms to revisit after worker/runtime foundations and broader module activation mature.

## A. Portfolio scheduling / uncertainty / forecasting

### CPM — Critical Path Method

Take:

- critical path;
- earliest/latest timing concepts;
- float/slack;
- critical-path recomputation after meaningful graph revisions.

Do not assume the project graph is static.

### CCPM — Critical Chain Project Management

Take:

- resource-constrained critical chain;
- shared-resource contention;
- project/feeding/uncertainty buffers;
- buffer consumption monitoring;
- limits on harmful multitasking / active work where appropriate.

Do not copy CCPM dogma wholesale.

### PERT

Take:

- optimistic / most-likely / pessimistic estimates;
- estimate confidence/provenance;
- use three-point estimates as inputs to probabilistic models.

Do not use classical PERT alone as the final schedule-risk engine for complex multi-path portfolios.

### Monte Carlo

Take:

- probabilistic completion/cost/resource distributions;
- P50/P80/P95-style outputs;
- criticality probability;
- scenario distributions rather than false single-point certainty.

Implement only after historical data and estimate calibration are adequate.

### Sensitivity Analysis / Tornado-style views

Take:

- identify dominant risk/result drivers;
- rank variables by impact;
- support multi-output sensitivity (time, cost, operator load, rework, etc.);
- use as explanatory layer over simulation.

### System Dynamics

Very far horizon.

Take:

- feedback loops;
- stocks/flows;
- delayed effects;
- rework/productivity/quality interaction;
- resource-addition side effects;
- policy what-if simulation;
- historical calibration.

Use only when sufficient event/history data exists.

## B. Performance / baseline / flow management

### EVM — Earned Value Management

Take selectively:

- baseline;
- plan-vs-actual variance;
- resource/time/rework variance;
- forecast-at-completion concepts.

Do not copy full financial EVM bureaucracy or invent false earned-value precision for uncertain architecture work.

### Lean / Last Planner System

Take:

- `SHOULD -> CAN -> WILL -> DID -> LEARN` control loop;
- make-ready/constraint-removal gate;
- pull planning backward from target milestones;
- commitment reliability;
- structured reasons-for-variance;
- continuous learning/recalibration.

This maps naturally to Strategic Horizon / Execution Frontier / Execution Lease / Event Store / feedback.

### BIM principle only

Do not implement BIM. Take only the concept of a shared structured information model with multiple role-specific views.

## C. Project/work management product lessons

### Jira-like lessons

Take:

- typed work items;
- workflow/state transitions;
- multiple views over one canonical work entity;
- blocker/dependency warnings;
- cross-project/portfolio views;
- scenario sandboxing;
- structured query language principle.

Do not recreate Jira wholesale.

### MS Project / Planner lessons

Take:

- typed temporal dependencies;
- critical path;
- shared resource pool;
- capacity/leveling;
- calendars;
- baselines;
- planned-vs-actual variance;
- timeline/Gantt only as projection.

Avoid false precision and static-plan assumptions.

## D. Modeling / notation lessons

### C4

Take small subset only:

- System Landscape;
- System Context;
- selected Container/Dynamic/Deployment views;
- generated human-readable projection from canonical model.

### UML

Take selectively:

- state machines;
- sequence diagrams;
- selected structural/data-contract views.

### BPMN

Take:

- process participants/lanes;
- events/messages;
- gateways/conditions;
- timers/waits/deadlines;
- exceptions/escalations;
- subprocesses;
- process-to-runtime traceability;
- later actual-vs-designed process conformance.

### WBS

Take:

- hierarchical scope decomposition;
- capability -> deliverable -> work package thinking;
- scope-completeness/100%-coverage principle;
- revisioned decomposition;
- roll-up reporting;
- strict separation of scope hierarchy from dependency ordering.

## E. Google engineering/management reference lessons

### Issue Tracker / Buganizer-like lessons

Take:

- canonical work identity;
- component hierarchy;
- parent/child distinct from blocking relations;
- cross-module dependency references;
- structured query/search;
- history/provenance.

### Critique-like lessons

High relevance to Publication Controller:

- small coherent change candidates;
- author self-review before promotion;
- integrated automated analyzers/checks;
- explicit review dimensions;
- review provenance/code archaeology;
- non-regression of canonical codebase health.

### Design Sprint concept

Adapt as bounded architecture discovery for high-uncertainty/high-rework-risk problems:

- understand/define;
- alternatives;
- small prototype/contract model;
- validate scenarios;
- record decision before costly implementation.

Do not require a literal five-day ritual.

### OKR concept

Use only as high-level strategy/outcome traceability:

`Objective -> measurable Key Result -> Capability -> Work`

Avoid turning OKRs into another task tracker.

### Cloud/HPC scaling

Treat only as a future implementation-scaling option for simulations. Do not canonize Google Cloud as an architectural dependency.

### World-model / digital-twin inspiration

Very far horizon: a portfolio digital twin / behavioral model may eventually simulate future trajectories. Prefer explicit graph/state/event/probabilistic/system-dynamics models before considering opaque neural world models.

### Unverified CSSI claim

Do not canonize the `CSSI` name/function from secondary descriptions until primary evidence is found.

## F. Multi-worker parallelism

Very far horizon and deliberately low priority until architecture stabilizes.

Take eventually:

- parallelization assessment;
- semantic mutation scopes;
- capability/contract reservations;
- shared-hotspot detection;
- dynamic concurrency budget;
- parallel-safe execution frontier;
- integration-cost estimation;
- branch divergence monitoring;
- semantic-conflict detection;
- serialized canonical promotion;
- concurrency performance analytics.

Default early pattern:

`1 primary mutation worker + optional read-only/test/review workers`.
