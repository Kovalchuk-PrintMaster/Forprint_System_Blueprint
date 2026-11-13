# ForPrint Execution Control Plane Program v0.1

**Status:** approved planning architecture / phased implementation program
**Owner:** Human Owner + ForPrint System Blueprint planning
**Authority:** planning context, not execution/dispatch/release authority
**Reconciled:** 2026-09-30

## 1. Purpose

ForPrint should not depend on a sequence of assistants reconstructing operational state from
Git history, dirty files, old scripts, terminal fragments or remembered chat context.

The long-term direction is a persistent **Execution Control Plane** that knows declared work,
records meaningful execution transitions, reconciles declared state with observed evidence and
publishes one current projection for humans, Dispatcher, workers and the future Operator Console.

Git is evidence. Tests are evidence. Filesystem activity is evidence. They do not independently
prove semantic state such as “mini-step complete” or “module free”.

## 2. Authority separation

Keep the following concerns distinct:

- **Roadmap:** what capability should eventually exist and desired dependency/sequence.
- **Roadmap detail package:** what the current implementation contour means.
- **Execution Control Plane:** what work is happening now.
- **Execution / step ledger and semantic journal:** where execution is inside that work.
- **Git, tests, files, workflows and artifacts:** technical evidence.
- **Operator Console:** a client/control surface over Control Plane actions and projections.

The Console is not execution-state authority.

## 3. Core invariants

1. `ONE MODULE REPOSITORY = ONE ACTIVE WRITABLE ACTOR`.
2. No ownership stealing. Transfer is interrupt/request → safe boundary → checkpoint →
   seal/suspend → release → new acquire.
3. Apply `REUSE → EXTEND → ADAPT → REPLACE → NEW` before adding permanent infrastructure.
4. A stale heartbeat does not automatically mean a module is free.
5. Never automatically commit unknown dirty state merely to release a module.
6. Observers record evidence; they do not silently invent semantic completion.
7. Stable operator surfaces call one canonical workflow backend.
8. Failure in a recurring workflow should repair the reusable workflow, not only the current session.
9. Planning integration does not authorize dispatch, release, push, merge or production mutation.

## 4. One execution truth for three actor modes

The same execution-state model must support:

- `internal_worker`
- `operator_assistant`
- `human_terminal`

`human_terminal` represents the current bounded workflow in which an assistant prepares a
command/script, the Human Owner runs it, and evidence is returned.

Actor adapters may differ, but durable execution identity, module ownership, lifecycle,
checkpoint, event and status semantics must converge.

## 5. Stable execution boundary

The target is one supported execution-start backend used by future operator surfaces.

Conceptually:

```text
Human / Worker / Console
          |
          v
stable workflow entrypoint
          |
          v
Execution Control Plane / workflow adapter
          |
          +--> resolve source and readiness
          +--> check predecessors / sequence
          +--> resolve module and occupancy
          +--> acquire module lease
          +--> create durable execution identity
          +--> create/load step ledger
          +--> capture base HEAD
          +--> prepare workspace
          +--> activate current mini-step
          +--> establish liveness/heartbeat
          +--> publish state
          +--> start/attach actor
```

Makefile, future CLI and Operator Console must be thin surfaces over the same backend.

## 6. First implementation contour — CF-10

The full architecture is described now, but CF-10 should initially prove only the smallest useful
durable contour:

1. Execution record / durable execution identity.
2. Execution source reference (`roadmap_step` or bounded equivalent).
3. Actor type.
4. Roadmap step/substep reference where applicable.
5. Exclusive module lease.
6. Heartbeat / last-seen and liveness state.
7. Current execution state.
8. Current mini-step state.
9. Minimal semantic event journal.
10. Checkpoint reference.
11. Machine-readable status projection.
12. Suspend / Resume / Complete / Release lifecycle.

The internal Worker is the first operational reference adapter. The architecture must remain
compatible with `operator_assistant` and `human_terminal` without requiring those adapters to be
fully operational in the first contour.

### Current Slice B2 boundary

The already frozen governed-worker Slice B2 remains bounded and is **not expanded** by this
program. B2 proves live-launch orchestration for the current governed Worker corridor. Wider
Control Plane capability is sequenced after that foundation is reviewable.

## 7. Minimum semantic events

The first contour needs only a compact durable vocabulary equivalent to:

- `EXECUTION_CREATED`
- `MODULE_LEASE_ACQUIRED`
- `MINI_STEP_ACTIVATED`
- `CHECKPOINT_CREATED`
- `EXECUTION_SUSPENDED`
- `EXECUTION_RESUMED`
- `EXECUTION_COMPLETED`
- `MODULE_LEASE_RELEASED`
- `EXECUTION_FAILED`

Reuse stronger existing CF-10 schemas when available instead of creating a duplicate vocabulary.

## 8. Minimum reconciliation and status

Initial reconciliation must at least answer:

- Is the execution record internally consistent?
- Does module lease agree with active execution?
- Does an ACTIVE execution have a current mini-step?
- Is its heartbeat recent?
- Does a suspended execution remain resumable?
- Does a completed execution incorrectly retain a lease?

A status projection should expose module occupancy, actor, execution/source, current step/substep,
heartbeat/liveness and latest checkpoint in machine-readable form.

## 9. Workflow registry and workflow health

Recurring supported operations should become discoverable through a machine-readable workflow
registry or a stronger existing equivalent.

A workflow should be able to describe information equivalent to:

- workflow ID / owner / status;
- stable entrypoint;
- inputs and prerequisites;
- authority sources;
- phases and state detection;
- idempotency;
- checkpoint/resume semantics;
- validators;
- result schema;
- failure classes;
- Makefile target and future Console action.

Useful lifecycle states are `DECLARED`, `IMPLEMENTED`, `VERIFIED`, `DEGRADED`, `DEPRECATED`.

A workflow is not VERIFIED merely because a Make target exists.

## 10. Worker self-hardening after first stable attempts

After B2 and the first stable live Worker attempts, use
`cf10_worker_self_hardening_backlog_v0_1.yaml` as the planning source for bounded work.

Progression rule:

```text
observable/read-mostly
→ small reusable workflow repair
→ stateful control-plane hardening
→ recovery / actor-neutral orchestration
```

Each task still requires normal execution-ready reconciliation and explicit activation. The backlog
does not dispatch itself.

## 11. Recovery and power loss

Abrupt server power loss is a real operating condition.

Durable execution state should eventually allow:

```text
ACTIVE
+ heartbeat becomes stale
+ durable execution/workspace/checkpoint exists
→ INTERRUPTED_UNEXPECTEDLY
→ reconcile execution + checkpoint + workspace + Git + tests + artifacts
→ RESUME or ABORT_AND_SEAL
```

A new assistant should not need to reconstruct the execution from chat memory.

## 12. Environment delta and artifact provenance

Isolated development environments may use useful modern tooling when it materially improves
quality, speed, observability or reliability.

Material additions should be captured as Environment Delta evidence and recurring useful additions
should become candidates for canonical developer/module profiles or discoverable capabilities.

Artifact payloads may expire, but durable provenance should preserve enough metadata to identify or
recreate important outputs: producing execution/module/actor, base HEAD, source inputs,
generator/recipe, file identity/hash/size and retention class.

## 13. Operator Console relationship

The future Operator Console consumes Control Plane projections and structured actions such as:

- Start
- Status
- Suspend
- Resume
- Complete
- Release
- Request interrupt
- Approve

The UI must not independently infer module ownership or completion from repository state.

## 14. Explicitly deferred long-horizon capability — CF-12

The following remain part of the approved target architecture but may stay deferred after the first
contour:

- advanced idle supervision;
- unattributed writable-activity handling;
- evidence-driven automatic mini-step completion;
- full `operator_assistant` adapter;
- full `human_terminal` adapter;
- rich Console controls;
- Telegram decisions/approvals;
- automatic commit/push workflows;
- artifact provenance UI;
- Conversation Archive UI and semantic conversation search;
- Inspector integration;
- crash-test/runtime validation integration;
- advanced storage-pressure management;
- secrets broker;
- network policy;
- full automated Integration Gate.

Deferred does not mean forgotten. CF-12 is the holding/review horizon until deliberate promotion.

## 15. Partial implementation accounting

Do not mark the entire capability DONE after the first contour.

Future implementation-state records should distinguish at least:

```yaml
capability: execution_control_plane
status: PARTIALLY_IMPLEMENTED
implemented: []
planned_not_implemented: []
```

The exact lists must come from live evidence, not from this planning document.

## 16. Re-entry rule

Whenever work returns to this capability:

```text
read full target architecture
→ read implemented-state evidence
→ inspect current project reality
→ compare prior assumptions with current capabilities
→ REUSE / EXTEND / ADAPT / REPLACE / NEW
→ define/update next bounded implementation contour
```

Do not mechanically continue an old implementation plan when the project has changed.

## 17. Clarification behavior

If current implementation conflicts with this program, do not silently replace it. Produce a
structured clarification identifying existing implementation, expected direction, conflict,
options, blocked scope and safe work that may continue.

## 18. Source lineage

This durable planning program reconciles:

- `29.09.26_cf10_operator_console_execution_fabric_intake_v0_1.zip`
- `30.09.26_f10_execution_work_flow_reliability_and_console_backend_v0_2`
- `30.09.26_f10_add_control_palne_workwlow.txt`
- live CF-10 / CF-12 Control Foundation planning
- existing Operator Console planning
- existing Human Intent and roadmap-enrichment provenance.

The intake archives are source evidence. This normalized program is planning context, not runtime
authority.

<!-- cf10-oc01-execution-enrichment-2026-10-04:start -->
## Execution enrichment â€” current-state relevance, practical outcomes and parallel contours

The Human Owner clarified that CF10 must keep developing in **logical dependency order** rather
than pulling capabilities forward merely to accelerate Operator Console work.

Before a future architectural Worker task is materialized, inspect the nearest relevant live
contour, confirm that the task still fits current project reality, and apply
`REUSE â†’ EXTEND â†’ ADAPT â†’ REPLACE â†’ NEW` before introducing another mechanism.

Continuous improvement is a persistent execution invariant: efficiency, stability, speed,
rationality, reuse, operator usability and resource/economic efficiency should be strengthened
where the bounded task can safely do so. This does **not** create automatic scope, acceptance,
promotion, publication or cross-module authority.

An execution profile / Work Front may explicitly permit broader **sandbox** experimentation.
If the resulting candidate exceeds the declared promotion scope, the Worker must report the
expanded paths, reason, expected benefit, risks/dependencies and validation evidence. Expanded
scope stops at explicit `ACCEPT / REWORK / REJECT` review and is never promoted implicitly.

For operator-facing functionality, practical completion should expose an obvious supported
surface â€” Makefile, CLI, API, Operator Console or an appropriate human/machine-readable report.
Makefile is the operator functional map; it must not be categorically excluded when the supported
workflow genuinely belongs there. Makefile/Console remain thin surfaces over shared backend logic.

CF10 and OC01 may proceed in parallel for read-only analysis, planning, artifact preparation and
other non-writable work. The canonical invariant `one module repository = one active writable actor`
remains unchanged. Exact-path non-overlap makes the handoff between writable actors cheaper but does
not grant concurrent write authority. After publication/release, a legitimate descendant HEAD with
no exact-path overlap permits continuation after refresh/reconciliation rather than reset/stash/clean.

Source handoff SHA-256:
`fc9052cf2cfc574c124095af6aa8cbe2962d07acc2860c21d4e900790acfed8d`.
<!-- cf10-oc01-execution-enrichment-2026-10-04:end -->
