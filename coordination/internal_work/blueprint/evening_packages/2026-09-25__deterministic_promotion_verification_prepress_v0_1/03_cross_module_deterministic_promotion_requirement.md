# Cross-Module Requirement — Deterministic Promotion Loop

Status: `GLOBAL_ARCHITECTURE_REQUIREMENT_CANDIDATE`

Candidate global requirement for every module using an AI worker.

## Minimum future behavior

Distinguish:
- deterministic success;
- partial deterministic + worker;
- deterministic failure + worker;
- direct worker;
- failure.

Preserve enough structured evidence to detect recurring patterns.

## Review loop

1. gather worker-handoff evidence;
2. group recurring task classes;
3. check whether existing reusable deterministic capability already exists;
4. estimate deterministic feasibility;
5. create architecture/roadmap candidate where justified;
6. implement only after ownership/roadmap approval;
7. add tests;
8. measure whether worker dependence decreased.

## Guardrail

Do not replace genuinely generative AI work with brittle deterministic logic just to reduce AI usage.

## Candidate metrics

- worker handoff rate;
- percentage fully deterministic;
- repeated worker-pattern frequency;
- latency/cost;
- retry/failure rate;
- percentage of recurring worker tasks later promoted into deterministic execution.

Metrics are diagnostic, not business truth.
