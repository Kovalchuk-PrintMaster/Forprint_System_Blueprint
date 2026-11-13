# Blueprint OC-01 — MINI/FULL Operator Console implementation prompt v0.1

Prompt ID: `blueprint_oc01_mini_full_operator_console_implementation_v0_1`
Target module: `forprint_system_blueprint`
Roadmap step: `OC-01`
Status: DRAFT_NOT_ACTIVATED
Dispatch ready: false
Created: 2026-10-01

## Mission

Implement OC-01 through two progressive contours:

1. `OC-01-MINI` — a genuinely useful minimum vertical slice.
2. `OC-01-FULL` — the complete approved OC-01 target built on the proven MINI.

Do not invent a parallel control plane. Before creating anything new classify every required
capability using:

`REUSE → EXTEND → ADAPT → REPLACE → NEW`

Existing CF10 / Execution Control Plane runtime, lease, sandbox, checkpoint, provenance,
recovery and operator workflow capability must be inspected first.

## Non-negotiable product outcome

Both contours preserve two core operator modes.

### Protected Terminal

A default-off governed terminal gateway with:
- read-only capability profile;
- bounded capability-shaped safe-write profile;
- exact repository/workspace scope;
- policy/capability gate before command execution;
- stdout/stderr/exit-code evidence;
- actor/session provenance;
- timeout/cancel;
- explicit denial outside granted capability;
- no unrestricted shell authority merely because the UI exposes a terminal.

### Assistant Dev Sandbox

A bounded isolated writable environment created from exact `BASE_HEAD`, where the authorized
assistant may:
- edit;
- run tests/checks;
- use broad local dev tooling;
- make local sandbox commits where useful;
- create Environment Delta evidence;
- checkpoint;
- pause/resume;
- seal a deterministic result package.

Sandbox freedom does not silently grant production secrets, host-root mutation, canonical
remote push, merge, production mutation or external mutable-system writes.

## Global invariants

1. ONE MODULE REPOSITORY = ONE ACTIVE WRITABLE ACTOR.
2. Console UI is not execution-state authority.
3. Ownership transfer uses checkpoint/seal or suspend → release → acquisition.
4. `internal_worker`, `operator_assistant`, and `human_terminal` converge on the same
   execution/session/lease semantics where existing Control Plane capability provides them.
5. No implicit commit/push/merge/release/production authority.
6. Material gray zones stop implementation until explicitly resolved.
7. Stable operator workflows belong in supported entrypoints/Makefile where appropriate.
8. Preserve unrelated dirty work exactly.

## Stage 0 — current-state inventory and gray-zone closure

Before mutation inspect:
- current OC-01 roadmap semantics;
- CF10 / Execution Control Plane runtime;
- sandbox/workspace primitives;
- execution/session/lease/checkpoint/event/provenance primitives;
- command broker / allowlist / subprocess / policy-gate capability;
- auth/capability/secret boundaries;
- API/web/UI foundations;
- Makefile operator workflows.

Classify every requirement REUSE/EXTEND/ADAPT/REPLACE/NEW.

Explicitly answer:
- execution-state authority;
- module lease owner;
- Protected Terminal actor identity;
- Assistant Sandbox actor identity;
- `human_terminal` reconciliation;
- read-only vs safe-write command classes;
- command policy evaluation point;
- sandbox isolation mechanism;
- secret exclusion/injection;
- promotion transaction owner/boundary;
- local commit authority;
- remote push authority;
- canonical HEAD drift behavior;
- restart persistence;
- safe mobile-visible controls.

Output: MINI design-freeze / activation packet. No implementation before material gray zones
are closed.

# OC-01-MINI

## MINI-1 — execution/session vertical foundation
Reuse/implement minimal session identity, repository/module, actor, task, lifecycle, lease,
BASE_HEAD, workspace, checkpoint, heartbeat and result/artifact references. Prove lease
collision rejection.

## MINI-2 — Protected Terminal Gateway MVP
Path:
`Console/API → capability/policy check → scoped command → evidence → state/event update`

Prove:
- allowed read-only command;
- denied command before side effect;
- exact bounded safe-write grant;
- timeout/cancel;
- output/exit code retention;
- actor/session attribution;
- writable-lease enforcement.

Initial read-only families may include supported `git status/diff/show/log`, non-mutating
Make checks, approved validators and bounded file inspection/search. Prefer capability/tool
registry semantics over a giant raw-shell allowlist.

## MINI-3 — Assistant Dev Sandbox MVP
Path:
`authorize task → session → exact BASE_HEAD → isolated writable sandbox → work/test/checkpoint`

Require isolation, task scope, edits/tests, Environment Delta, health/status, minimum
pause/resume or restart recovery and seal.

## MINI-4 — sealed result package
Include module/repository, task id, BASE_HEAD, final sandbox HEAD if applicable, changed paths,
deterministic diff/patch, local commits, tests/checks, artifacts, Environment Delta, open issues,
recommended canonical write-set and promotion preconditions.

## MINI-5 — Sandbox → Canonical Promotion MVP
Preview before apply:
1. repository identity;
2. canonical HEAD vs BASE_HEAD;
3. writable lease;
4. exact write-set;
5. conflict/drift detection;
6. promotion preview;
7. explicit authorization;
8. bounded apply;
9. focused validation;
10. retained success/failure/rollback evidence.

No automatic remote push. Canonical HEAD drift must never silently overwrite work.

## MINI-6 — minimum phone/laptop Console UI
Show module, actor, lease, task, lifecycle, heartbeat, checkpoint, terminal state/profile,
sandbox state, bounded start/pause/stop controls, latest evidence, result readiness, promotion
readiness/conflict and artifacts. UI consumes Control Plane truth.

## MINI-7 — real proof A: Protected Terminal
`authorize → acquire → command → evidence → checkpoint/complete → release`

Acceptance: proof path needs no manual SSH command copying.

## MINI-8 — real proof B: Assistant Sandbox
`authorize → sandbox → work → tests → checkpoint → seal → result package → promotion preview
→ explicit promotion → validation → release`

Acceptance: useful engineering progress can continue while Human Owner is away from the local
terminal.

## MINI completion gate
Both proof cycles PASS. Record only PARTIAL_IMPLEMENTED progress for OC-01.

# OC-01-FULL

## FULL-1 — Protected Terminal hardening
Richer capability profiles, tool-registry integration, explainable denial, streaming where
appropriate, history, stronger cancellation and explicit approval for sensitive elevation.

## FULL-2 — Sandbox lifecycle hardening
Durable long-running sessions, deterministic restart/recovery, resource limits, richer health,
multiple checkpoints, retention, environment/dependency capture and reproducibility evidence.

## FULL-3 — Promotion hardening
Robust drift/conflict reconciliation, promotion transaction identity, rollback/recovery
evidence, exact-path apply, staged validation, provenance, local commit handling and a separate
explicit remote-push authority path if policy later permits.

## FULL-4 — three-actor operational convergence
Prove controlled handoff among `internal_worker`, `operator_assistant`, `human_terminal`.
No ownership stealing.

## FULL-5 — mature Console surface
Event timeline, alerts/attention, recovery actions, retained artifacts/checkpoints,
actor/lease history, promotion history, health diagnostics, mobile layout and authority-aware
controls.

## FULL-6 — recovery/fault proofs
Prove process loss, sandbox restart, stale heartbeat, lease contention, canonical HEAD drift,
failed promotion validation and interrupted promotion.

## FULL-7 — operator docs and stable entrypoints
Document modes, authority, recovery, sandbox lifecycle, promotion lifecycle, terminal profiles
and failure handling. Add stable operator workflows to the Makefile functional map.

## FULL completion gate
Protected Terminal, Assistant Sandbox, controlled promotion, three-actor handoff, phone/laptop
UI and fault/recovery proofs are all operational with boundaries intact.

## Explicit non-goals

No MCP implementation, unrestricted shell, autonomous production mutation, broad simultaneous
multi-module writable execution, automatic merge/push without authority, or unrelated module
work.

## Required closeout

Report separately:
- MINI status;
- FULL status;
- reused vs new capabilities;
- gray zones;
- both real proofs;
- tests/checks;
- exact write-set;
- milestone commits;
- Makefile coverage;
- authority verification.

This prompt is detailed implementation planning only. It does not activate itself.


<!-- oc01-8-plus-7-reconciliation-2026-10-04:start -->
## Canonical OC-01 delivery decomposition â€” 8 MINI + 7 FULL

This section reconciles the 2026-10-02/03 Operator Console packages into the existing
OC-01 prompt. It refines the already-approved MINI/FULL contours; it does not create a
parallel control plane or new authority.

### OC-01-MINI
1. `MINI-1` â€” execution/session vertical foundation.
2. `MINI-2` â€” Protected Terminal Gateway MVP.
3. `MINI-3` â€” Assistant Dev Sandbox MVP.
4. `MINI-4` â€” sealed result package.
5. `MINI-5` â€” Sandbox â†’ Canonical Promotion MVP.
6. `MINI-6` â€” minimum phone/laptop Console UI.
7. `MINI-7` â€” real proof A: Protected Terminal.
8. `MINI-8` â€” real proof B: Assistant Sandbox â†’ controlled promotion.

MINI completion requires both real proof cycles to pass. A UI-only implementation is not
sufficient evidence.

### OC-01-FULL
1. `FULL-1` â€” Protected Terminal hardening.
2. `FULL-2` â€” Sandbox lifecycle hardening.
3. `FULL-3` â€” Promotion hardening.
4. `FULL-4` â€” three-actor operational convergence.
5. `FULL-5` â€” mature Console surface.
6. `FULL-6` â€” recovery/fault proofs.
7. `FULL-7` â€” operator docs and stable entrypoints.

FULL extends the proven MINI and preserves the same authority, lease, provenance,
sandbox/canonical and explicit-promotion boundaries.

### Research-package disposition
- MCP external AI adapter: FAR_HORIZON; do not implement as part of OC-01.
- typed evidence: FAR_HORIZON.
- independent oracle architecture: FAR_HORIZON; preserve evaluator seam only.
- architecture reconciliation engine: FAR_HORIZON; preserve declared/discovered separation.
- capability/contract registries: FAR_HORIZON / extension points only.
- multi-anchor approval engine: FAR_HORIZON.
- existing lease/actor invariants, UI non-authority and
  `REUSE â†’ EXTEND â†’ ADAPT â†’ REPLACE â†’ NEW`: reuse existing canonical semantics.

This refinement does not authorize remote push, merge, release, production mutation or
automatic ownership transfer.
<!-- oc01-8-plus-7-reconciliation-2026-10-04:end -->
