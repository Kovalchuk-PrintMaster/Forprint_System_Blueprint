# Portfolio Roadmap, Dependency and Prioritization Standard v0.1

## Objective

Move the ForPrint ecosystem as a balanced portfolio rather than maximizing isolated module velocity.

## Dependency model

A dependency SHOULD record at least:

- provider module;
- consumer module;
- dependency type;
- capability/contract/data involved;
- earliest stage where it matters;
- latest safe stage for readiness;
- blocking severity;
- fallback if any;
- confidence.

Recommended dependency types:

- `hard_dependency`
- `soft_dependency`
- `data_dependency`
- `contract_dependency`
- `runtime_dependency`
- `ux_dependency`
- `operational_dependency`
- `external_provider_dependency`

## Timing matters

"A depends on B" is insufficient.

A module can depend heavily on another module but only near the final 10% of work. In such a case
the provider need not be accelerated immediately.

Prioritization therefore uses dependency **timing**, not only dependency existence.

## Separate scales

Work complexity and portfolio value MUST NOT be conflated.

Example:

- `work_weight=20`, `portfolio_value=high`
- `work_weight=40`, `portfolio_value=low`

The first can deserve budget sooner even if it is easier.

## Portfolio priority inputs

Priority may consider:

- number/severity of downstream blockers;
- time until dependency is required;
- business value;
- technical uncertainty;
- risk reduction;
- readiness of dependent modules;
- cost/velocity of current executor;
- opportunity cost;
- operational/release gate relevance.

## Blocking classes

Recommended initial classes:

- `BLOCKING_NOW`
- `PHASE_GATE_BLOCKING`
- `DEPENDENCY_CRITICAL_LATER`
- `NON_BLOCKING_SUPPORT`
- `OPTIONAL_DEFERRED`
- `TBD_REVIEW_REQUIRED`

## Activation principle

Not every known module should run continuously.

Budget should be concentrated where it produces the best ecosystem progress while maintaining enough
movement in secondary modules to avoid future dependency cliffs.

## Dynamic reprioritization

Blueprint MUST re-evaluate priorities when:

- a dependency is resolved or newly discovered;
- a module reaches a gate;
- cost/velocity changes;
- an executor underperforms;
- requirements/technology change;
- a new external constraint appears.
