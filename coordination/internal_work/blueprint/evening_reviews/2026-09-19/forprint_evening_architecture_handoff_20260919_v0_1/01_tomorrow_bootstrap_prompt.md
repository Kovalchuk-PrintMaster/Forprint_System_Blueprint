# Tomorrow Bootstrap Prompt

We are resuming the ForPrint System Blueprint work after the 2026-09-19 evening architecture discussion.

## First rule

Do **not** start by creating new policy files or new modules.

First inspect the current repository state and the existing canonical documents, roadmaps, standards, module boundaries and Q1–Q8 coordination/clarification mechanisms.

## Phase A — finish the daytime work

The previous daytime session left CF09 not formally closed.

Run only the current final technical gate first:

```bash
make check \
  2>&1 | tee tmp/20260918_make_check_final_after_all_repairs_v0_1.txt
```

Evaluate the result before doing anything else.

Preserve the existing dirty working tree. Do not reset, stash or clean legitimate changes.

## Phase B — architecture/policy audit

Inspect existing material for:
- Telegram Bot roadmap and responsibilities;
- Calculator Engine roadmap;
- CRM / customer-management responsibility;
- Operational Registry boundaries;
- Accounting Registry Service boundaries;
- Logistics Service boundaries;
- Prepress Hub boundaries;
- Integration Gateway boundaries;
- Blueprint Dispatcher/control-plane boundaries;
- current roadmap governance/package documents;
- existing Makefile/operator-interface standards;
- Q1–Q8 clarification/escalation documents;
- any existing process/workflow/orchestration concept;
- existing customer/profile/account-manager concepts.

Determine:
1. what already exists;
2. what is partial;
3. what conflicts with the evening discussion;
4. what should be extended;
5. what is genuinely missing.

## Phase C — integrate evening architecture concepts

Do not interpret “put it in roadmap” as “append everything to one roadmap file”.

Distribute concepts into the correct normative, canonical, derived, human-readable and machine-readable surfaces.

Main topics:
- Telegram Bot communication boundary;
- customer-specific semantic memory;
- adaptive customer preference drift;
- dynamic customer profiling and policy adaptation;
- continuous customer health/trajectory concept;
- historical asset indexing and retrieval;
- clarification workspace / structured Order Draft;
- durable long-running business process orchestration;
- hosted/incubated Process Manager capability with extraction readiness.

## Phase D — host decision for Process Manager

Do not create a standalone module yet.

Determine which existing module is the best temporary host.

Evaluate at least:
- Operational Registry;
- CRM;
- Logistics;
- any existing orchestration/control-plane component.

Chosen host must not absorb Process Manager semantics into its own internal model.

The capability must remain separable through:
- its own namespace/package;
- versioned contracts;
- own state model;
- own tests;
- explicit ports/adapters;
- minimal host-specific imports;
- explicit extraction-readiness requirement.

## Governance constraint

Much of the evening discussion is target architecture, not implemented state.

Do not present it as already built.
