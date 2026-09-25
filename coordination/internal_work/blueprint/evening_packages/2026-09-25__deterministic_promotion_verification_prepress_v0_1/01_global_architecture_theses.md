# Global Architecture Theses Pending Roadmap Enrichment

Status: `PENDING_REVIEW`

## A. Deterministic Promotion Loop

Every ForPrint module that can invoke an AI worker should continuously observe which requests reach that worker.

Requests should be distinguishable conceptually as:
- fully deterministic success;
- partial deterministic handling followed by worker;
- deterministic handling failed/insufficient then worker;
- direct worker delegation because the task is inherently generative/ambiguous;
- final failure.

Repeated worker tasks should become candidates for:
- deterministic business logic;
- scripts;
- contracts;
- templates;
- specialized non-AI services;
- improved validation/routing.

Permanent loop:

`real workload -> worker handoffs -> analysis -> deterministic candidate -> implementation/test -> reduced handoff -> observe again`

There is no terminal DONE state.

## B. Worker as Last Capable Layer

Preferred execution order:

1. deterministic business logic;
2. deterministic reusable tool/template;
3. AI worker.

AI should not be used merely because AI can solve the task.

## C. Worker-Handoff Telemetry

Future telemetry should make it possible to understand:
- what reached the worker;
- why deterministic processing did not complete it;
- which module/capability initiated the handoff;
- whether the worker result succeeded;
- latency/cost/resource metadata where appropriate;
- recurrence of similar cases;
- whether an existing deterministic capability could have handled it.

Telemetry is diagnostic evidence, not a second business-truth store.

## D. Improvement Candidate Lifecycle

Recurring worker patterns may become bounded improvement candidates, but never automatic implementation authority.

Initial preferred responsibility split:
- Inspector: factual evidence;
- Blueprint/planning: decide whether to promote a deterministic capability and assign owner;
- target module: implementation;
- Verification Lab: adversarial/regression verification.

This ownership model must be revalidated before implementation.
