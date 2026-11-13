# Deterministic Worker Promotion Policy v0.1

Status: `CANONICAL_PLANNING_POLICY`
Owner: `forprint_system_blueprint`
Execution authority: `false`

## Purpose

ForPrint should use AI workers where they add real capability, while continuously moving stable,
repetitive and economically formalizable work into deterministic business logic, scripts,
contracts, templates or bounded reusable services.

This promotes and extends the earlier Managed Assistant Autonomy self-optimization direction
into a system-wide architecture rule.

## Preferred execution order

1. deterministic business/domain logic;
2. deterministic reusable tool/template/service;
3. AI worker;
4. human escalation where required.

AI remains appropriate for genuinely generative, ambiguous, interpretive or otherwise
uneconomic-to-formalize tasks.

## Permanent loop

`OBSERVE → PATTERN → CANDIDATE → ROI/RISK → OWNER/CONTRACT CHECK → IMPLEMENT IN DEV → VERIFY → ADOPT/ROLLBACK → OBSERVE AGAIN`

There is no terminal DONE state.

## Evidence

Where technically feasible, worker-enabled capabilities should expose enough diagnostic evidence
to distinguish deterministic success, partial deterministic handling followed by worker,
deterministic failure/insufficiency followed by worker, direct worker delegation, final failure
and human escalation.

Useful evidence may include request/capability class, deterministic handler path, worker-escalation
reason, AI/tool calls, retries, latency, cost/resource evidence, result/rework outcome and recurrence.

This evidence is diagnostic and must not become a second business source of truth.

## Promotion rule

A repeated AI pattern becomes a deterministic-promotion candidate when semantics are stable,
owner/contract evidence supports the behavior, deterministic handling is cheaper/safer/faster/more
reliable, module boundaries remain intact and an equivalent reusable capability does not already exist.

Frequency alone never authorizes implementation.

## Responsibility split

- Production Runtime Inspector / canonical runtime telemetry: factual runtime evidence where available.
- Project Inspector: architecture/conformance evidence, duplicate/equivalent capability candidates.
- Verification Lab: adversarial/regression verification.
- Blueprint + human governance: initial promotion decision, owner selection and gates.
- Each module owner: approved domain-local implementation.

Project Inspector does not own runtime truth or canonical business semantics.

## Adoption rule

This policy applies to every capability that invokes or materially depends on an AI/LLM/generative worker.
Module roadmaps should reference this global policy during their next controlled enrichment rather than
creating parallel local policies.

## Source lineage

- `coordination/internal_work/blueprint/evening_packages/2026-09-03__u92/governance/07_managed_assistant_autonomy_context_cost_policy_v0_1.md`
- `coordination/internal_work/blueprint/evening_packages/2026-09-03__u92/governance/09_verification_adversarial_testing_policy_v0_1.md`
- `coordination/internal_work/blueprint/evening_packages/2026-09-25__deterministic_promotion_verification_prepress_v0_1/`
