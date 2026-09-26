<!-- FORPRINT_BLUEPRINT_ASSISTANT_PROTOCOL_START -->
# ForPrint System Blueprint — AI Assistant Entry

<!-- bootstrap-mandatory-startup-contract-2026-09-15:start -->
## Mandatory startup contract — 2026-09-15 operator reconciliation

A fresh broad Blueprint assistant must load this section before the first project mutation or roadmap decision.

- `MUST_READ_BEFORE_FIRST_ACTION`: Project Constitution, this `AGENTS.md`, `coordination/bootstrap/START_HERE.md`, current lifecycle/roadmap reconciliation, current Work Front when one exists, and the active reconciliation-question projection.
- `MUST_VERIFY`: repository root/HEAD, `ROADMAP_SYNC=IN_SYNC`, current lifecycle state, no hidden open Work Front, source freshness, and whether an evening/return handoff package is awaiting intake.
- `OPERATOR_INTERACTION_MODE`: address the operator as a man; keep the tone friendly, direct and informal-professional; explain roadmap status in human language first and put machine IDs second.
- `EXECUTION_ENTRYPOINT`: Python-first bounded action files with unique semantic/versioned names; `tmp.py` is only a volatile operator alias and must self-materialize to a unique source before mutation.
- `EVENING_MODE`: when the operator is away from the computer, use conversation for architecture/decisions/risks and produce a Z-package at a meaningful session end; do not assume repo mutation is available.
- `MORNING_Z_PACKAGE_INTAKE`: never execute a Z-package as a batch. Inspect -> reconcile against fresh repo -> classify each atomic item -> map to roadmap -> assess dependencies -> resolve ambiguous conflicts -> update canonical planning -> execute only currently due work.
- `PROJECT_INDEX_ENTRYPOINT`: use the existing Bootstrap/Knowledge/Index surfaces before inventing new navigation or capability duplicates.
- `OPEN_RECONCILIATION_QUESTIONS`: read `coordination/bootstrap/ACTIVE_RECONCILIATION_QUESTIONS.yaml`; it is a bootstrap projection only and does not replace the Q1 clarification lifecycle.
- `DO_NOT_IMPROVISE`: a newer operator statement that conflicts with canonical project policy must create an explicit reconciliation item; never silently overwrite the older rule. Show old rationale/provenance, new request/rationale, options, dependency/roadmap impact and recommendation before superseding.

Roadmap answers to the operator must say what capability was completed, what is being built now, why it matters, and what the next 3–5 meaningful steps implement/change. `CF-*`, work IDs and event sequences are traceability metadata, not the primary explanation.

The current pilot sequence is scoped and explicit: after CF-07/08/09, run one bounded internal Blueprint worker zero-stage pilot; after internal stability, Logistics remains the first external/module pilot. This does not authorize broad multi-module rollout or weaken later readiness/autonomy gates.
<!-- bootstrap-mandatory-startup-contract-2026-09-15:end -->


If you are a new AI assistant with no repository context, do not read the tree
randomly and do not mutate the project first.

Mandatory zero-context project entry:
1. Read `coordination/bootstrap/START_HERE.md`.
2. From the Blueprint repository root run `make assistant-context-pack`.
3. Read the generated portfolio context archive before broad planning or mutation.
4. For a concrete authorized task, still build/use the strict task-specific context;
   the project-entry archive does not replace `scripts/coordination/build_context_bundle.py`
   or its `--task-context` mode.

1. Read `coordination/releases/current.yaml` — release authority.
2. Read `machine/module_identity_registry.yaml` — canonical module identities.
3. Read `indexes/knowledge_summary.yaml`.
4. Use `indexes/document_catalog.yaml`, `indexes/references.json`,
   `indexes/dependencies.json`, `indexes/prompts.yaml`, `indexes/roadmaps.yaml`,
   `indexes/governance.yaml`, `indexes/contracts.yaml`,
   `indexes/source_coverage.yaml`, and `indexes/incoming_requests.yaml`.
5. Read `coordination/roadmaps/details/forprint_system_blueprint/`.

Choose onboarding mode:
- `BOOTSTRAP_WITHOUT_TASK` when no concrete task is assigned;
- `BOOTSTRAP_FOR_TASK` when a roadmap step/task exists.

Prefer one generated bootstrap/task context bundle over repeated manual transfer
of individual files.

Before implementation resolve: active roadmap step, process-contract revision,
applicable governance/standards, dependencies, validators and acceptance evidence.

Before handoff: refresh/check derived indexes, update required documentation,
verify the pinned process revision is still supported, run deterministic checks,
and produce completion/conformance evidence.

Derived indexes are navigation/evidence, not authority. `make check` validates;
it must not silently auto-fix project state.
<!-- FORPRINT_BLUEPRINT_ASSISTANT_PROTOCOL_END -->

<!-- assistant-temporary-execution-and-artifact-handoff-v0-1:start -->
## Temporary assistant execution and artifact handoff

Read:
`coordination/standards/governance/assistant_temporary_execution_and_artifact_handoff_protocol_v0_1.md`.

Operational rule:
- operator-side `tmp.py` is volatile execution convenience, not durable history;
- every assistant-delivered operator-side action script must use a unique filename; do not reuse a fixed `tmp.py` filename for successive delivered actions because distinct action source/hash identity must remain visible;
- `tmp.py` is only a volatile/local operator alias; if an operator/runtime path starts through `tmp.py`, first preserve an exact uniquely named action source in the current `tmp/assistant_work/<horizon_id>/` workspace with the next `NNNN__` prefix, then continue execution from that unique source before project mutation;
- do not depend on old `tmp.py`, shell scrollback or prior `tee` output being preserved;
- during a bounded manual work horizon, operator-facing assistant artifacts accumulate under one
  horizon workspace `tmp/assistant_work/<horizon_id>/`; do not create a new subdirectory for each
  small task;
- reserve `0000__workspace_index_v0_1.yaml` for local workspace metadata and prefix subsequent
  user-facing artifacts with a zero-padded monotonic index: `NNNN__<semantic_name>...`;
- within one horizon workspace, the highest numeric prefix is the newest generated artifact;
- filenames after the index retain semantic task/work identity and artifact role; never silently
  overwrite an existing numbered artifact;
- per-task subdirectories are exceptional and allowed only for tool-internal candidate/staging,
  extracted-archive, debug, or explicitly isolated parallel-execution structure;
- existing tool-owned runtime directories and historical `tmp/assistant_work/<work_id>/` layouts
  are grandfathered; do not mass-migrate them during unrelated work;
- cleanup permission is optional deletion permission; the operator may retain closed session
  artifacts for later analysis;
- never use broad cleanup/reset/stash to manufacture cleanliness.

If temporary history is missing, prefer a new bounded read-only probe over asking the human
to reconstruct disposable execution history.
<!-- assistant-temporary-execution-and-artifact-handoff-v0-1:end -->

<!-- logistics-reference-rollout-and-pool-governance-v0-1:start -->
## Logistics reference rollout and execution pools

Read:
`coordination/standards/governance/module_reference_rollout_execution_pool_policy_v0_1.md`
and the unified completion-report profile in
`coordination/standards/governance/module_prompt_execution_and_reporting_protocol.md`.

Current rollout rule:
- `logistics_service` is the reference module for reusable coordination and self-knowledge behavior;
- first substantial Logistics pool is `L0_FULL_MANUAL_PROMPT_GATE`;
- every prompt in that first pool requires operator review before the next prompt is released;
- after each pool the operator explicitly chooses the next pool control level;
- every pool ends in human review even when child progression is automated;
- machine child-step conformance is not Blueprint `ACCEPT`;
- all modules converge on one completion-report envelope while module internals may differ;
- after the first Logistics pool perform an independent repository inventory/audit before
  widening automation or propagating the reference profile.
<!-- logistics-reference-rollout-and-pool-governance-v0-1:end -->

<!-- assistant-operator-language-convention-v0-1:start -->
## Assistant/operator Ukrainian language convention

Read:
`coordination/standards/governance/operator_interaction_profile_v0_1.yaml`.

When communicating in Ukrainian:
- the AI assistant refers to herself using feminine grammatical forms
  (`зробила`, `підготувала`, `перевірила`);
- the human operator is addressed using masculine grammatical forms
  (`зробив`, `передав`, `перевірив`);
- do not swap these roles or alternate grammatical gender without an explicit operator update.
<!-- assistant-operator-language-convention-v0-1:end -->


<!-- human-intent-ledger-v0-1:start -->
## Human intent preservation
For substantial architecture / evening-review work, read `coordination/human_intent/README.md`.
Completion of the review requires a Human Intent Delta, append-only module intent updates, regenerated expanded human portfolio, and an explicit GAP list. Do not replace missing exact human details with invented equivalents.
<!-- human-intent-ledger-v0-1:end -->

- Portfolio review rendering/content standard: `coordination/standards/governance/portfolio_rendering_and_content_specification_v0_1.md`
- Latest integrated evening-review architecture index: `coordination/internal_work/blueprint/evening_reviews/2026-08-31/README.md`


<!-- FORPRINT_EXECUTION_PROGRESS_VISIBILITY_START -->
## Execution progress visibility

Read:
`coordination/standards/automation/execution_progress_visibility_contract_v0_1.yaml`.

Operational rule for future assistants and long-running project commands:
- the operator terminal must not remain silent for more than the configured heartbeat
  interval while a long task is still running;
- multi-phase scripts must emit `START`, periodic `HEARTBEAT` when otherwise silent,
  and terminal `PASS`/`FAIL` events with the phase name and elapsed time;
- assistant-supplied scripts expected to run longer than a few seconds must use
  `scripts/coordination/execution_progress.py` when that helper is available;
- do not hide a long subprocess behind capture-only execution without visible progress;
- detailed child output remains durable evidence even when successful terminal output is compact;
- progress goes to stderr; final machine-readable summaries/paths may remain on stdout;
- default mode is visible: `FORPRINT_PROGRESS=always`,
  `FORPRINT_PROGRESS_HEARTBEAT_SECONDS=15`,
  `FORPRINT_PROGRESS_CHILD_OUTPUT=failures`;
- suppressing progress requires an explicit `--no-progress` or
  `FORPRINT_PROGRESS=never`; silence is never the implicit default;
- for an operator-side shell log, prefer
  `python -u <unique_action_file>.py 2>&1 | tee tmp/report.txt`.

Progress visibility does not widen mutation, rollback, cleanup, worker-dispatch,
commit, push, or release authority.
<!-- FORPRINT_EXECUTION_PROGRESS_VISIBILITY_END -->


<!-- FORPRINT_CONTINUITY_CONTRACT_START -->
## Continuity contract

Read:
`coordination/standards/automation/continuity_contract_v0_1.yaml`.

Binding continuity rules:
- chat transcripts are not project source of truth;
- meaningful project state changes become append-only continuity events once the
  immutable checkpoint subsystem is installed;
- checkpoint correction is append-by-supersession, never in-place history rewrite;
- checkpoint evidence binds final post-repair artifact hashes, not raw candidate hashes;
- dirty Git state is a valid source-state baseline and must be fingerprinted rather
  than cleaned with reset/stash/rebase;
- `ACTIVE -> CLOSED` is forbidden: closure requires checkpoint, validation,
  continuity validation, reconciled source delta, and blocker disposition;
- generated continuity projections and assistant handoff archives are derivative
  and cannot grant release, queue, worker-dispatch, operator-approval, or foreign-module
  mutation authority;
- `UNRECONCILED_CURRENT_DELTA` must remain visible when current durable state differs
  from the latest accepted checkpoint;
- handoff packs must be reconstructable without chat history and carry source/compiler
  fingerprints plus included-file hashes.

The checkpoint writer is installed at `scripts/coordination/continuity.py`.
Create checkpoints only through `continuity.py checkpoint --spec <path>` or the
`make continuity-checkpoint SPEC=<path>` wrapper; never edit/delete accepted event
files in place. The generic knowledge index intentionally excludes the event ledger.

Current continuity projections live under `coordination/continuity/projections/` and
are generated only by `scripts/coordination/build_continuity_projections.py`.
Use `make continuity-projections-refresh` for an explicit refresh and
`make continuity-projections-check` for a non-mutating exact check. Never edit projection
files manually. `UNRECONCILED_CURRENT_DELTA.yaml` must remain visible when durable source
state differs from the latest checkpoint; projection files do not grant release, queue,
worker-dispatch, operator-approval, or foreign-module mutation authority.
During faithful isolated `make check`, continuity source-state is frozen at mirror creation
through a root-scoped baseline so validation-generated runtime reports cannot redefine the
source input; this does not implicitly exclude reports from normal source-state fingerprints.
Continuity foundation through Step 12 (`u179h`) is canonically closed. Current manual control-plane horizon is `coordination/roadmaps/details/forprint_system_blueprint/control_foundation_near_horizon_program_v0_1.yaml`: CF-01 is the repository/baseline reconciliation work (`u180a`) and CF-02 is the roadmap/execution reconciliation controller. Remain in manual operator mode for broad/general dispatch. The dated startup contract above permits only the explicitly scoped CF-10 internal Blueprint manual/shadow zero-stage exception before the later broad readiness gate.
<!-- FORPRINT_CONTINUITY_CONTRACT_END -->

<!-- FORPRINT_ASSISTANT_HANDOFF_COMPILER_START -->
## Deterministic assistant handoff pack

The continuity handoff operator surface is:

`make assistant-pack`

It builds a deterministic runtime ZIP under `tmp/assistant_handoff/` from immutable
continuity events plus the current working-tree source state. The pack includes
`00_READ_FIRST.md`, mission/bootstrap inputs, latest checkpoint, current in-memory
continuity projections, blockers/unknowns, next horizon, roadmap/dependency slices,
knowledge-health evidence, compiler source and a hash-bound manifest.

Binding boundaries:
- the pack is non-authoritative and cannot grant release, queue, worker-dispatch,
  foreign-module mutation or operator-approval authority;
- chat transcripts are excluded;
- current unreconciled durable delta is preserved visibly rather than silently
  folded into the latest checkpoint;
- archive bytes are deterministic for the same compiler and repository state;
- `make assistant-handoff-check` validates buildability without writing an archive;
- the legacy `make assistant-context-pack` Project Context surface remains separate
  compatibility tooling until its later determinism/provenance/safety hardening and
  zero-context startup migration are explicitly accepted.
<!-- FORPRINT_ASSISTANT_HANDOFF_COMPILER_END -->

<!-- FORPRINT_CONTINUITY_LIFECYCLE_ENFORCEMENT_START -->
## Continuity lifecycle enforcement v0.1

Accepted work lifecycle is append-only and event-backed:

`PLANNED -> ACTIVE -> CHECKPOINTED -> VALIDATED -> CLOSED`

Rules:
- direct `ACTIVE -> CLOSED`, `PLANNED -> CLOSED`, and `CHECKPOINTED -> CLOSED` are forbidden;
- `CHECKPOINTED -> ACTIVE` and `VALIDATED -> ACTIVE` are remediation-only transitions with explicit reason;
- `CLOSED` is immutable for the same `work_id`; continuation requires a new correlated work id;
- close requires a checkpoint, validation-pass evidence, continuity/source-state reconciliation, and empty blockers or explicit blocker deferral;
- lifecycle events are written to `coordination/continuity/events/` and share the same append-only content-addressed chain;
- pre-enforcement completed work may only be migrated with an explicit `WORK_SUPERSEDED` event bound to the accepted enforcement boundary; history is never rewritten;
- lifecycle authority does not grant release, queue, worker-dispatch, foreign-module mutation, or operator-approval authority.

Operator surfaces:
- `make continuity-lifecycle-check` validates lifecycle semantics without mutation;
- `make continuity-lifecycle-status` shows derived lifecycle state;
- transitions use `scripts/coordination/continuity_lifecycle.py transition ...`;
- checkpoint creation remains owned by `scripts/coordination/continuity.py checkpoint --spec ...`.
<!-- FORPRINT_CONTINUITY_LIFECYCLE_ENFORCEMENT_END -->


<!-- FORPRINT_PROJECT_CONSTITUTION_START -->
## Project Constitution and authority hierarchy

Canonical machine-readable Project Constitution:

`coordination/standards/governance/project_constitution_v0_1.yaml`

Authority precedence is:

`Project Constitution -> Module Policy -> Execution Profile -> Work Front`

A lower layer may narrow authority. It may not widen authority without a separate,
explicit, evidence-bound authority gate. Generated projections, assistant packs and
chat are not authority. Accepted history is immutable. Foreign writes require explicit
authority. Completion requires independent validation. Blueprint AI may not modify and
self-certify the same guardrail change.

Before governed lifecycle/roadmap mutation or assistant-pack execution, preserve these
boundaries and run:

`make project-constitution-check`

CF-03 does not itself implement the CF-04 Work Front schema, CF-06 Execution Profile
registry, worker dispatch, release authority or automatic next-step activation.
<!-- FORPRINT_PROJECT_CONSTITUTION_END -->

<!-- FORPRINT_WORK_FRONT_CONTRACT_START -->
## Canonical Work Front and capability reuse gate

Canonical machine-readable Work Front contract:

`coordination/standards/automation/work_front_contract_v0_1.yaml`

A Work Front is the bounded execution-authority contract for one unit of work. Human intent,
chat, generated projections and assistant packs are not Work Front authority.

A valid Work Front must explicitly carry objective, scope, exclusions, provenance,
dependencies, outputs, acceptance, stop conditions, Work Front authority and capability
reuse evidence.

Before NEW implementation, search existing capabilities, scripts, libraries, and APIs and record
exactly one disposition:

`REUSE / EXTEND / ADAPT / REPLACE / NEW`

`NEW` requires explicit rationale and evidence that the bounded reuse search was performed.

Task-execution assistant packs must validate the supplied `FRONT`. The existing no-`FRONT`
`make assistant-pack` remains a bounded PROJECT_ONBOARD compatibility surface until CF-08
Handoff v2; it does not become task execution authority. Dispatcher gating requires a valid
Work Front, but CF-04 does not grant worker-dispatch authority.

Run:

`make work-front-contract-check`

For an individual front:

`make work-front-check FRONT=<path>`

CF-04 does not implement CF-05 history, CF-06 Execution Profiles, CF-07 Procedure Graphs,
CF-08 Handoff v2, CF-09 dispatcher launch integration, release authority, foreign writes or
Blueprint AI trial readiness.
<!-- FORPRINT_WORK_FRONT_CONTRACT_END -->

<!-- FORPRINT_CF05_HISTORY_LEDGER_START -->
## Workfront and execution-attempt durable history

Read:
`coordination/standards/automation/workfront_history_contract_v0_1.yaml`
and
`coordination/standards/automation/execution_attempt_ledger_contract_v0_1.yaml`.

Operational rule:
- Work Front remains the bounded execution-contract authority;
- the Continuity Event Store remains actual roadmap lifecycle execution authority;
- Workfront History and Execution Attempt Ledger are separate append-only fact histories;
- a retry creates a new attempt and never overwrites the prior attempt;
- failed and partial attempts remain durable;
- partial/interrupted attempts preserve resume coordinates from the latest accepted mutation/event and must not replay already accepted work;
- raw chat may be provenance evidence only and is never execution authority;
- history records do not grant worker-dispatch, release or foreign-repository-write authority;
- CF-06 Execution Profiles are not implemented by CF-05.
<!-- FORPRINT_CF05_HISTORY_LEDGER_END -->

<!-- FORPRINT_EXECUTION_PROFILE_REGISTRY_START -->
## Execution Profiles registry

Canonical contract:
`coordination/standards/automation/execution_profile_registry_contract_v0_1.yaml`

Canonical registry:
`coordination/registry/execution_profiles_v0_1.yaml`

Execution Profiles are reusable versioned policy bundles composed from reasoning,
authority, budget and context policy. They are not execution authority and do not grant
dispatch, release or foreign-repository-write authority.

Authority precedence remains:

`Project Constitution -> Module Policy -> Execution Profile -> Work Front`

Profile permissions are a ceiling, not a grant. Effective authority is the intersection
of higher authority, the selected profile ceiling and the Work Front. Effective budget is
the most restrictive tier. A profile or operator override may narrow bounds; a request
for higher budget or wider authority requires separate explicit escalation evidence and
still does not bypass higher canonical authority.

The initial registry contains:
`deep-readonly-analysis@r1`, `deep-dev@r1`, `standard-dev@r1`,
`light-maintenance@r1`.

Canonical profiles bind only abstract reasoning/model tiers; provider/model backends stay
replaceable. The selected `profile_id@revision` is suitable for
`Execution Attempt Ledger.profile_ref_or_revision`.

Dispatcher recommendation is recommendation only, not dispatch authority. CF-06 does not
implement CF-07 Procedure Graphs, CF-08 Handoff v2, CF-09 Dispatcher integration, actual
worker launch, release authority, foreign writes or Blueprint AI trial readiness.

Run:
`make execution-profile-registry-check`
<!-- FORPRINT_EXECUTION_PROFILE_REGISTRY_END -->


<!-- assistant-handoff-v2-s1-v0-1:start -->
## CF-08 Handoff v2 S1 contract

Canonical contract: `coordination/standards/automation/assistant_handoff_v2_contract_v0_1.yaml`.

CF-08 S1 defines the shared contract only. It extends accepted Handoff v1 and
Task Context/Fresh Context surfaces; it does not create a parallel handoff framework.

The only launch modes are `PROJECT_ONBOARD` and `TASK_EXECUTION`. ACK/result field names
are exact and aliases are invalid. Handoff packages grant no execution, dispatch,
release, push/merge or cross-repository authority.

Runtime compiler integration remains a later CF-08 slice. Dispatcher integration,
actual worker launch and central retry/result routing remain deferred to CF-09.
<!-- assistant-handoff-v2-s1-v0-1:end -->

<!-- assistant-handoff-v2-s2-runtime-v0-1:start -->
## CF-08 Handoff v2 S2 runtime integration

Canonical runtime contract: `coordination/standards/automation/assistant_handoff_v2_runtime_contract_v0_1.yaml`.
Canonical runtime adapter: `scripts/coordination/assistant_handoff_v2_runtime_v0_1.py`.

S2 is a thin adapter over accepted Handoff v1 and Task Context/Fresh Context mechanisms. It does not create a parallel context framework. PROJECT_ONBOARD delegates to the deterministic Handoff v1 builder. TASK_EXECUTION requires Work Front, Execution Profile, task-context inputs and governed procedure binding (or explicit NOT_REQUIRED reason) and delegates task-context compilation to the existing builder.

S2 grants no execution, dispatch, release, push/merge or cross-repository authority. Exact result validation and bounded self-repair remain S3. Freshness/resume hardening remains S4. Dispatcher integration and worker launch remain CF-09 or later.
<!-- assistant-handoff-v2-s2-runtime-v0-1:end -->

<!-- assistant-handoff-v2-s3-result-v0-1:start -->
## CF-08 Handoff v2 S3 result validation

Canonical result contract: `coordination/standards/automation/assistant_handoff_v2_result_contract_v0_1.yaml`.
Canonical result runtime: `scripts/coordination/assistant_handoff_v2_result_v0_1.py`.

S3 validates the exact nine-field Handoff v2 result envelope before return and binds `handoff_manifest_sha256` to the origin manifest. Result field aliases and extra fields are invalid. `attempt_id` reuses Execution Attempt Ledger identifier semantics without appending central attempt history; central result routing/history remains CF-09.

Bounded self-repair is local and authority-neutral. It never writes project source, never widens Work Front/Profile/Procedure authority, and never rewrites manifest hash, attempt id, status, missing fields or aliases. The only S3 v0.1 automatic repair is exact duplicate removal in `changed_paths`; every applied repair is recorded in `self_repair_attempts` and `validation_evidence`, with a hard ceiling of three attempts.

Freshness and durable resume hardening remain S4. Dispatcher integration, worker launch and central retry orchestration remain CF-09 or later.
<!-- assistant-handoff-v2-s3-result-v0-1:end -->

<!-- assistant-handoff-v2-s4-freshness-resume-v0-1:start -->
## CF-08 Handoff v2 S4 freshness + durable resume

Canonical S4 contract: `coordination/standards/automation/assistant_handoff_v2_freshness_resume_contract_v0_1.yaml`.
Canonical S4 runtime: `scripts/coordination/assistant_handoff_v2_freshness_resume_v0_1.py`.

S4 keeps the existing Handoff v2 family and reuses the Fresh Context Gate, Execution Attempt Ledger, roadmap reconciliation, and lifecycle status. Before accepting a returned result, the origin `source_state_fingerprint` and `lifecycle_roadmap_cursor` must still match a freshly compiled live Handoff v2 runtime manifest.

`resume_coordinates` are structured and bind to the same `attempt_id`, `handoff_manifest_sha256`, source-state fingerprint and lifecycle/roadmap cursor. Partial/interrupted/blocked/retryable results additionally require `latest_completed_node`, `latest_accepted_ref`, and non-empty `replay_forbidden_refs`. If `retry_of_attempt_id` is present it must differ from the current attempt id.

S4 grants no execution, dispatch, release, lifecycle mutation or cross-repository write authority. It does not append central attempt history and does not route resumes. Dispatcher integration, worker launch, central resume routing and result routing remain CF-09.
<!-- assistant-handoff-v2-s4-freshness-resume-v0-1:end -->
