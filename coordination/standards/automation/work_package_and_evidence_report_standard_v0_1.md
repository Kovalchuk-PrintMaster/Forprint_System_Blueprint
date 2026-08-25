# Work Package and Evidence Report Standard v0.1

## Work-package purpose

A work package is the unit handed to an executor.

It should be large enough to be meaningful but bounded enough that scope, evidence and rollback remain
understandable.

## Work-package recommended fields

- package_id
- module_id
- roadmap_step_refs
- capability_refs
- goal/outcome
- rationale
- authoritative_context
- preconditions
- in_scope
- out_of_scope
- dependency_assumptions
- acceptance_criteria
- required_checks
- mutation_limits
- budget_ceiling
- retry/rework ceiling
- clarification policy
- stop_conditions
- report_contract

## Evidence report principle

The owner/Blueprint should not have to manually rediscover basic facts with ad-hoc commands after
every package.

The executor should self-run mechanical checks and produce a **compact but highly informative report**
that can be inspected directly or uploaded into a review chat.

## Recommended report fields

- report_id
- package_id
- module_id
- executor/provider/model
- started_at / completed_at / wall_time
- roadmap/capability refs
- repo base/head and commit(s)
- exact changed-file scope
- concise implementation summary
- important design decisions
- acceptance criteria result
- tests/checks and exact results
- evidence artifact paths/hashes
- dependency effects
- unresolved questions
- blockers/escalations
- rework/retry count
- budget/spend/token/cost information if available
- risks
- proposed next package

## Report location

The canonical report should normally remain in or alongside the module's governed work/evidence
records. The module may simply return its stable path and compact summary.

Large evidence may be packaged as an archive if that makes semantic review easier.

## Mechanical versus semantic review

Lint/test/schema/check failures should normally be found and resolved by the executor before the
report is presented, within package limits.

Human/Blueprint review focuses on:

- business meaning;
- architectural correctness;
- scope fidelity;
- dependency correctness;
- risk;
- evidence credibility;
- whether progression is justified.

## No noisy micro-report loop

The automation design should avoid a cycle where the operator must stop work every five minutes to
read a trivial report and click continue.

Progressive trust determines package size and review frequency.
