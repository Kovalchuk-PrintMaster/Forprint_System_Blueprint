

Master Bootstrap / Continuation Prompt

Status: design + implementation bootstrap
Owner: ForPrint System Blueprint
Prepared: 2026-08-13
Purpose: allow any new coordination assistant to resume the v0.4 workstream without relying on chat history.

1. Mission

Build Completion Exchange / Coordination Lifecycle v0.4 as a bounded, auditable, dependency-aware, operator-controlled closed loop for all ForPrint modules.

The target is not merely “a better completion packet”.

The target is:

ROADMAP
  ↓
PROMPT BUFFER / QUEUE
  ↓
ACTIVE PROMPT
  ↓
MODULE EXECUTION
  ↓
MODULE COMPLETION OUTBOX
  ↓
BLUEPRINT DISCOVERY
  ↓
READ-ONLY INTAKE / REVIEW
  ↓
EXPLICIT OPERATOR DECISION
  ↓
BLUEPRINT ROADMAP UPDATE
  ↓
NEXT PROMPT SELECTION / ACTIVATION
  ↓
ROADMAP + PROMPT BUFFER HEALTH CHECK
  └──────────────────────────────→ repeat

This closed loop must work for every registered ForPrint module and Blueprint self-coordination. It must work locally without GitHub; CI/GitHub may later be transport/trigger only.

2. Known repository checkpoints at bootstrap

Blueprint:

/srv/software_development/forprint-project/forprint_system_blueprint
branch: audit/blueprint-inventory-refresh-2026-07-29
known HEAD: f80c8a6b8cf3cc0b348f3bf2504e6add11f2b1c8
commit: governance(blueprint): verify v0.3 publication from remote evidence

Logistics reference:

/srv/software_development/forprint-project/forprint_logistics_service
branch: feature/logistics-tracking-events-contract-v01
known HEAD / remote: ecf3e23223cec90e47ac206be9a33c3e3b02673c

These are only bootstrap checkpoints. A new assistant MUST re-read Git state before doing work.

3. Current Completion Exchange state

At bootstrap:

v0.2:
  operational current
  normal acceptance allowed

v0.3:
  candidate/reference validation
  normal acceptance forbidden
  reference module: logistics_service
  reference prompt: logistics_service_tracking_events_v0_1

Tracking Events v0.3 reached:

operator status: REFERENCE_VALIDATION_READY
publication verified: true
requirements: 10/10
required checks: 9/9
warnings: 0
RESULT: COMPLETION_INTAKE_CHECK_PASSED

This does NOT mean ACCEPTED and does NOT promote v0.3.

4. Why v0.3 must not be promoted

Manual semantic audit showed that v0.3 is structurally strong but not expressive enough.

It correctly validates:

source prompt SHA;

requirement IDs;

required check IDs;

implementation base/tip;

evidence paths;

changed-path membership;

safety boundary flags;

packet/report frontmatter;

superseding chain;

external Git publication.

But it does not prove semantic completeness of:

SOURCE PROMPT → PROMPT CONTRACT

A mandatory source-prompt obligation can be omitted from the machine contract and therefore disappear from the 10/10 score.

Tracking Events manual audit found obligations that were not separately machine-modeled, including:

detailed required test catalogue;

exact focused/full collection/pass totals;

check-report totals;

mandatory completion-report content;

detailed Telegram handoff evidence;

completion automation idempotency.

Therefore:

v0.3 reference validation = successful experiment
v0.3 promotion             = HOLD
v0.4                       = required

Historical v0.3 evidence remains immutable.

5. Non-negotiable governance invariants

Blueprint owns roadmap truth, prompt queue truth, prompt contracts, completion discovery/intake, review records, ACCEPT/RETURN/HOLD, roadmap effects, next-prompt activation and global coordination health.

Modules own implementation, tests, module-local completion packet/report, module-local outbox event and module-local status/evidence.

Modules MUST NOT write Blueprint repositories.

Blueprint MUST NOT mutate module implementation repositories during intake/review.

Historical published artifacts are immutable.

No automatic commit/push.

No live/production/external writes or calls without explicit authorization.

ACCEPT remains an explicit operator decision. Machine validation may be automatic.

Capacity/horizon warnings do not block ordinary work unless separately promoted to hard policy.

tmp/ is ignored diagnostic/build staging only.

6. Existing standards v0.4 must preserve

Existing roadmap policy already expects a long future horizon and allows fewer than eight future steps only as an explicit uncertainty/discovery exception.

Existing prompt queue policy already says:

structured queue index is source of truth;

drafts are non-executable;

a draft never becomes executable merely because it exists;

Blueprint explicitly promotes work;

sequence is the main navigation order;

priority can influence selection;

modules pull only their own active prompt.

Existing completion/reporting protocol already separates module completion from Blueprint intake/review/queue/roadmap mutation.

v0.4 must unify these rules instead of creating parallel semantics.

7. Roadmap health policy

Use configurable policy, not hardcoded Python constants:

roadmap:
  hard_floor_future_steps: 5
  target_future_steps: 8
  under_target_behavior: advisory
  under_floor_behavior: warning

prompt_buffer:
  minimum_dispatchable_drafts: 2
  target_dispatchable_drafts: 3
  under_minimum_behavior: warning

active_prompt:
  desired_for_active_module: 1
  maximum: 1
  missing_behavior: warning
  multiple_behavior: error

Interpretation:

future >= 8  → target healthy
future 5..7  → advisory replenish
future < 5   → warning

dispatchable drafts >= 2 → healthy minimum
dispatchable drafts < 2  → warning

active = 0 → warning for active-development module
active = 1 → healthy
active > 1 → integrity error unless explicit policy says otherwise

8. Roadmap semantics

Roadmap is not a single cursor.

Support semantic states such as:

planned
ready
active
blocked
completed
superseded
deferred

Each step should have stable step_id, sequence, priority, dependencies, prompt references, evidence, status and block/defer/supersede reason.

Out-of-order completion is allowed. A prompt may close steps 10, 11 and 12 while step 6 remains planned if dependency rules allow it.

Do not use current_step++. Resolve work from eligible incomplete dependency-aware steps.

9. Roadmap ↔ Prompt binding

Every v0.4 prompt contract must declare roadmap scope:

roadmap_scope:
  - step_id: ...
    expected_effect: complete

Completion packet reports claimed effects:

roadmap_results:
  - step_id: ...
    claimed_result: completed
    evidence_ids: [...]

The module never mutates Blueprint roadmap state. Blueprint applies verified roadmap effects only after explicit ACCEPT.

10. Prompt queue model

Canonical state is the structured index, not the folder name.

Recommended queue fields:

prompt_id: ...
state: draft | prepared | released | in_progress | completed_in_module | pending_review | accepted | returned | held
created_at: ...
sequence: ...
queue_rank: ...
priority: ...
dispatch_ready: true|false
roadmap_refs: [...]
dependencies: [...]
file: ...

Default selection:

explicit operator override;

dependency eligibility;

queue rank / sequence;

priority;

created_at tie-breaker.

Do not rename historical files just to change order.

11. Dispatchable drafts

A file in drafts/ is not automatically usable work.

A draft counts toward the buffer only when:

valid prompt_id
+ draft state
+ file exists
+ roadmap refs exist
+ dependency state known
+ no unresolved blocking prerequisite
+ metadata valid
+ queue ordering metadata valid

Health tooling should display both physical draft files and dispatchable drafts.

12. Immutable Prompt Contract v0.4

v0.3 uses a mutable semantic address:

coordination/prompt_contracts/<module>/<prompt_id>.yaml

v0.4 should use immutable contract instances:

coordination/prompt_contracts/<module>/<prompt_id>/<contract_id>.yaml

Packet reference:

prompt_contract:
  contract_id: ...
  path: ...
  schema_version: module_prompt_contract_v0_4
  sha256: ...
  source_prompt_sha256: ...

Historical packets must always resolve the exact contract bytes they originally referenced.

13. Source prompt fidelity ledger

v0.4 must explicitly map source-prompt obligations.

Example:

source_obligations:
  - obligation_id: OBL-001
    kind: implementation
    source:
      heading: ...
      start_line: ...
      end_line: ...
    required: true
    maps_to:
      requirements:
        - REQ-001

Also support verification and completion-evidence obligations.

Validator must reject duplicate IDs, unknown targets and required obligations with no mapping.

14. Verification obligations

Generic test_paths are not enough.

Use explicit verification obligations:

verification_obligations:
  - id: TEST-001
    statement: ...
    test_paths: [...]
    selectors: [...]
    maps_from_source_obligations: [...]

Required command results remain separate from test obligations.

15. Structured verification totals

Packet v0.4 must separately record:

verification_summary:
  focused_tests:
    collected: ...
    passed: ...
    failed: 0
    skipped: ...
  full_tests:
    collected: ...
    passed: ...
    failed: 0
    skipped: ...
  check_report:
    total: ...
    passed: ...
    failed: 0
    warnings: ...

Never infer test totals from check-report totals.

16. Completion obligations

Prompt-required completion/report content must receive IDs.

Typical obligations:

taxonomy summary;

lifecycle summary;

handoff path/examples;

idempotency rules;

focused/full totals;

check-report totals;

safety confirmations;

completion automation idempotency.

Packet must answer each required completion obligation exactly once.

17. Completion Outbox

Do NOT create a shared repository every module writes into.

Use module-owned immutable records:

coordination/completion_outbox/records/<event_id>.yaml

Example fields:

schema_version: module_completion_outbox_event_v0_1
event_id: ...
module_id: ...
prompt_id: ...
packet_path: ...
report_path: ...
branch: ...
declared_publication_state: pending_operator_publication

Do not encode a self-referential final commit hash.

18. Blueprint completion discovery

Blueprint scans registered module outboxes read-only.

Suggested states:

unseen
discovered
publication_unverified
ready_for_intake
intake_failed
ready_for_operator_review
accepted
returned
held
superseded

Discovery is idempotent. Re-scanning the same event+publication must not duplicate review work.

19. Global coordination pulse

Create:

make coordination-pulse

It should show every registered module plus Blueprint:

Module          Active  Drafts  Dispatchable  Roadmap Ahead  New Completion  Health
------------------------------------------------------------------------------------
...

Stable warning/error codes should include:

ROADMAP_HORIZON_BELOW_TARGET
ROADMAP_HORIZON_LOW
PROMPT_BUFFER_LOW
ACTIVE_PROMPT_MISSING
MULTIPLE_ACTIVE_PROMPTS
COMPLETION_PENDING_REVIEW
QUEUE_ROADMAP_DRIFT
ROADMAP_PROMPT_REFERENCE_MISSING

Capacity warnings are non-blocking. Integrity failures may block mutation.

20. Refresh versus local pulse

Do not network-fetch all modules during every normal check.

Separate:

coordination-pulse
  → local registered refs

coordination-refresh
  → fetch/read remote state

coordination-pulse --refresh
  → optional composition

Core governance must work without GitHub.

21. Operator review workflow

Target command shape:

make completion-review MODULE=<module> COMPLETION_ID=<id>

Machine validation covers schema, prompt/contract identity, source obligations, implementation, verification, totals, checks, completion obligations, safety, publication, roadmap effects and superseding chain.

Machine result:

READY_FOR_OPERATOR_REVIEW

Operator choices:

[A] Accept + default next prompt
[B] Accept + choose another eligible prompt
[C] Accept + do not activate next prompt
[R] Return
[H] Hold

CLI flags may be used before interactive TTY UX exists.

22. Acceptance transaction

After explicit ACCEPT, Blueprint performs one bounded transaction:

review record
→ prompt accepted
→ verified roadmap results applied
→ dependencies recomputed
→ roadmap horizon recomputed
→ prompt buffer recomputed
→ next candidate selected
→ optional activation
→ final coordination pulse

If the transaction fails before commit, restore all Blueprint paths. Never leave half-updated roadmap/queue state.

No automatic Git commit.

23. Prompt activation

Activation is Blueprint-owned.

A draft becomes executable only after an explicit Blueprint activation transaction.

The module later pulls/reads its own active prompt using approved module workflow. Blueprint does not normally write prompts directly into module repos.

24. Blueprint self-coordination

Blueprint must participate in the same health model.

Current canonical self paths:

coordination/self_coordination/roadmap.yaml
coordination/self_coordination/prompt_queue/index.yaml

Other modules use:

coordination/roadmaps/<module_id>.yaml
coordination/outgoing_prompts/<module_id>/index.yaml

v0.4 must introduce a source registry so tools do not hardcode a single path convention.

25. Coordination source registry

Create one Blueprint-owned registry describing per module:

module_id: ...
active_development: true|false
roadmap:
  path: ...
prompt_queue:
  index: ...
  drafts_dir: ...
  approved_dir: ...
module_source:
  local_path: ...
  remote: origin
  branch: ...
completion_outbox:
  records_dir: ...

This registry drives pulse, discovery, roadmap health, prompt buffer health and module lookup.

26. Soft health vs hard integrity

Soft:

roadmap below target;

fewer than two dispatchable drafts;

no active prompt for active module;

completion waiting for review.

Hard:

multiple active prompts under WIP=1;

queue points to missing file;

roadmap current step invalid;

prompt references unknown roadmap step;

contract/source hash mismatch;

conflicting outbox identity;

unauthorized cross-repository mutation.

27. Publication semantics

Preserve the v0.3 fix:

packet/outbox may say pending_operator_publication

Blueprint derives publication_verified=true only from Git commit existence + evidence in commit + remote branch containment.

Never require a packet to recursively claim its own final publication commit.

28. Revision strategy

Create:

module_prompt_contract_v0_4
module_completion_packet_v0_4
blueprint_completion_intake_v0_4

v0.2 remains operational until separate promotion.
v0.3 remains historical/reference evidence.
v0.4 starts as candidate/reference validation with normal acceptance forbidden.

29. Implementation slices

Baseline / lifecycle audit.

Closed-loop lifecycle standard.

Coordination source registry.

Coordination health policy + coordination-pulse.

Immutable Prompt Contract v0.4.

Completion Packet v0.4.

Completion Outbox.

Discovery + v0.4 intake.

Review / roadmap / queue transaction.

Next-prompt selection and activation.

Tracking Events v0.4 reference migration.

Manual dark-zone audit.

Separate promotion decision.

30. Minimum tests

Contract:

immutable path/hash;

source SHA;

historical contract resolution.

Fidelity:

missing required source mapping fails;

unknown mapping target fails.

Roadmap:

missing roadmap warns;

invalid current step fails;

horizon warnings;

out-of-order completion allowed;

blocked step not dispatchable.

Prompt queue:

active 0 warns;

active 1 passes;

active >1 fails;

buffer <2 warns;

invalid draft does not count;

ordering deterministic.

Discovery:

idempotent repeated scan;

conflicting event identity fails;

unpublished commit not ready;

remote containment verifies publication.

Review transaction:

ACCEPT applies verified roadmap effects;

RETURN does not close roadmap;

HOLD preserves state;

next prompt must be eligible;

failure rolls back exact Blueprint paths.

Boundaries:

no module repo write;

real Git index unchanged;

no auto commit/push/accept.

31. Bootstrap procedure for a new assistant

Always start read-only:

cd /srv/software_development/forprint-project/forprint_system_blueprint

git status --short
git branch --show-current
git rev-parse HEAD

make roadmap-validate MODULE=forprint_system_blueprint
make roadmap-dashboard MODULE=forprint_system_blueprint BEFORE_CURRENT=8 AFTER_CURRENT=15

cat coordination/self_coordination/roadmap.yaml
cat coordination/self_coordination/prompt_queue/index.yaml

make completion-revision-status
make completion-revision-check

Then inventory:

find coordination/roadmaps -maxdepth 1 -type f -print | sort
find coordination/outgoing_prompts -maxdepth 3 -type f   \( -name '*.yaml' -o -name '*.md' \) -print | sort

Do not mutate until current Git state, self roadmap, prompt queue and exact slice are known.

32. Continuation-state record

At the end of each bounded slice record:

slice_id: ...
blueprint_head_before: ...
blueprint_head_after: ...
changed_paths: [...]
tests_run: [...]
result: ...
next_slice: ...
operator_decision_required: true|false
module_repositories_modified: false
automatic_commit: false
automatic_acceptance: false

33. Immediate task

Complete Slice 0 before schema mutation:

CURRENT SELF ROADMAP
+
ALL MODULE ROADMAP INVENTORY
+
PROMPT QUEUE / DRAFT BUFFER INVENTORY
+
COMPLETION DISCOVERY SURFACE INVENTORY
=
V0.4 CLOSED-LOOP BASELINE

Then reconcile the Blueprint self roadmap so the v0.4 workstream itself is present with a healthy future horizon.

34. Definition of done

v0.4 is ready for promotion consideration only when:

roadmap/prompt/completion are one lifecycle;

all active modules + Blueprint appear in coordination-pulse;

roadmap and draft-buffer health are machine-readable;

prompt activation remains explicit;

prompt contracts are immutable;

source prompt obligations are mapped;

verification obligations and totals are explicit;

completion obligations are explicit;

module outbox exists;

discovery is idempotent;

Git publication is externally verified;

operator review is explicit;

roadmap effects are transactional;

next prompt selection is deterministic and overrideable;

historical v0.2/v0.3 evidence is immutable;

Tracking Events v0.4 reference passes;

manual semantic audit finds no uncovered mandatory source obligation;

promotion is separately operator-authorized.

35. Core principle

predictable enough to automate,
explicit enough to audit,
simple enough to recover,
human-controlled at the decision boundary.

Automate discovery, verification, synchronization, health and transaction preparation.
Keep governance decisions explicit.

---

# v0.4 Addendum — Prompt File Completion Transition

The executable prompt queue must not accumulate accepted work in `approved/`.

Canonical physical transition:

```text
draft/
  -> approved/ only by explicit Blueprint activation
  -> completed/ only after explicit operator ACCEPT
```

Rules:

- module completion or `READY_FOR_OPERATOR_REVIEW` does not move a prompt to `completed/`;
- ACCEPT moves the prompt file from `approved/` to `completed/` as part of the same bounded Blueprint transaction;
- the queue record must change to completed/accepted state and point to the completed file path;
- RETURN and HOLD must not archive the prompt as completed;
- accepted prompts remaining in `approved/` are an integrity defect;
- completion transition must be idempotent and rollback-safe;
- no automatic Git commit or push is implied.
