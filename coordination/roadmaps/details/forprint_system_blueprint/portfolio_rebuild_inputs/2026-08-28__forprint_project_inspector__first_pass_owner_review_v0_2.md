# ForPrint Project Inspector — evening first-pass owner review

Module: `forprint_project_inspector`

Status: `FIRST_PASS_OWNER_DIRECTION_RECORDED / SYNTHETIC_MICROSTEPS_PENDING_SECOND_PASS`

## AGREED_WITH_OWNER

Inspector continuously re-reads current standards/roadmaps/policies and compares them with real module state.
It detects drift, missing evidence, suspicious architecture movement, quality problems and cross-module weaknesses
early, then reports findings for Blueprint/operator action.

A key value is early warning before an implementing assistant wastes many hours in the wrong direction.

## Working boundary

Inspector is an observer/auditor, not semantic owner and not a hidden architecture dictator. External/industry
standards are evidence/risk signals unless explicitly adopted as ForPrint policy.

Any future pause/stop power must be bounded and auditable.

## Synthetic roadmap expansion for pass 2

Everything below is `SYNTHETIC_CANDIDATE` unless explicitly described as owner direction.

### INS-R0 — Inspection input set
- define current docs/standards/roadmaps read repeatedly
- authority/freshness resolution
- module observation inventory
- finding provenance
### INS-R1 — Structural/quality checks
- repo structure
- Makefile/check/lint/test/docs/metadata
- dependency/version drift
- basic quality standards
### INS-R2 — Roadmap/architecture conformity
- current work vs assigned target vector
- unexpected scope growth
- missing dependencies
- architecture analyzability/risk
### INS-R3 — Cross-module inspection
- contract compatibility
- duplicate ownership
- stale Library/Design System/contracts
- orphan dependencies
### INS-R4 — Finding lifecycle
- severity/evidence/confidence
- open/acknowledged/resolved/recheck
- false-positive classification
- repeat/trend analysis
### INS-R5 — Pause/escalation semantics
- OBSERVE -> WARN -> CRITICAL -> REQUEST/ISSUE PAUSE
- automatic pause only for predeclared critical classes
- semantic/strategic ambiguity -> Blueprint/operator
- idempotent pause/resume evidence
### INS-R6 — Inspector self-quality
- false-positive/negative sampling
- coverage/freshness metrics
- check/scanner improvement
- regression corpus

## Dependencies

Blueprint owns governance/roadmap; module repos own implementation; System Administration performs IT repairs;
Strategic Control Plane challenges strategy; Inspector observes/measures/reports.

## Open questions for pass 2

Automatic pause classes; safe deterministic repairs; adopted vs advisory industry standards; cadence by risk;
inspection cost/performance.

## Target milestone

Important drift is detected early enough to prevent large wasted implementation branches, with evidence-rich findings.

## Steady state

Continue measured improvement after the target milestone; the module is not considered permanently finished.
