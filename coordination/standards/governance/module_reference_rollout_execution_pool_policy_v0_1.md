# Module Reference Rollout and Execution Pool Policy v0.1

Status: active Blueprint governance standard
Authority: `forprint_system_blueprint`
Applies to: all canonical ForPrint modules receiving Blueprint-directed AI implementation work
Reference pilot: `logistics_service`
Adopted: `2026-09-05`

## 1. Purpose

This standard defines how the Logistics H10 pilot becomes the reference model for later
module rollout, how prompt work is grouped into execution pools, how human control is
relaxed or tightened between pools, and how fresh AI workers preserve continuity without
depending on conversational memory.

It does not authorize automatic Blueprint ACCEPT, RETURN/HOLD, next-prompt release in the
first pool, commit/push, live-provider writes or cross-repository mutation.

## 2. Logistics is the reference implementation, not a byte-for-byte template

`logistics_service` is the first reference module for the current rollout.

The pilot validates reusable control-plane behavior:

- module-local `AGENTS.md` front door;
- deterministic inventory/index and current-state evidence;
- implementation lineage and documentation authority;
- `module-start` / prompt intake semantics;
- fresh-context startup;
- WIP=1 execution ownership;
- completion reporting and evidence publication;
- conformance review;
- context continuity between fresh workers.

After a Logistics pattern is proven and explicitly approved for portfolio reuse, other
canonical modules SHOULD inherit the behavioral contract and reporting shape.

Domain implementation, internal code and provider-specific architecture need not be copied
byte-for-byte. A justified module deviation must be explicit and reviewable. Silent
per-module protocol forks are forbidden.

## 3. Self-knowledge before business expansion

Before normal capability expansion, a module must be able to explain itself to a zero-context
assistant from repository-owned evidence.

Minimum self-knowledge baseline:

```text
AGENTS.md
current authority pointers
module inventory/index
documentation authority
implementation lineage
roadmap/current task
test, contract and evidence navigation
inventory-build / inventory-check
fresh-context validation
completion/report history pointers
```

The first Logistics H10 prompt is specifically intended to establish this baseline.

## 4. Fresh worker per prompt

The target execution model is one fresh AI worker per released prompt.

Conversation memory is never required for continuity.

A fresh worker receives a bounded generated context snapshot containing, at minimum:

1. module `AGENTS.md`;
2. current Blueprint release/Prompt Queue authority relevant to the task;
3. current prompt + pinned Prompt Contract + Acceptance Oracle;
4. relevant module inventory/index and implementation lineage;
5. current roadmap slice and dependencies;
6. immediately previous completion report/packet evidence;
7. pointers to older prompt/report history;
8. current repository HEAD/status and execution baseline;
9. explicit stop/escalation rules.

The previous worker report is evidence and continuity context, not authority. Current
repository state and pinned governance must be revalidated.

## 5. Execution Pool

An **Execution Pool** is a human-approved bounded parent objective decomposed into a sequence
of substantial child prompts.

Pool identity and child-prompt membership must be explicit.

A pool is larger than one prompt and smaller than an unconstrained project phase.

## 6. First pool control mode — L0 FULL_MANUAL_PROMPT_GATE

The first substantial Logistics execution pool MUST run in:

```text
L0_FULL_MANUAL_PROMPT_GATE
```

Rules:

- every child prompt runs with a fresh worker;
- every child prompt produces the standard completion evidence;
- machine conformance may validate the result;
- the next child prompt is NOT released until the operator personally reviews the previous
  child result and explicitly authorizes continuation;
- automatic Blueprint ACCEPT remains forbidden;
- automatic next-prompt release remains disabled;
- no control level widens merely because tests are green.

The first pool is the reference-quality calibration run for later modules.

## 7. Later pool control levels

After a completed pool, the operator explicitly selects the next pool control level.

### L0 — FULL_MANUAL_PROMPT_GATE

Every prompt boundary requires operator review and authorization.

### L1 — CHECKPOINTED_POOL_AUTOMATION

The operator approves a bounded pool and explicit internal checkpoints. Within an approved
segment deterministic machine conformance may close one child step and activate the next
eligible step. Progress stops at configured checkpoints for operator review.

### L2 — AUTOMATED_CHILD_PROGRESSION_WITH_FINAL_HUMAN_POOL_GATE

Within an explicitly approved pool deterministic machine conformance may progress through
eligible child prompts automatically.

The pool still stops at:

```text
PENDING_HUMAN_POOL_REVIEW
```

before another pool is authorized.

### Downgrade rule

Any material unexplained failure, reporting inconsistency, inventory drift, unexpected
mutation, repeated correction cycle or inability to prove evidence may downgrade the next
pool to L1 or L0.

Automation level never widens itself.

## 8. ACCEPT semantics remain protected

Machine progression inside an approved pool is **not** Blueprint `ACCEPT`.

Use distinct semantics such as:

```text
POOL_STEP_CONFORMANCE_PASS
POOL_STEP_CLOSED
NEXT_CHILD_ELIGIBLE
```

Blueprint `ACCEPT`, `RETURN` and `HOLD` remain explicit operator decisions under the
closed-loop lifecycle standard unless that lifecycle is separately revised by explicit
human decision.

Green tests are evidence, not a business/architectural acceptance decision.

## 9. Mandatory human gate at the end of every pool

Every pool, including L2, ends with operator review.

The operator reviews:

- implemented/live behavior where applicable;
- completion evidence;
- changed-file scope;
- tests and checks;
- unresolved risks;
- architecture/inventory drift;
- quality of fresh-worker continuity;
- resource/AI efficiency where observable.

Allowed pool outcomes include:

```text
ACCEPT_POOL
RETURN_POOL
HOLD_POOL
ACCEPT_POOL_AND_SELECT_NEXT_CONTROL_LEVEL
```

No next pool begins merely because the previous pool is machine-green.

## 10. Independent post-pool inventory/audit

After the first Logistics pool, and whenever requested later, perform an independent
repository inventory/audit that does not merely trust the worker's completion report.

Compare:

```text
claimed work
vs repository reality
vs module inventory/index
vs implementation lineage
vs roadmap obligations
vs tests and evidence
```

The first-pool audit is a mandatory calibration checkpoint before automation widening or
portfolio propagation.

## 11. Resource and AI-budget evaluation

Pool review SHOULD evaluate execution efficiency where trustworthy telemetry exists.

Useful observations:

- input/output token counts;
- model/runtime cost;
- wall-clock execution time;
- worker restarts;
- retries/clarification rounds;
- repeated test/check executions;
- changed-file count;
- context bundle size;
- correction/rework count.

If a metric is unavailable, report:

```text
status: not_observable
```

Never invent token, cost or runtime metrics.

Exact L0 -> L1 -> L2 quantitative promotion thresholds are intentionally deferred until the
first Logistics pool produces real evidence.

## 12. Portfolio inheritance rule

All later canonical modules are expected to adopt proven Logistics reference behavior for:

- front-door onboarding;
- inventory/current-state maintenance;
- fresh-worker startup;
- prompt lifecycle ownership;
- WIP=1 default;
- unified completion-report envelope;
- conformance evidence;
- pool control semantics;
- human end-of-pool gate.

A generally useful improvement discovered by the Logistics worker should first be reviewed
as a candidate shared pattern, then promoted to the shared reference before broader reuse.

## 13. Rollout sequence

```text
Logistics pilot
-> first fully manual pool
-> independent pool audit
-> operator quality/control-level decision
-> second Logistics pool at L0/L1/L2
-> stabilize worker/context/reporting automation
-> approve reusable reference profile
-> propagate profile to additional modules
-> compare cross-module conformance with shared tooling
```

## 14. Related authority/evidence

Unified reporting:
`coordination/standards/governance/module_prompt_execution_and_reporting_protocol.md`

Human Intent Delta:
`coordination/human_intent/deltas/2026-09-05__logistics_reference_rollout_pool_controls_and_reporting__human_intent_delta_v0_1.yaml`

Expanded human portfolio projection:
`coordination/human_intent/expanded_portfolio_current.md`

Adoption evidence:
`coordination/internal_work/blueprint/governance/2026-09-05__blueprint__logistics_reference_rollout_pool_controls_unified_reporting_and_interaction_adoption_v0_1.yaml`

## 15. No authority widening from this document

This standard does not itself authorize:

- automatic Blueprint ACCEPT/RETURN/HOLD;
- automatic first-pool next-prompt release;
- live provider writes;
- Telegram mutation;
- cross-repository writes;
- automatic commit/push;
- daemon/systemd activation;
- production rollout.
