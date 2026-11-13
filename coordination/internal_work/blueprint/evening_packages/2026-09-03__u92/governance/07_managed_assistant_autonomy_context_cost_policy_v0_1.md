# Managed Assistant Autonomy, Context & Cost Policy v0.1

Status: PROPOSED

## Goal

Reduce long-term operator micromanagement while preventing uncontrolled module evolution.

## Autonomy is action-specific

Never declare an entire module simply "autonomous".

Suggested levels:
- A0 HUMAN_DRIVEN
- A1 AI_ASSISTED
- A2 SUPERVISED_AUTONOMY
- A3 BOUNDED_AUTONOMY
- A4 AUTONOMOUS_ROUTINE

Each module/action records:
- current level;
- allowed autonomous actions;
- actions requiring review;
- prohibited actions;
- evidence window;
- rollback/downgrade conditions.

Autonomy can decrease when evidence worsens.

## Self-optimization loop

`OBSERVE → PATTERN → AUTOMATION_CANDIDATE → ROI/RISK → IMPLEMENT_IN_DEV → VERIFY → CANARY → ADOPT/ROLLBACK`

A repeated AI pattern should become deterministic when:
- semantics are sufficiently stable;
- deterministic implementation is cheaper/more reliable;
- owner/contract evidence supports the behavior.

AI does not silently convert its own invented assumption into canonical business truth.

## Runtime telemetry

Per capability, collect where feasible:
- request count;
- AI calls;
- repeated AI calls;
- tool calls;
- repeated tool calls;
- input/output tokens;
- model/provider;
- latency;
- retries;
- clarification count;
- failures;
- manual escalations;
- cost;
- context pressure;
- cache hits/misses.

## Context budget

Do not use a single hard cutoff as truth.

Initial operational bands:
- 0–60% NORMAL
- 60–75% CHECKPOINT_RECOMMENDED
- 75–85% DO_NOT_START_LARGE_NEW_SUBTASK
- 85%+ HANDOFF_REQUIRED_AT_SAFE_BOUNDARY

Thresholds are provisional and should be tuned from production evidence.

## Durable checkpoint

Before fresh-context handoff store:
- task/root request ID;
- objective;
- completed work;
- decisions;
- changed assets;
- evidence;
- blockers;
- current validation state;
- open questions;
- next actions.

Do not copy an entire large conversation into the new episode unless necessary.

## Safe handoff boundary

Prefer fresh context when:
- atomic step is finished;
- no active transaction;
- no tool call in flight;
- no partial file mutation;
- no resource lock held;
- checkpoint persisted.

## AI budget/runway

Track provider/account budget where technically available.

Preferred metric:
`runway_days = available_budget / forecast_daily_spend`

Initial bands:
- >45 days HEALTHY
- 30–45 NOTICE
- 14–30 WARNING
- 7–14 CRITICAL
- <7 EMERGENCY

Target minimum reserve: about 30 days unless operator changes policy.

If provider balance API is unavailable, use a clearly labeled estimate based on usage ledger/invoices. Never invent a precise balance.

## Degradation

When cost/provider/context limits threaten service:
- alert early;
- prioritize critical workloads;
- queue noncritical workloads;
- optionally use approved lower-cost models for explicitly permitted low-risk classes;
- never silently replace intended AI work with canned responses while reporting healthy status.

## Human control surface

Operator should eventually receive a small number of decision packages instead of raw module chatter:
- autonomy promotions/downgrades;
- high-value automation candidates;
- abnormal cost/context behavior;
- cross-module conflict;
- high-impact production approval.

Runtime Inspector supplies facts.
Project Inspector supplies architectural/conformance analysis.
Strategic Control Plane supplies business priority.
