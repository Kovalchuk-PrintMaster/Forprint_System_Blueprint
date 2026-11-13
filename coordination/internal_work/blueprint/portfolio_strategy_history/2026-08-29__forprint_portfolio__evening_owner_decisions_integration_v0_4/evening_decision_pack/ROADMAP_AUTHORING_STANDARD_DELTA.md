# Proposed roadmap / review authoring standard delta

## A. Owner examples are requirements

Every concrete real-world example stated by the owner must be evaluated as a potential roadmap requirement.

If it expresses actual production practice, desired behavior, a known exception or a real business constraint, capture it at the relevant roadmap step.

Example:
> For large sheet quantities, support count estimation from measured stack height using material thickness/reference parameters, in addition to direct quantity entry.

## B. Explain internal language

Expanded reviews must not use unexplained internal shorthand as the main presentation.

Every internal ID should have a plain-language explanation nearby.

## C. Every open question gets options

For each important unresolved question include:
1. what is unclear;
2. why it matters;
3. Option A;
4. Option B;
5. Option C if useful;
6. recommended option;
7. owner decision/status.

## D. Roadmap completeness

Every module requires:
- explicit current state;
- explicit finish-state definition;
- a continuous sequence of meaningful lifecycle/business steps;
- no large semantic gaps where an executor would need to invent a major subsystem.

Prefer maturity bands initially:
`FRAGMENTARY / BASIC / CONTINUOUS / DETAILED / EXECUTION_READY`.

## E. Dependency view

Dependencies should be tied to roadmap steps/capabilities, not only module names.

Example:
`Calculator.quote_acceptance -> OperationsControlRegistry.available_to_promise`

Suggested severity:
- RED — blocks the step;
- YELLOW — required soon / materially improves capability;
- GRAY — useful but not blocking.

## F. Unassigned capability queue

Add a permanent final section:
**Unassigned Capability & Decision Queue**
