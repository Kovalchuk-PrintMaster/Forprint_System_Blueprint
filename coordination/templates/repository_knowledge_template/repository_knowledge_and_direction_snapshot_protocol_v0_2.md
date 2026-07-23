# ForPrint Repository Knowledge & Direction Snapshot Protocol v0.2

## 1. Purpose

This protocol creates a lightweight manual memory layer for the growing ForPrint system.

It is designed to prevent:

- forgotten implementations being rebuilt elsewhere;
- unexplained scripts, directories and dependencies;
- duplicate validators, reports, contracts or utilities;
- dormant code being confused with dead code;
- operational chains existing only in an assistant's memory;
- repeated switching between unrelated tasks;
- workstreams consuming time without contributing to a declared goal;
- loss of the original reason behind prompts, contracts and module boundaries;
- later uncertainty about why a module was asked to implement a particular front.

The protocol is deliberately manual in v0.2. The future Project Inspector may automate collection and analysis later.

## 2. Artifact set

### 2.1 Repository Capability Inventory — RCI

Answers:

- What project-owned paths exist?
- What does each important path do?
- What is verified, inferred, unknown or conflicting?
- Who owns the capability?
- What consumes it?
- What side effects exist?
- Is it active, occasional, dormant, duplicated, orphaned, deprecated or generated?
- Which dependencies were added and why?

### 2.2 Repository Execution & Dependency Map — REDM

Answers:

- What triggers an operation?
- Which files, targets, functions, contracts and dependencies participate?
- In what order?
- What inputs, outputs and side effects exist?
- Where can the flow fail?
- What recovery path exists?
- Which links remain unverified?
- Are there parallel or duplicate flows?

### 2.3 State, Direction & Rationale Snapshot — SDRS

Answers:

- What is the current state?
- What are the declared goals?
- Why are those goals important?
- What work has already been completed toward them?
- What is active now?
- Which prompts, decisions and reports explain the current direction?
- What is blocked or uncertain?
- Is effort balanced?
- Is the scope drifting?
- Which workstream should continue, pause, stop, split or receive more support?

## 3. Profile-specific structure

### 3.1 Blueprint repository

```text
coordination/
└── repository_knowledge/
    ├── README.md
    ├── repository_knowledge_and_direction_snapshot_protocol_v0_2.md
    ├── inventory/
    ├── flows/
    ├── direction/
    │   ├── blueprint_coordination/
    │   └── system_portfolio/
    └── templates/
```

Blueprint creates:

- one RCI snapshot;
- one REDM snapshot;
- one `blueprint_coordination` SDRS;
- one `system_portfolio` SDRS.

### 3.2 Module repository

```text
coordination/
└── repository_knowledge/
    ├── README.md
    ├── repository_knowledge_and_direction_snapshot_protocol_v0_2.md
    ├── inventory/
    ├── flows/
    ├── direction/
    │   └── module_self_view/
    └── templates/
```

A module creates:

- one RCI snapshot;
- one REDM snapshot;
- one `module_self_view` SDRS.

## 4. Naming

```text
YYYY-MM-DD__<scope_id>__repository_capability_inventory_v0_2.yaml
YYYY-MM-DD__<scope_id>__repository_execution_dependency_map_v0_2.yaml
YYYY-MM-DD__<scope_id>__state_direction_rationale_snapshot_v0_1.yaml
```

Examples:

```text
2026-07-17__forprint_system_blueprint__repository_capability_inventory_v0_2.yaml
2026-07-17__forprint_system__state_direction_rationale_snapshot_v0_1.yaml
2026-07-17__forprint_library__state_direction_rationale_snapshot_v0_1.yaml
```

## 5. Evidence and honesty model

Every substantive claim must use:

```text
verified
inferred
unknown
conflicting
```

Confidence:

```text
high
medium
low
none
```

A filename is never sufficient for `verified`.

Unknowns must remain visible. Do not convert uncertainty into polished but unsupported prose.

## 6. Usage-state model

```text
active
occasional
dormant_candidate
duplicate_candidate
orphan_candidate
deprecated
generated
external
unknown
```

Do not use `dead` without separate proof, review and deletion approval.

## 7. Ignore policy

Ignore contents of:

```text
.git/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.cache/
.idea/
.vscode/
node_modules/
.venv*/
venv/
env/
dist/
build/
coverage/
htmlcov/
tmp/
temp/
logs/
```

Also ignore:

- compiled bytecode;
- editor artifacts;
- OS metadata;
- secrets and local credentials;
- downloaded dependencies;
- large binary outputs.

Summarize rather than enumerate:

- generated reports;
- repetitive migrations;
- large fixture collections;
- datasets;
- static assets;
- vendored source;
- lockfiles.

Always inspect important project-owned entrypoints, manifests, schemas, contracts, scripts, tests, coordination records, runbooks, recovery guides and files changed since the prior snapshot.

## 8. Manual inspection algorithm

### Phase A — baseline

Record repository, scope, branch, commit, tree state, date, author, prior snapshots and ignore rules.

### Phase B — directory pass

Describe relevant directories before individual files:

- declared purpose;
- observed purpose;
- owner;
- content class;
- evidence;
- confidence;
- usage state;
- unknowns.

### Phase C — priority file pass

Inspect in this order:

1. Make targets, CLIs and application entrypoints;
2. contracts, schemas and manifests;
3. implementation called by entrypoints;
4. tests and fixtures;
5. configuration;
6. coordination, runbook and recovery records;
7. remaining project-owned files.

### Phase D — evidence pass

Use evidence in this order:

1. runtime or direct entrypoint;
2. import, call or reference;
3. Make/task target;
4. test;
5. manifest or config;
6. documentation;
7. Git history or completion report;
8. filename inference.

### Phase E — flow extraction

Map flows from:

- CLI and Make commands;
- HTTP endpoints;
- event handlers and consumers;
- validators;
- report generators;
- previews;
- migrations;
- recovery operations.

### Phase F — direction extraction

For SDRS, collect:

- current declared purpose;
- north-star outcome;
- active objectives;
- work completed toward each objective;
- current workstreams;
- recent decisions and why;
- prompt/report/commit evidence;
- dependencies and bottlenecks;
- unknowns;
- potential drift;
- recommended attention changes.

### Phase G — duplicate/dormancy review

Flag without deleting:

- similar capabilities in multiple paths;
- parallel validators;
- multiple scripts producing the same artifact;
- old and new entrypoints together;
- unsupported or unexplained files;
- repeated schemas and error taxonomies;
- workstreams with repeated effort but little goal contribution.

### Phase H — historical comparison

Compare to the immediately previous snapshot:

- added, removed, moved and renamed paths;
- changed purposes and confidence;
- new or removed flows;
- changed goals;
- objective progress;
- decisions that changed direction;
- unresolved items carried forward;
- drift or rework signals.

## 9. Blueprint SDRS profiles

### 9.1 `blueprint_coordination`

Scope is Blueprint's own control-plane work:

- prompt preparation and issue workflow;
- report intake and acceptance;
- standards and schema consistency;
- module balancing;
- recovery and audit procedures;
- automation toward low-friction or one-command operations;
- reliability of module-to-Blueprint communication;
- future Inspector, Gateway governance and contract governance preparation.

This snapshot must not pretend to be the whole-system portfolio view.

### 9.2 `system_portfolio`

Scope is the full ForPrint program:

- system purpose and north-star outcomes;
- module portfolio;
- critical path;
- cross-module dependencies;
- work completed toward system outcomes;
- active and planned fronts;
- overloaded, blocked or low-value workstreams;
- missing capabilities or modules;
- rationale behind historical prompts;
- system-wide drift and balance.

It must distinguish:

```text
module_reported_view
blueprint_assessment
verified_system_fact
unresolved_conflict
```

## 10. Module SDRS profile

### `module_self_view`

The module assistant records its own view:

- what the module currently does;
- what stage it is in;
- what has been completed;
- what is active;
- what it believes should happen next;
- dependencies and blockers;
- unknowns and confidence;
- perceived duplicate or dormant areas;
- expected contribution to the wider system.

The module must not claim authority over whole-system priorities.

Recommendations must be marked as module proposals, not Blueprint decisions.

## 11. Decision and prompt rationale

Every important decision entry should capture:

- decision ID;
- date;
- decision;
- problem addressed;
- rationale;
- rejected or deferred alternatives;
- affected modules;
- expected outcome;
- prompt IDs;
- report and commit evidence;
- review date;
- current validity.

This is how later analysis can answer why a prompt existed and whether its rationale still applies.

## 12. Workstream evaluation

Each workstream records:

```text
status
goal_contribution
value_signal
cost_signal
risk
dependency_effect
recommendation
```

Allowed recommendations:

```text
continue
accelerate
support_dependency
split
pause
stop_candidate
reassess
unknown
```

`stop_candidate` is a review recommendation, not authorization to stop work.

## 13. Snapshot cadence

Suggested cadence:

- rapidly changing repository: every 1–2 weeks;
- moderate repository: monthly;
- stable repository: after major fronts or every 2–3 months;
- Blueprint system portfolio: every 1–2 weeks during active expansion;
- always before major refactors, Gateway activation, ownership changes or new module creation.

## 14. Historical review

After enough snapshots accumulate, perform a manual historical review across a chosen period.

The review should identify:

- stable versus changing goals;
- recurring blockers;
- repeated rework;
- workstreams that consume attention without advancing goals;
- neglected critical dependencies;
- modules repeatedly waiting on others;
- reasons for direction changes;
- missing capabilities;
- useful historical implementations worth reusing;
- areas ready for automation.

Do not create dashboards or scoring systems in v0.2 unless clearly needed.

## 15. Completion criteria

A snapshot set is complete when:

- metadata and ignores are recorded;
- important directories and files are represented;
- evidence and confidence are explicit;
- unknowns remain visible;
- major operational chains are mapped;
- duplicate/dormant/orphan candidates are non-destructive;
- current goals and workstreams are linked to evidence;
- decisions and prompt rationale are recorded;
- prior snapshots are compared;
- YAML validates;
- implementation files were not modified.

## 16. Prohibited behavior

Do not:

- delete, move, rename or rewrite implementation files;
- invent ownership or runtime evidence;
- hide unknown paths;
- copy secrets;
- enumerate caches and environments;
- label code dead from age alone;
- overwrite prior snapshots;
- convert a module proposal into a Blueprint decision;
- claim strategic drift without evidence;
- use the snapshot as an automatic stop/merge authorization.

## 17. Result states

```text
READY
READY_WITH_UNKNOWNS
BLOCKED
INVALID
```
