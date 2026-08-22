# ForPrint v0.4.1 — Remaining Coordination Hardening Plan v0.1

Status: PLANNED / NOT ACTIVE
Current external pilot: H9 Logistics reference rollout.

This document captures missing coordination semantics discovered during the Logistics
pilot discussion. It intentionally does not change the H9 target while the Logistics
assistant is working.

## Why this belongs to v0.4.1

Current lifecycle covers roadmap, queue, active prompt, module execution, completion,
review and next work. Missing is a first-class execution-time clarification path.

A module may need one parameter, access, a cross-module fact, provider capability
confirmation, or an operator decision without the prompt being ready for RETURN/HOLD.

## B1 — `blueprint_v0_4_1_execution_baseline_and_drift_control_v0_1`

Goal: eliminate repeated assistant-side Git archaeology when Blueprint or a module
moves forward between prompt preparation, release, claim and execution.

### Core rule

A prompt is not permanently pinned to the repository HEAD that existed when it
was authored.

Instead, the prompt records immutable **required inputs and provenance**. At
execution start, a deterministic preflight decides whether the newer repository
state remains compatible.

`freshness != compatibility`

A repository may be current but a prompt superseded, or a prompt may have been
authored many commits ago while all of its required inputs remain compatible.

### Three baselines

Every execution distinguishes:

1. `release_baseline` — state observed when the prompt was released;
2. `execution_baseline` — real Blueprint/module state when the prompt was
   claimed and execution began;
3. `completion_baseline` — state observed when module work completed.

A later HEAD is not itself a failure.

### Required-input manifest

The released prompt/contract identifies only inputs it materially depends on:

- current coordination release;
- exact prompt contract;
- exact acceptance oracle;
- relevant standards/policies;
- relevant roadmap parent;
- declared cross-module contracts;
- other explicitly required artifacts.

For immutable inputs, record stable ID, path and SHA256 where appropriate.

Do **not** freeze the entire Blueprint repository merely because a prompt was
prepared against an older commit.

### Blueprint drift classification

Initial machine results:

- `READY_EXACT`;
- `READY_FORWARD_COMPATIBLE`;
- `READY_CURRENT_REVALIDATED`;
- `BLOCKED_BLUEPRINT_MATERIAL_DRIFT`;
- `BLOCKED_REQUIRED_INPUT_MISSING`;
- `BLOCKED_BREAKING_RELEASE_CHANGE`;
- `BLOCKED_PROMPT_SUPERSEDED`.

Ordinary unrelated commits should normally produce
`READY_FORWARD_COMPATIBLE`, not human investigation.

### Module repository drift classification

A prompt may also have been prepared against an older module commit.

If current module HEAD is a valid forward descendant, expected branch is correct
and worktree is safe, do not checkout the historical commit merely to match the
prompt baseline.

Initial results:

- `MODULE_EXACT`;
- `MODULE_FORWARD_COMPATIBLE`;
- `BLOCKED_MODULE_DIVERGED`;
- `BLOCKED_MODULE_DIRTY`;
- `BLOCKED_MODULE_BRANCH_MISMATCH`.

For initial unattended automation, require a clean module worktree before claim.
Per-prompt Git worktrees may be added later.

### Deterministic execution preflight

Target startup:

`coordination-sync-check`
→ `module-sync`
→ `prompt-read`
→ `execution-preflight`
→ `CLAIM`
→ work.

`coordination-sync-check` answers whether current Blueprint state is observable.

`execution-preflight` answers whether **this specific prompt** can safely execute
against that state.

The AI receives a deterministic readiness result instead of reconstructing Git
history manually.

### Claim-time execution epoch / lease

After successful preflight and claim create a stable execution identity:

- `execution_id`;
- prompt ID;
- claim timestamp;
- Blueprint execution baseline;
- module execution baseline;
- prompt contract SHA;
- acceptance oracle SHA;
- required-input manifest;
- execution policy;
- revalidation state.

After claim, execution does not continuously chase Blueprint HEAD.

Normal unrelated Blueprint commits do not interrupt it.

Material change is signaled explicitly through:

- `EXECUTION_REVALIDATION_REQUIRED`;
- `PROMPT_SUPERSEDED`;
- `EXECUTION_REVOKED`;

or another versioned equivalent.

### Completion provenance

Completion evidence records:

- release baseline;
- execution baseline;
- completion baseline;
- Blueprint drift classification;
- module drift classification;
- revalidation/revocation events;
- final source commit containing module work.

Blueprint review must not need chat archaeology to know what state was executed.

### Logistics reference validation

After H9 acceptance validate exact and forward-compatible Logistics fixtures,
including a prompt authored on an older Blueprint commit whose required inputs
remain unchanged.

Historical checkout is not required merely because Blueprint advanced.

---

## B2 — `blueprint_v0_4_1_coordination_data_classification_and_persistence_boundary_v0_1`

Goal: prevent growing coordination data from becoming an unqueryable collection
of files while preserving Git-native governance and future database migration.

### Core decision: hybrid storage

Do **not** move the entire Blueprint into SQL.

Use storage according to data semantics.

#### A. Git/YAML/Markdown — declarative canonical truth

Keep human-reviewable, versioned governance artifacts in Git:

- current release authority;
- standards/policies;
- roadmaps;
- released prompts;
- prompt contracts;
- acceptance oracles;
- durable operator scope decisions/waivers that change project truth;
- sealed reviews and promotion decisions;
- module registry and durable architecture documentation.

YAML remains suitable for structured human-edited governance.
Markdown remains suitable for explanatory/contract documentation.
JSON may be used for generated machine interchange.

File count alone is not a reason to move this layer into SQL.

#### B. Coordination operational store — high-churn runtime truth

When runtime automation becomes active, store high-churn state in a small DB:

- append-only event journal;
- execution runs/baselines/leases;
- question threads/messages;
- current prompt/module runtime projection;
- attention events;
- notification delivery/ack state;
- worker leases/retry state;
- idempotency records;
- correlation/index state;
- runtime health projections.

For the single-server pilot:

`SQLite + WAL`

Do not make the future business database a prerequisite for coordination.

#### C. Filesystem/artifact store — bulky evidence

Large logs, archives, generated reports, diffs and context packs remain files.

The operational DB stores artifact metadata:

- artifact ID;
- path/URI;
- SHA256;
- media/type;
- producer;
- correlation ID.

Do not copy large evidence payloads into relational rows by default.

#### D. Secret storage

Secrets, tokens, passwords and private credentials must not live in roadmap YAML,
prompt text, SQLite event payloads or Git.

Store secret references only where needed.

### Avoid dual sources of truth

A Git-governed object is not silently duplicated as an independently mutable DB
row.

The DB may index a canonical artifact by stable ID, Git path, Git commit, SHA256
and schema version while authoritative artifact bytes remain in Git.

For operational events, the coordination store is authoritative runtime history.

Only durable project decisions that change governance/project truth are promoted
into explicit Git artifacts through reviewed transactions.

### Initial schema families

The eventual runtime should represent tables equivalent to:

- `event_journal`;
- `execution_runs`;
- `execution_revalidations`;
- `question_threads`;
- `question_messages`;
- `attention_events`;
- `operator_decisions`;
- `notification_deliveries`;
- `worker_leases`;
- `prompt_runtime_state`;
- `module_runtime_state`;
- `artifact_index`;
- `idempotency_keys`;
- `schema_migrations`.

Exact normalization remains an implementation decision.

### SQLite operating rules

Pilot rules:

- WAL mode;
- foreign keys enabled;
- explicit schema version;
- migrations from day one;
- bounded transactions;
- deterministic unique/idempotency constraints;
- one coordination-service write boundary;
- assistants do not receive arbitrary direct SQL writes;
- backup through SQLite-safe backup mechanisms, not naive live-file copies;
- database binary is not committed to Git.

### Migration-ready boundary

Code depends on a storage interface such as `CoordinationStore`, not scattered
SQLite-specific behavior.

Use:

- stable IDs;
- UTC timestamps;
- portable scalar types;
- explicit migrations;
- versioned event payload schemas;
- repository/service interfaces;
- database-independent contract tests.

This keeps later migration to PostgreSQL mechanical.

### When SQLite is enough

SQLite remains appropriate while:

- coordination runs mainly on one server;
- write concurrency is moderate;
- one coordination service owns writes;
- HA is not required;
- heavy evidence remains outside the DB.

Large row counts alone are not a reason to migrate.

### When to move to PostgreSQL/central storage

Re-evaluate for real requirements such as:

- multiple hosts writing concurrently;
- high write contention;
- remote workers requiring service access;
- HA/failover;
- replication;
- richer operational analytics;
- stronger concurrent transaction needs.

Migration is driven by operational requirements, not file-count anxiety.

### Separation from future ForPrint business database

Do not accelerate the future business-database module merely to host development
coordination.

Customers, orders, products, pricing and logistics business truth have different
ownership/security/lifecycle boundaries from development coordination events.

Both may later share physical PostgreSQL infrastructure while keeping separate
schemas/databases and contracts.

Coordination must not be blocked on the business DB roadmap.

### Retention and audit

Define retention by class:

- runtime projections may be rebuilt;
- append-only audit events follow audit retention;
- large logs may be archived/compressed;
- durable project/operator decisions remain in Git;
- DB backups are restore-tested.

### Acceptance intent

B2 is complete when there is an explicit source-of-truth matrix,
migration-ready storage contract, retention/backup policy and tested decision
about what remains in Git versus what later moves into SQLite.

B2 does **not** itself enable a persistent daemon or live SQLite runtime. That
implementation stays in the future autonomy/runtime program unless separately
promoted.

## Q1 — blueprint_v0_4_1_clarification_question_lifecycle_v0_1

Create first-class question threads.

Lifecycle:
`OPEN -> ROUTED -> ANSWERED -> CONFIRMED -> RESOLVED`

Alternative terminals:
`ESCALATED`, `CANCELLED`, `EXPIRED`.

Prompt may remain `in_progress` with `waiting_on_clarification`.

Minimum identity:
question_id, module_id, prompt_id, roadmap_step_id, requester, target,
correlation_id, blocking, question_class, round, question, answer,
evidence_refs and timestamps.

A question alone never means RETURN or HOLD.

## Q2 — blueprint_v0_4_1_bounded_clarification_and_escalation_v0_1

Default:
`maximum_unresolved_round_trips_per_question_thread: 5`

This is per unresolved issue, not five questions for the whole prompt.

After round five:
- autonomous dialogue for that thread stops;
- thread becomes ESCALATED;
- blocking prompt state becomes visibly waiting/blocked;
- escalation packet contains original question, all rounds, evidence, unresolved fact,
  impact, safe options and recommended next action.

## Q3 — blueprint_v0_4_1_execution_blocker_taxonomy_v0_1

Initial reasons:
missing_input, ambiguous_requirement, access_required,
credential_or_token_expired, external_resource_unavailable,
dependency_contract_missing, dependency_module_blocked, provider_api_unavailable,
environment_failure, policy_conflict, unsupported_capability, security_boundary,
manual_decision_required.

Keep distinct:
- clarification_required;
- execution_blocked;
- unable_to_execute;
- RETURN;
- HOLD.

`unable_to_execute` is module evidence for review, not Blueprint RETURN.

## Q4 — blueprint_v0_4_1_immutable_prompt_adjustment_and_decision_v0_1

Canonical rule:

**A released prompt is an immutable execution contract.**

Do not edit/delete/rewrite released prompt requirements.

Later changes use correlated artifacts/events:
operator_decision, scope_adjustment, waiver, skip_optional,
clarification_resolution, blocker_resolution, cancellation,
follow_up_prompt or superseding_prompt.

A requirement that is not executed never disappears. It must have explicit disposition.

Minimum decision evidence:
decision_id, related event/question, prompt_id, requirement/substep/criterion,
actor, decision type, reason code, explanation, timestamp, execution effect,
acceptance effect and evidence refs.

Completion report must include `Execution deviations / operator decisions`,
or explicitly `none`.

## Q5 — blueprint_v0_4_1_common_coordination_event_envelope_v0_1

Define one event envelope before building any daemon.

Fields:
event_id, event_type, occurred_at, producer, target, module_id, prompt_id,
roadmap_step_id, correlation_id, causation_id, severity, blocking,
schema_version, payload, evidence_refs, idempotency_key.

Events are immutable observations; state is projected from events.

Initial families:
claim/status, clarification, answer/resolution, execution blocker,
unable-to-execute, operator attention, operator decision, completion publication.

## Q6 — blueprint_v0_4_1_operator_attention_semantics_v0_1

Define semantic attention reasons without implementing Telegram yet:

clarification_escalated, access_required, execution_blocked, unable_to_execute,
no_dispatchable_work, operator_execution_required, operator_acceptance_required,
manual_review_required, coordination_freshness_stale, dependency_blocked,
repeated_verification_failure.

Attention state is independent from transport.

## Q7 — blueprint_v0_4_1_cross_module_question_routing_contract_v0_1

Allowed target identities:
- module -> Blueprint/operator;
- module -> module;
- Blueprint -> module.

Current v0.4.1 scope is contract/evidence semantics only, not persistent runtime.

Rules:
- no cross-repository writes;
- no module writes Blueprint to deliver live questions;
- answers carry evidence refs;
- strategic ambiguity escalates;
- secrets/access may route directly to operator;
- five-round limit remains per thread.

## Q8 — blueprint_v0_4_1_logistics_clarification_reference_validation_v0_1

After H9 acceptance, prove with Logistics:
- recoverable clarification does not RETURN prompt;
- module and operator routing identities are representable;
- five-round escalation is deterministic;
- blocker reason is explicit;
- released prompt remains immutable;
- scope adjustment is separate evidence;
- completion preserves deviations;
- attention state is visible;
- no automatic ACCEPT;
- no automatic next release;
- no Blueprint write into module repo.

## Proposed order

H8 SEALED -> H9 CURRENT -> B1 -> B2 -> Q1 -> Q2 -> Q3 -> Q4 -> Q5 -> Q6 -> Q7 -> Q8
-> H10 ecosystem rollout -> H11 legacy retirement/archive audit.

Stable IDs, not display numbers, are durable.

## Explicitly not part of Q1-Q8

Do not implement here:
persistent daemon, SQLite runtime, systemd, automatic Codex launch,
automatic ACCEPT, automatic next activation, Telegram transport,
intelligent development bot, full autonomous module-to-module runtime,
AgentRunner, broad autonomy/risk classes.

Those belong to the future autonomy initiative.

## H10 entry refinement

Preferred H10 entry:
- H9 accepted;
- B1-B2 accepted or explicitly waived;
- Q1-Q8 accepted or explicitly waived;
- current release docs reconciled;
- Logistics still passes as reference;
- no new legacy dependency.
