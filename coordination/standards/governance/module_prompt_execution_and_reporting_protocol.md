# Module Prompt Execution and Reporting Protocol

Status: active cross-repository boundary standard
Created/updated: `2026-07-14`; completion exchange revision notice updated `2026-08-12`

> Current release notice: `coordination/releases/current.yaml` is the effective current coordination authority. `coordination/revisions/current.yaml` now points at promoted v0.4. The old v0.2/v0.3 transition is a non-blocking compatibility lane registered in `coordination/legacy/compatibility_registry_v0_1.yaml`.

## Purpose

This protocol defines the global prompt execution and reporting workflow for all ForPrint module assistants.

It connects the existing Blueprint prompt queue, module-side prompt reading, module-side completion reporting, completion packet automation and Blueprint-side review flow into one end-to-end protocol.

This is a global protocol. It is not specific to Library, Telegram Bot, Website, Calculator Engine, Operations Control Registry or any other single module.

## Scope

This protocol applies to every ForPrint module that receives work from ForPrint System Blueprint, including but not limited to:

- `forprint_library`
- `telegram_bot`
- `website`
- `calculator_engine`
- `forprint_operations_control_registry`
- `forprint_integration_gateway`
- `forprint_accounting_registry_service`
- `forprint_prepress_hub`
- future channel assistants and services

## Core rule

A module may read Blueprint prompts, standards, dashboards and context bundles.

A module must write only inside its own repository.

A module assistant must not directly create, update, copy or commit files inside the Blueprint repository unless the current working repository is explicitly `forprint_system_blueprint` and the active task is a Blueprint task.

Blueprint-side completion intake, review records, acceptance metadata and prompt queue updates are created only from the Blueprint context.

## Repository ownership boundary

### Module repository

A module repository owns its own implementation and coordination records.

A module may update:

```text
coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/status/next_questions_for_blueprint.md
coordination/reports/index.yaml
coordination/reports/completion/*.md
coordination/prompts/index.yaml
module source code
module tests
module docs
module local tooling

```

A module may not update:

```text
/srv/software_development/forprint-project/forprint_system_blueprint/...
```

from a module-side task.

### Blueprint repository

Blueprint owns:

```text
coordination/outgoing_prompts/<module_id>/
coordination/outgoing_prompts/<module_id>/index.yaml
coordination/review_packets/<module_id>/processed/
coordination/roadmaps/
coordination/standards/
coordination/templates/
Blueprint review metadata
Blueprint acceptance metadata
Blueprint prompt queue state
```

Module completion reports and Completion Outbox records remain module-owned evidence.
Blueprint reads them from the registered module repository in read-only mode, validates
them during completion intake, and materializes only Blueprint-owned review/queue/roadmap
evidence.

## End-to-end workflow

The normal prompt execution loop is:

Blueprint creates or updates an outgoing prompt for a module.
Blueprint registers the prompt in coordination/outgoing_prompts/<module_id>/index.yaml.
The module pulls or reads Blueprint state using approved Make targets.
The module resolves the next active prompt from the prompt queue.
The module executes the prompt only in its own repository.
The module creates or updates its module-side completion artifacts.
The module updates its own coordination records.
The module runs validation, tests and governance checks.
The module commits and pushes its own repository.
Blueprint reads the module-side report.
Blueprint validates module-owned completion evidence and may create a Blueprint-owned review packet.
Blueprint reviews the result.
Blueprint updates prompt queue execution and review metadata.
Blueprint commits and pushes its own repository.
## Prompt reading

Modules should use queue-based prompt navigation.

Preferred targets:

make prompt-notify
make prompt-dashboard
make prompt-next
make prompt-read-next

A module must read only its own prompt queue:

coordination/outgoing_prompts/<module_id>/index.yaml

A module must not self-assign work from another module queue.

A module must not execute draft prompts.

Draft prompts may be read for awareness only. They become executable only after Blueprint promotes them into the active prompt queue.

## Module-side execution

After reading a prompt, the module assistant should:

check the working tree;
confirm the prompt target module matches the current module;
review applicable standards;
implement only the prompt scope;
keep unrelated changes out of the checkpoint;
avoid live external integrations unless explicitly approved;
avoid production writes unless explicitly approved;
update tests and documentation as required;
prepare module-side completion reporting.
## Completion reporting automation

Manual editing of several coordination files is not the preferred workflow.

When completion packet automation is available, a module assistant should use it instead of manually synchronizing duplicated metadata across multiple files.

Preferred workflow:

completion packet
completion-packet-validate
completion-packet-apply
completion-packet-check
git diff review
module validation
commit/push

The completion packet workflow should update or generate:

coordination/reports/completion/<report>.md
coordination/reports/index.yaml
coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/status/next_questions_for_blueprint.md

The assistant should review the generated diff before committing.

## Completion automation boundary

Module-side completion automation may write only inside the module repository.

Completion scripts must not write into the Blueprint repository.

Completion scripts that accept paths must validate that generated or modified paths stay under the module root.

Completion scripts may include Blueprint prompt paths as read-only metadata, but must not modify those Blueprint files.

A module-side completion script must not perform Blueprint-side intake, Blueprint review, prompt queue acceptance or Blueprint metadata commits.

## Deferred automation

A module may temporarily expose deferred-safe completion targets when full completion packet automation is not yet configured.

Deferred-safe behavior is allowed only if it is explicit and does not fake successful automation.

Acceptable deferred-safe behavior:

print that completion packet automation is not configured;
make no file changes;
return success only for compatibility if the module checkpoint does not require packet application;
document the deferral in the completion report or status.

Deferred-safe targets should later be replaced with real packet validation and application.

## Manual fallback

Manual completion reporting is allowed only as a fallback when completion automation is not yet available or when Blueprint explicitly requests a manual transition checkpoint.

When manual fallback is used, the assistant must still keep module-side ownership boundaries:

write module report in module repo;
update module status in module repo;
update module reports index in module repo;
do not write into Blueprint repo.

Manual fallback should not become the normal workflow for active modules.

## Blueprint-side completion intake and review evidence

Blueprint does not require a second current copy of a module-owned completion report.

The current cross-repository flow is:

```text
module-owned completion report / Completion Outbox
-> Blueprint read-only discovery
-> completion intake validation
-> explicit Blueprint decision
-> coordination/review_packets/<module_id>/processed/
-> prompt queue and roadmap evidence update
```

`coordination/review_packets/<module_id>/processed/` is the durable Blueprint-owned
review-evidence surface. The module-side report path remains provenance pointing back to
the module repository.

A module assistant must not create or update Blueprint review packets, Blueprint prompt
queues, or Blueprint roadmap acceptance evidence from a module-side task.

## Blueprint review

Blueprint review should update the prompt queue record separately for:

module_execution.status
module_execution.completion_commit
module_execution.completion_report
blueprint_review.status
blueprint_review.acceptance_commit
blueprint_review.review_notes

Module completion is not the same as Blueprint acceptance.

A prompt can be completed by the module while still pending Blueprint review.

## Make target expectations

Active modules should gradually support:

make module-start
make module-sync
make module-validate
make module-finish

make prompt-dashboard
make prompt-next
make prompt-read-next

make completion-packet-validate
make completion-packet-apply
make completion-packet-check

make coordination-check
make governance-check
make check
make check-report

module-finish should run validation and completion reporting checks, but must not perform Blueprint-side review or Blueprint-side intake.

## Forbidden patterns

Module assistants must not:

copy files into forprint_system_blueprint from module context;
edit Blueprint prompt queues from module context;
mark their own Blueprint review as accepted;
commit Blueprint metadata from a module repository;
treat draft prompts as executable work;
treat module completion as Blueprint acceptance;
manually maintain duplicated completion metadata when automation exists;
write generated reports outside the module root.
## Allowed patterns

Module assistants may:

read Blueprint outgoing prompts;
read Blueprint standards;
read Blueprint dashboards;
read context bundles;
write module-local reports;
write module-local current status;
write module-local next questions for Blueprint;
commit and push module-local changes;
ask Blueprint to review completion output.

Blueprint assistants may:

read module-owned completion reports and Completion Outbox records in read-only mode;
create Blueprint-owned review packets after explicit review decisions;
update Blueprint prompt queues;
record Blueprint review status;
update Blueprint roadmap evidence;
issue the next prompt;
commit and push Blueprint-side metadata.

## Relationship to other standards

This protocol connects and clarifies:

coordination/standards/module_outgoing_prompt_pull_protocol.md
coordination/standards/module_prompt_completion_protocol.md
coordination/standards/module_coordination_records_protocol.md
coordination/standards/governance/prompt_queue_navigation_policy.md
coordination/standards/make_command_standard.md
coordination/templates/module_makefile_standard.template.mk

If these documents conflict, this protocol controls the cross-repository write boundary and the end-to-end execution/reporting loop.

<!-- blueprint-completion-finalization-v0-1:start -->

## Blueprint completion intake and finalization

Module-side completion and Blueprint-side acceptance are separate operations.

The module finishes its own work first:

```text
module implementation
-> module checks
-> completion packet
-> module completion report
-> module commit and push
```

Blueprint then performs an independent finalization flow:

```text
completion intake preview
-> evidence validation
-> Blueprint decision
-> review packet
-> prompt queue update
-> roadmap evidence update
-> documented next-work suggestion
```

### Blueprint intake commands

Preferred Blueprint commands:

```text
make completion-intake-preview MODULE=<module> MODULE_ROOT=<path> PACKET=<module-relative-packet>
make completion-accept MODULE=<module> MODULE_ROOT=<path> PACKET=<module-relative-packet>
make completion-return MODULE=<module> MODULE_ROOT=<path> PACKET=<module-relative-packet> REVIEW_NOTES="..."
make completion-finalize-check MODULE=<module>
```

`completion-intake-preview` must not write files.

`completion-accept` and `completion-return` require an explicit operator decision and write only inside the Blueprint repository.

### Completion evidence validation

Blueprint intake must verify, where available:

```text
module id;
prompt id;
completion report path;
implementation commit;
completion commit;
remote containment of completion commit;
push status;
required successful checks;
boundary confirmations;
prompt queue record;
roadmap step.
```

Legacy v0.1/v0.2 evidence may be recognized for transition diagnostics, but old boundary forms are not a second current interface.

New v0.3 evidence uses explicit positive `no_*: true` safety confirmations and machine-readable prompt/check coverage. Unsafe or ambiguous boundary values always block intake.

### Review packet

Every written Blueprint decision creates or updates a deterministic review packet under:

```text
coordination/review_packets/<module_id>/processed/
```

The review packet is the stable Blueprint evidence record.

The existing `blueprint_review.acceptance_commit` field may remain `null`. A Git commit cannot safely contain its own final hash. Git history identifies the commit that introduced the review packet and queue/roadmap update.

### Idempotency

Repeating the same intake command with the same:

```text
packet;
completion commit;
decision;
review date;
review notes
```

must produce no additional diff.

The tool must not duplicate prompt queue records, roadmap evidence or review packets.

## Next-work recommendation hierarchy

Blueprint automation must not invent the content of a new prompt.

The documented source hierarchy is:

```text
1. current approved prompt that is ready or in progress;
2. draft prompt matching the next roadmap step;
3. next non-completed roadmap step;
4. explicit NEXT_WORK_UNDEFINED warning.
```

Preferred command:

```text
make next-work-suggestion MODULE=<module_id>
```

### Active approved prompt

When an approved prompt has execution status `ready_for_module_pull` or `in_progress`, the result is:

```text
ACTIVE_PROMPT_EXISTS
```

The module should continue or pull that prompt. Draft and roadmap recommendations remain secondary.

### Matching draft candidate

When no approved prompt is active and exactly one draft matches the next roadmap step, the result is:

```text
DRAFT_CANDIDATE_FOUND
```

The system proposes the draft for human review. It does not promote or activate the draft automatically.

Multiple matching drafts produce:

```text
MULTIPLE_DRAFT_CANDIDATES
```

Drafts that do not match the next roadmap step produce:

```text
DRAFT_ROADMAP_CONFLICT
```

### Roadmap fallback

When no active approved prompt and no matching draft exist, but the roadmap contains a next step, the result is:

```text
ROADMAP_PROMPT_NEEDED
```

The suggestion must show only documented roadmap fields such as:

```text
sequence;
step_id;
title;
status;
priority;
summary;
expected_outputs;
dependencies.
```

This is a prompt-authoring hint, not generated business scope.

### Undefined next work

When neither draft nor roadmap defines the next work, the result is:

```text
NEXT_WORK_UNDEFINED
```

Blueprint must update the roadmap before issuing another prompt.

### Promotion boundary

Draft promotion and approved prompt activation are explicit future write operations.

A draft must never become executable merely because it exists in `drafts/`.

Before promotion, Blueprint must verify:

```text
target module;
prompt id uniqueness;
roadmap step match;
sequence;
dependencies;
scope;
outgoing prompt validation.
```

<!-- blueprint-completion-finalization-v0-1:end -->

## Compact tabular final handoff

Routine module completion handoffs should use one or more compact boxed tables when terminal table rendering is available.

Recommended concern groups include:

```text
implementation result;
tests and validation;
boundaries and safety;
coordination lifecycle;
warnings, blockers and decisions;
artifact and commit paths.
```

The number of tables and rows is determined by readability and risk, not by a rigid universal line limit.

For a normal module, output near or below 100 lines is a useful guideline. Larger architectures may require more rows. When a failure needs deep investigation, extended diagnostics may be unlimited and should be stored in a file with a stable path.

Modules must use the applicable visual-interface standards referenced by:

```text
coordination/standards/visual_interface/index.yaml
```

Color is supplementary. Status text, counts and markers must remain understandable in plain text.

## Documentation and recovery gate

Meaningful coordination and automation changes must follow:

```text
coordination/standards/governance/documentation_and_recovery_gate.md
```

Important workflow decisions must not remain only in chat history.

The repository must preserve enough architecture, operations, recovery, test and completion evidence for another assistant to resume safely after context loss or assistant replacement.


## Module-owned prompt execution events — v0.4.1 hardening

This section adds an observational execution-event channel without creating a
second Prompt Queue state machine.

The module owns append-only records under:

```text
coordination/prompt_execution_events/records/
```

Blueprint reads those records from the module repository in read-only mode.
Modules still MUST NOT write the Blueprint repository. Blueprint does not
automatically materialize an event into the Blueprint-owned Prompt Queue.

The event schema is `module_prompt_execution_event_v0_1`. The supported event
types and observed execution states are:

```text
CLAIMED            -> claimed
IN_PROGRESS        -> in_progress
BLOCKED            -> blocked
UNABLE_TO_EXECUTE  -> unable_to_execute
```

`CLAIMED` is the explicit module acknowledgement that the module received and
took responsibility for the current Blueprint prompt. It is distinct from
`IN_PROGRESS`.

The first event for a prompt MUST be `CLAIMED`. Valid subsequent transitions
are deliberately small:

```text
CLAIMED           -> IN_PROGRESS | BLOCKED | UNABLE_TO_EXECUTE
IN_PROGRESS       -> IN_PROGRESS | BLOCKED | UNABLE_TO_EXECUTE
BLOCKED           -> BLOCKED | IN_PROGRESS | UNABLE_TO_EXECUTE
UNABLE_TO_EXECUTE -> UNABLE_TO_EXECUTE | IN_PROGRESS
```

`BLOCKED` and `UNABLE_TO_EXECUTE` require a stable reason code and explanatory
reason. Neither state means Blueprint RETURN or HOLD. They are module execution
observations only.

There is intentionally no `COMPLETED`, `ACCEPTED`, `RETURNED`, or `HELD`
execution event. Module completion continues through the Completion Packet /
Completion Outbox channel. ACCEPT / RETURN / HOLD remain explicit Blueprint
operator-review decisions.

Blueprint discovery validates every event against the registered local module
repository and the Blueprint-owned Prompt Queue record for the same
`module_id`/`prompt_id`. Missing event directories mean `not_present_yet`; they
must not be fabricated.

Discovery is local, network-independent, and read-only. Its projection reports
both the persisted queue status and the latest observed module status. It does
not mutate roadmap, queue, prompt files, module repositories, or review state.

One module should have at most one current execution observation at a time.
Multiple current prompt observations for one module are an attention condition
and must not trigger automatic selection, activation, ACCEPT, RETURN, or HOLD.

H3 defines the event contract, validation and Blueprint read-only discovery.
Module-side producer/sync/notification commands are a later coordination-sync
hardening slice and are not implied by this section.

### H3 stream integrity and built-in observability

Execution-event `sequence` is per prompt, starts at `1`, and MUST be contiguous.
`occurred_at` MUST NOT move backwards as sequence increases; equal timestamps are
allowed because sequence is the deterministic tie-breaker.

Only `ready_for_module_pull`, `in_progress`, and `blocked` queue states are
directly compatible with a current H3 observation. `completed_by_module` and
`superseded` make the stream historical. Other states such as
`returned_for_fix` and legacy `paused` require explicit review and MUST NOT
silently reactivate a stale event.

Unknown module filters fail closed. H3 registry entries must preserve
`blueprint_lookup_mode: read_only` and `blueprint_may_write_repository: false`.

Normal Blueprint observability consumes H3 read-only projections: prompt
dashboards surface observed module state and the coordination pulse reports
execution events plus attention codes. The deterministic Blueprint check path
runs the pulse. No queue mutation, module writes, network access, automatic
ACCEPT/RETURN/HOLD, selection, activation, commit, or push is implied.

### H3 local checkout coverage semantics

The deterministic Blueprint check is network-independent and may run in a
checkout where some registered module repositories are not locally present.
`repository_not_present` and `not_present_yet` are therefore observability
coverage states, not governance source errors by themselves. They remain
visible in discovery summaries but do not add
`PROMPT_EXECUTION_SOURCE_UNAVAILABLE`.

Structural failures remain attention conditions: an invalid registry boundary,
unknown requested module, malformed event source, invalid event, transition
violation, incompatible queue state, or WIP=1 violation still fails closed.
Network/sync readiness belongs to the separate coordination-sync hardening
slice rather than the deterministic local H3 check.

### H3 Blueprint self-module applicability boundary

`forprint_system_blueprint` is not an external H3 module execution-event source.
Its repository is Blueprint-owned, so the registry legitimately permits
Blueprint writes there. Applying the external-module
`blueprint_may_write_repository: false` invariant to the self module would be a
category error.

H3 discovery therefore reports the Blueprint self module as
`self_module_not_applicable` and does not scan it for
`module_prompt_execution_event_v0_1` records. Blueprint self work continues to
use the dedicated self-coordination roadmap / prompt queue / completion
lifecycle. This exception is identity-specific to `forprint_system_blueprint`;
it does not relax read-only boundaries for any external module.

<!-- forprint-execution-workspace-compatibility-v0-1 -->
## Execution workspace compatibility, cleanliness, and isolation

### Normative distinction

Global worktree cleanliness is not the same thing as execution compatibility.

The coordination layer must distinguish at least these concepts:

- **repository freshness** — whether repository `HEAD` advanced relative to a release or prompt baseline;
- **global worktree cleanliness** — whether any tracked or untracked path in a checkout differs from `HEAD`;
- **required-input compatibility** — whether the prompt contract, release authority, queue binding, required material inputs, and other declared execution inputs still match the execution contract;
- **execution-lane cleanliness** — whether the workspace in which a module is about to claim a prompt contains pre-existing changes that cannot be attributed to that execution;
- **material drift** — a change to a declared required input or authority that can change the meaning or safety of the execution.

These concepts MUST NOT be collapsed into one boolean `clean/dirty` decision.

### Blueprint / coordination repository rule

The Blueprint coordination repository MAY contain unrelated local development work while a prompt is selected, validated, claimed, executed, reviewed, or completed.

A globally dirty Blueprint checkout is therefore **not, by itself, an execution blocker**.

Blueprint execution preflight must evaluate the declared authority and required-input surface. Unrelated dirty paths are tolerated when they do not alter:

- the active release authority relevant to the execution;
- the selected prompt / prompt contract;
- queue or registry bindings required by the execution;
- declared material required inputs;
- validator/tooling inputs explicitly included in the execution contract.

If one of those execution inputs changes, the system must classify the change through the normal B1 compatibility / revalidation / material-drift rules. It must not hide the change merely because other unrelated work is present.

The intended rule is:

```text
unrelated Blueprint dirt
    != execution incompatibility

required-input / authority drift
    => revalidate or block according to the execution contract
```

This permits normal Blueprint development to continue while already released or queued work remains executable from its immutable contract surface.

### Module shared execution-lane rule before CLAIM

A module's **shared execution workspace** is stricter than the Blueprint coordination workspace.

Before `CLAIMED`, the workspace used to execute a prompt must have a known, attributable state. Under the current shared-lane model, pre-existing module worktree changes are a blocker (`BLOCKED_MODULE_DIRTY`) because the system cannot safely prove whether those bytes belong to the new prompt, another prompt, or manual work.

Therefore a prompt waiting for a busy shared module lane remains queued. It does not force-reset, auto-stash, discard, absorb, or reinterpret existing changes.

This is a WIP / execution-lane safety rule, not a requirement that the whole ForPrint ecosystem be idle.

### Module state after CLAIM

Once a prompt is claimed, changes created by that execution are expected. The execution workspace may become dirty and its `HEAD` may advance through implementation commits.

The execution identity remains bound to the accepted preflight fingerprint and execution epoch. The implementation must not "chase" a newer `HEAD` by silently redefining its execution baseline.

In short:

```text
before CLAIM:
    shared execution lane must be attributable / clean

after CLAIM:
    prompt-owned changes are expected
    execution epoch remains stable
```

### Parallel work in one module

Parallel execution of multiple prompts in the same module must not be implemented by allowing multiple agents to write concurrently into one dirty shared checkout.

If true parallel module execution is enabled in the future, each active execution must receive an **isolated execution workspace** (for example a Git worktree or equivalent checkout) bound to its own:

- prompt ID and contract;
- baseline commit / branch policy;
- preflight evidence;
- execution fingerprint / epoch;
- mutation surface;
- completion provenance.

Parallelism is therefore achieved by **workspace isolation**, not by weakening ownership of a shared dirty tree.

Until isolated execution-lane tooling is explicitly activated, WIP=1 per shared module execution lane remains the safe default.

### Sender / receiver independence

A prompt or cross-module task is transferred through immutable coordination artifacts and declared required inputs, not through an assumption that the sender's live checkout will remain frozen.

After publication, the sending repository may continue unrelated development. The receiving execution remains valid while its contract and required inputs remain compatible.

The same rule applies to Blueprint-to-module and future module-to-module work:

```text
sender freshness != task compatibility
```

### Bounded Blueprint mutations while unrelated work exists

Execution compatibility policy does not automatically authorize every mutation tool to operate on a dirty worktree.

A bounded mutation may safely coexist with unrelated Blueprint work only when the mutation mechanism proves all of the following:

1. its declared target paths were unmodified before the transaction;
2. unrelated dirty paths are captured and preserved;
3. only declared target paths are written;
4. only declared target paths are staged / committed;
5. validation covers new and tracked files in the declared scope;
6. unrelated worktree state remains unchanged after success or rollback.

A mutation builder that has not yet implemented these protections MAY retain a stricter clean-worktree precondition. That local tooling restriction MUST NOT be generalized into an ecosystem execution-compatibility rule.

### Decision matrix

| Situation | Result |
| --- | --- |
| Blueprint has unrelated dirty files | Allowed; evaluate declared required inputs |
| Blueprint required input changed | Revalidate or block according to B1 classification |
| Blueprint `HEAD` advanced, required inputs unchanged | Exact/forward-compatible/revalidated path; no historical checkout solely for freshness |
| Shared module execution lane dirty before CLAIM | Block / keep prompt queued |
| Shared module lane clean and compatible before CLAIM | CLAIM may proceed |
| Claimed execution creates dirty files or commits | Expected; preserve execution epoch |
| Second prompt targets a busy shared module lane | Queue it; do not merge execution ownership |
| Multiple prompts must execute concurrently in one module | Require isolated execution workspaces |
| Sender repository changes after task publication | Not a blocker unless declared task inputs drift |
| Bounded Blueprint mutation amid unrelated dirt | Allowed only with explicit scope-preservation tooling |

### Forbidden shortcuts

The following are forbidden as substitutes for the policy above:

- broad `git reset --hard` to manufacture cleanliness;
- broad `git clean` to remove unrelated work;
- automatic stash/pop of operator work as an execution precondition;
- accepting all dirty module bytes as belonging to the next prompt;
- silently rebasing an execution epoch onto a newer `HEAD`;
- letting two autonomous executions mutate one shared dirty module checkout.

The system must preserve operator work and reason about compatibility from declared authority, inputs, and execution ownership.
