# ForPrint — Autonomous Multi-Module Coordination Program v0.1

Status: PLANNED / DEFERRED STRATEGIC INITIATIVE
Stable initiative ID:
`blueprint_autonomous_multi_module_coordination_program_v0_1`

Purpose: preserve the complete long-horizon design so it can be resumed later without
reconstructing decisions from chat history.

Nothing here authorizes automation today.

## Strategic objective

Automate mechanical coordination while preserving human control over project direction,
high-risk work, milestone acceptance, production-impacting changes and architecture decisions.

Target separation:
- Blueprint Git = declarative project truth;
- module repos = module code/adapters/evidence;
- coordination runtime = events/questions/leases/notifications;
- AI workers = on-demand executors behind policy;
- operator = final strategic authority.

## Coordination data architecture

The autonomy program inherits the v0.4.1 B2 source-of-truth boundary.

Use multiple storage classes deliberately:

- Git/YAML/Markdown for declarative, human-reviewable project truth;
- coordination operational DB for high-churn runtime state;
- filesystem/artifact storage for large evidence;
- dedicated secret storage for credentials;
- future ForPrint business DB for business-domain data.

Do not collapse these into one database merely for architectural neatness.

The operational coordination database is not the canonical home for roadmaps,
released prompt bytes, standards or acceptance oracles. It references them by
stable ID/path/commit/SHA.

The future business database is not a prerequisite for development coordination
and must not become coupled to assistant orchestration.

Initial operational implementation should use SQLite WAL behind a migration-ready
`CoordinationStore` boundary with explicit migrations, stable IDs, UTC
timestamps, versioned payloads, idempotency constraints and
database-independent tests.

PostgreSQL or another central store becomes justified by actual concurrency,
multi-host, HA, replication or analytics requirements rather than file count.

## AUT-01 — Initiative/epic layer

Add non-executable:
`initiative -> work package -> substep -> criterion`.

Only work packages dispatch. Initiative keeps one coherent strategic block and milestone gate.

## AUT-02 — Zero-context assistant entry point

Create a short `coordination/bootstrap/START_HERE.md`, linked visibly from root README.

It points to repo identity/path, purpose, current release, operator interaction,
architecture/standards, roadmap/prompts/completions and context-pack command.

## AUT-03 — Machine-readable bootstrap index

Create a topic index for purpose, release, lifecycle, repository structure, coding rules,
Git policy, prompt execution, completion reporting, module map, dependencies,
clarification/escalation and documentation maintenance.

Avoid duplicated policy prose.

## AUT-04 — Deterministic context-pack generator

Concept:
`make assistant-context-pack MODULE=<module> TOPICS=<...>`

Build deterministic archive under `tmp/`, include manifest/hashes/current release,
optional roadmap/prompts/history, exclude secrets, print one upload path.

Goal: zero-context assistant becomes productive in 2–3 short context rounds.

## AUT-05 — Module bootstrap views

Blueprint owns canonical onboarding. Modules keep a visible pointer and optional generated,
non-authoritative snapshots. Do not maintain duplicated manual policy corpora.

## AUT-06 — Operator/assistant interaction protocol

Formalize:
explain intent before commands; short commands inline; large scripts as files;
document sets as archives; expected result marker; operator returns evidence;
no automatic commit/push; normal conversational explanation.

## AUT-07 — Common event envelope

Operationalize v0.4.1 event semantics with stable IDs, correlation, evidence and idempotency.

## AUT-08 — Clarification runtime

Implement OPEN/ROUTED/ANSWERED/CONFIRMED/RESOLVED and escalation states operationally.

## AUT-09 — Direct module-to-module question routing

Let the owner of a fact answer directly through the coordination runtime.
No cross-repo writes; no Git message bus; secrets/access may route to operator.

## AUT-10 — Bounded clarification

Maximum **5 unresolved round-trips per question thread**.
After round five, stop autonomous dialogue and escalate with transcript/evidence.

## AUT-11 — Execution blocker runtime

Operationalize precise blocker and unable-to-execute reason codes without collapsing them into RETURN.

## AUT-12 — Durable coordination runtime

Pilot:
lightweight deterministic daemon + SQLite WAL + optional filesystem projections + systemd.
Idempotent ingestion, worker leases, restart recovery.

The daemon is the normal writer of operational coordination state.
AI assistants do not receive unrestricted direct SQL write access.

The SQLite store follows the v0.4.1 B2 data boundary and includes explicit
schema migrations, foreign keys, idempotency constraints, backup/restore tests
and an append-only event journal.

Runtime rows reference canonical Git artifacts by stable ID/path/commit/SHA
instead of becoming a second mutable copy of governance truth.

Large logs/evidence stay outside the database and are referenced by artifact
metadata and hashes.

`inotify` may reduce latency but is not source of truth.
Do not start with Redis/NATS/PostgreSQL unless real concurrency, multi-host,
availability or analytics requirements justify migration.

Storage sits behind `CoordinationStore` (or equivalent), so later PostgreSQL
migration does not change event, question, execution or attention contracts.

This coordination store remains separate from the future ForPrint business-data
schema even if both later share physical database infrastructure.

## AUT-13 — Generic on-demand AI worker

Do **not** use an AI assistant as the permanent listener.

Create an AgentRunner-style adapter. First backend may be Codex/terminal assistant.
Daemon stays lightweight; AI starts only for policy-authorized work.

## AUT-14 — Execution policy

Independent enum:
- autonomous_allowed;
- supervised;
- operator_only.

`operator_only` emits attention and cannot be auto-started.

## AUT-15 — Acceptance policy

Independent enum:
- operator_required;
- oracle_auto_allowed.

Execution permission and acceptance permission are separate.

## AUT-16 — Bounded automatic ACCEPT

Only if explicitly opted in and all blocking oracle criteria PASS, no manual criterion,
no unresolved clarification, no unsafe boundary, exact hashes/scope match,
tests/evidence pass, and risk policy permits.

No silent acceptance.

## AUT-17 — Human initiative/milestone gates

Significant initiative closure remains operator-reviewed.
This guards against many locally-correct prompts drifting globally.

## AUT-18 — Advance policy

Third independent permission:
- manual;
- auto_if_accepted_and_eligible.

Requires previous ACCEPT, WIP=0, dependency eligibility, green health, no checkpoint/hold,
valid current-release freshness.

**Execution, acceptance and advance are independent permissions.**

## AUT-19 — Operator Attention Gateway semantics

Attention transitions include:
no dispatchable work, clarification escalation, access/credential issue,
external dependency block, unable-to-execute, operator-only execution,
operator-required acceptance, stale freshness, repeated verification failure,
worker retry exhaustion, dependency cycle and degraded health.

Deduplicate and cooldown; never notify every poll.

## AUT-20 — Operator Attention Gateway + policy-dumb transport adapters

This replaces the idea of an intelligent development Telegram bot.

Flow:
`coordination event -> template catalog -> Attention Gateway -> transport adapter`

First transport may be Telegram.

Transport may:
- render predefined templates;
- show allowed predefined buttons/actions;
- carry structured free-text;
- return structured operator decisions;
- preserve event/correlation IDs.

Transport MUST NOT:
- reason about project policy;
- choose strategy;
- decide acceptance;
- decide roadmap order;
- mutate prompts;
- invent action types;
- run semantic AI;
- require vector/semantic DB.

There is **no fixed artificial count** like 50/50 templates.
Use exactly as many real request/action templates as needed.

Buttons produce decision events; they do not mutate project state directly.

Customer-facing ForPrint Telegram Bot is a separate product/runtime and should not be coupled
to this development control-plane transport.

## AUT-21 — Immutable prompt / operator decision runtime

**Released prompts are immutable execution contracts.**

Scope changes, waiver, optional skip, cancellation, clarification resolution,
blocker resolution and superseding/follow-up work are separate correlated evidence.

An unexecuted requirement never disappears. Completion records the exact disposition.

## AUT-22 — Human-controlled Blueprint coordinator

Daemon may run continuously, but Blueprint AI should not autonomously redesign or strategically
advance the project. Operator starts strategic Blueprint AI explicitly.

## AUT-23 — Logistics autonomy pilot

After H9 and v0.4.1 Q-track:
1. questions;
2. module routing;
3. attention delivery;
4. one explicit low-risk autonomous prompt;
5. oracle evaluation;
6. optional one low-risk auto-ACCEPT;
7. one auto-advance;
8. operator-only milestone;
9. restart/recovery;
10. no-work/blocker notification.

No production writes.

## AUT-24 — Pilot metrics

Measure release-to-claim, clarification wait, unresolved rate, autonomous rounds,
time blocked without awareness, manual interventions, auto-accept ratio,
rework after auto-accept, false notifications, idle time, recovery success,
prevented policy violations.

Success = less operator load without more rework or architecture drift.

## AUT-25 — Progressive ecosystem rollout

Enable one module at a time with bootstrap pointer, module adapter, event/question compatibility,
policy classification, deterministic health, attention integration and kill switch.
No bulk autonomy rollout.

## AUT-26 — Risk classes

After pilot evidence classify docs/refactors/contracts/DB/security/external writes/
production mutation/cross-module breaking changes/releases.
High-risk remains human-gated by default.

## AUT-27 — Audit/replay/operator dashboard

Show module state, current prompt, last event, pending questions, blocker, worker state,
execution/acceptance mode, last verification, last notification, initiative progress,
correlation-ID replay.

## AUT-28 — Recovery / kill switch / safe mode

Global autonomy disable, per-module disable, initiative hold, lease expiry,
replay-safe restart, notification-only safe mode, current-work preservation,
no automatic Git rewrite, no unsafe side-effect retry.

## AUT-29 — Documentation consolidation and stale guidance retirement

After adoption update bootstrap docs, deprecate old onboarding, remove duplicated current guidance,
preserve sealed history, archive obsolete compatibility under retirement policy.

## Operator transport model

Development Telegram is intentionally dumb transport.

Example message fields:
module, prompt, step/requirement, requester, target, question/reason,
blocking/importance, round, event_id.

Actions are fixed by template/policy, e.g.:
answer, request details, pause, resume after access, escalate,
skip optional item, request scope adjustment, manual review.

A button never edits the released prompt.

## Bootstrap operating model

New assistant:
1. read START_HERE;
2. choose topics;
3. request context-pack command;
4. operator uploads archive;
5. assistant reads purpose/current release/role;
6. request deeper roadmap/prompts only if needed;
7. begin work.

Goal: context-window replacement causes near-zero project slowdown.

## Core architecture decisions

1. Deterministic daemon, not AI, is permanent listener.
2. AI workers start on demand.
3. Git is declarative truth, not live message bus.
4. Start with SQLite WAL.
5. One Operator Attention Gateway; transports are policy-dumb.
6. Customer Telegram Bot and development transport are separate.
7. Module-to-module questions are allowed through router.
8. Five unresolved round-trips maximum per question thread.
9. Execution, acceptance and advance are independent.
10. Released prompts are immutable.
11. Scope changes/waivers are separate correlated evidence.
12. Human milestone gates remain for significant initiatives.
13. Blueprint strategic AI remains human-started by default.

## Recommended dependency order

AUT-01 -> AUT-02..06 -> AUT-07..11 -> AUT-12..13 ->
AUT-19..22 -> AUT-14..18 -> AUT-23..24 -> AUT-25..29

Numeric IDs are stable references, not mandatory execution order.

## Entry conditions

Do not activate merely because roadmap exists.

Preferred prerequisites:
- v0.4.1 hardening closed;
- Logistics reference stable;
- clarification/question semantics proven;
- event/attention semantics proven;
- no major current-release ambiguity;
- explicit operator decision.

## Success definition

Modules do not sit idle because routine coordination was not manually relayed;
missing information produces visible bounded questions; low-risk intermediate work can progress
under policy; operator is notified when judgment is required; major milestones remain human-reviewed;
new assistants regain context quickly; audit/replay explains history; automation lowers operator load
without increasing rework or architectural drift.

## Cross-cutting portfolio/operator capability mapping

The canonical detailed planning record is:

`coordination/roadmaps/details/forprint_system_blueprint/portfolio_operator_governance_and_project_standardization_program_v0_1.md`

It extends this AUT program without renumbering packages or changing the recommended dependency order.

Mapping:

- portfolio progress/dependency/priority and effective-readiness views -> AUT-01 + AUT-27;
- AI budget/model/resource governance and funding rounds -> AUT-14 + AUT-19/20 + AUT-26 + AUT-27;
- remote/mobile operator control -> AUT-20 + AUT-22;
- outcome-alignment audits and major-milestone closure gate -> AUT-17 + AUT-19 + AUT-27;
- recurring time/event coordination obligations -> deterministic runtime/attention layers, separately
  activated;
- unified project skeleton and same-intent/same-command contract -> ecosystem standardization/H10
  compatibility plus later reusable tooling.

Two additional program invariants:

1. Locally correct agent work is not enough; significant work must also be reviewed for whether it
   advances the whole system toward the agreed successful project outcome.
2. Reusable framework capabilities emerge from repeated proven ForPrint patterns; do not create a
   framework as an independent goal.

This mapping is planning-only and grants no new execution, acceptance, publication or production
authority.

Planning marker: `PORTFOLIO_OPERATOR_GOVERNANCE_PROJECT_STANDARDIZATION_V0_1`.
