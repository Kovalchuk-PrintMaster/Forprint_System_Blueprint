# Operator Workflow, Worker Tool Gateway & Human-Readable Roadmap Amendment v0.1

Status: **ACCEPTED OWNER DIRECTION / PLANNING AMENDMENT / NON-EXECUTABLE**

Date: 2026-10-06

This amendment records three owner-approved infrastructure directions that must survive chat/context
replacement and later be integrated into the existing Control Foundation / portfolio roadmap without
creating parallel authority.

It does not activate work, dispatch a Worker, widen authority, authorize commit/push, mutate
lifecycle/roadmap execution state, or change the current CF-10 Handoff repair corridor.

## 1. Human + Assistant governed change lifecycle automation

Move the recurring engineering closeout mechanics out of chat-generated shell sequences and into
project-native reusable workflow entrypoints.

Target capability family:

- change-status
- change-preflight
- change-validate
- change-stage
- change-commit
- change-publish
- bounded aggregate change-close where safe

Exact command names remain an implementation decision.

Required behavior:

- exact-path write-set and staging only;
- no broad git add . / git add -A;
- HEAD/upstream re-checks at irreversible boundaries;
- preserve unrelated/concurrent dirty paths;
- declared write-set versus observed diff reconciliation;
- change-specific validation before commit;
- diff/cached-diff checks;
- bounded commit-message binding;
- explicit publication approval before push;
- post-push HEAD == upstream verification;
- machine-readable closeout/publication evidence;
- fail closed on source/staging/validation/write-set drift.

First consumer: human + assistant engineering work.
Worker use of stronger mutation/publication capabilities is a later evidence-driven policy decision.

Roadmap placement:
- near-term bounded self-hardening under CF-10;
- later generalized under CF-18 operator/publication controls and Project Tool Gateway.

## 2. Provider-neutral ForPrint Worker Tool Gateway

Do not create independent capability semantics or a separate semantic MCP for Copilot, Codex, Grok,
Gemini or other providers.

Target architecture:

Capability Registry -> Authorization Envelope -> Structured Command Executor -> Worker Tool Gateway

MCP is a transport/interface over the canonical capability layer, not the source of authority.

Provider adapters may own only provider mechanics such as prompt transport, model/runtime selection,
MCP attachment syntax, native-tool restrictions, timeout/heartbeat/cancellation integration,
provider-specific budget/accounting, and process/result transport.

Gateway rules:

- evolve the current validation MCP proof into a provider-neutral Worker Tool Gateway;
- use one shared gateway implementation instantiated per execution attempt;
- bind attempt/task/work-front/decision/workspace/evidence identity at startup;
- expose only capabilities allowed for that exact attempt;
- no Worker may self-request additional authority;
- preserve the structured executor and capability registry as the execution core;
- provider adapters remain thin;
- a second real Worker provider is blocked until this separation is implemented or explicitly reviewed
  as unnecessary.

Initial read/validation capability examples:
- validation suite execution;
- repository status;
- repository HEAD;
- diff check;
- bounded context/work-front inspection.

Roadmap placement:
- CF-13 capability/Gateway/Golden Path semantics;
- CF-18 operator/tool/publication integration;
- CF-10 remains the real reference implementation and evidence source.

## 3. Human-readable roadmap, work and attempt projection

Stable machine identifiers such as u180j, CF-10 and cf10-u180j-a029 remain unchanged, but operator
surfaces must not require humans to memorize those identifiers.

Presentation rule:

<machine identity> — <human-readable title>

Where useful also show:
- short current purpose;
- parent work/task;
- current state;
- why the attempt exists;
- next required action/boundary.

Examples:
- u180j — Validation pipeline profiling and optimization
- cf10-u180j-a029 — Pre-ACK context-delivery diagnostic after blocker repair

Human-readable labels should resolve from canonical roadmap/task/work-front/attempt metadata where
possible. Do not create a second hand-maintained naming authority merely for UI.

Required operator surfaces:
- roadmap/status CLI;
- generated current/next projections;
- reports/review packets;
- Dispatcher/operator status;
- Telegram/operator transports;
- Operator Console/dashboard.

Roadmap rebuild rule:
every operator-visible major step and meaningful executable substep must have stable machine identity,
human-readable title, and concise purpose/expected outcome when the title alone is insufficient.

Roadmap placement:
- CF-18 operator projections;
- portfolio roadmap rebuild methodology;
- later CF-02 projection enrichment without changing lifecycle identity.

## 4. Integration sequence

1. Do not modify or ACK diagnostic attempt cf10-u180j-a029.
2. Complete the frozen Handoff v2 internal resume-binding repair.
3. Retry Task70 with new attempt cf10-u180j-a030 after repair closeout/publication.
4. Promote these directions into exact active-roadmap locations in a separate bounded roadmap update
   after the current execution corridor is stable.
5. Exercise human/assistant change-lifecycle automation on routine project work before delegating
   equivalent mechanics to Workers.
6. Resolve provider-neutral Worker Tool Gateway separation before the second real Worker provider.
7. Make human-readable roadmap projection mandatory when roadmap normalization/operator-view work is
   implemented.

## 5. Invariants

- Chat is not durable execution authority.
- Existing canonical IDs remain stable.
- No parallel roadmap authority is created by this amendment.
- No Worker receives new authority merely because a gateway capability exists.
- Capability semantics are provider-neutral.
- Provider adapters are transport/runtime adapters, not policy authorities.
- Human-readable labels improve comprehension but do not replace machine identity.
- Reusable project-native workflows are preferred over repeated chat-generated command sequences.
