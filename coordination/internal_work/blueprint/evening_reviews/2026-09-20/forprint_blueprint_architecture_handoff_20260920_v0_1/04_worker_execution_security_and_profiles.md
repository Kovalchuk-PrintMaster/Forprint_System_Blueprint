# Worker Execution Security & Profiles

## Core rule

**Reason broadly; act narrowly.**

A ForPrint worker may inspect and reason about broader module/portfolio context, but it may mutate only resources explicitly granted by its effective execution authority.

## Effective authority model

Target semantic model:

```text
Project / ecosystem policy
        ∩
Module policy
        ∩
Execution profile ceiling
        ∩
Current work lease / mutation scope
        =
Effective authority
```

The exact existing Blueprint model must be audited and reused/extended where possible.

## Why prompt-only safety is insufficient

Critical safety requirements can disappear from a long AI context, be compressed, or be misinterpreted. Therefore high-risk restrictions must be enforced in runtime/control-plane layers.

## Desired defense layers

1. Worker bootstrap/context instruction.
2. Structured execution profile.
3. Work lease / mutation scope.
4. Policy decision point.
5. Capability/action broker for sensitive actions.
6. Filesystem/mount isolation.
7. Network default-deny or scoped allowlist.
8. Secret/credential scoping and short-lived grants.
9. Device/privilege restrictions.
10. CPU/memory/PID/disk/time budgets.
11. Post-run mutation/effect audit.
12. Event publication for sensitive decisions.

## Filesystem principle

Prefer task-specific worktree/overlay/sandbox over direct canonical repository mutation.

Typical conceptual access:

- own task workspace: `RW`;
- own relevant module projection: controlled `RW`;
- strategic/Blueprint context: `RO`;
- foreign module repositories: no direct write; preferably query through coordination interface;
- host block devices/system administration surfaces: unavailable.

## Shell principle

Do not rely primarily on a blacklist of dangerous commands. A useful shell can remain available inside a constrained environment. The objects/capabilities reachable by that shell should be restricted.

## Sensitive actions

Potential brokered actions include:

- branch push;
- promotion/merge request;
- package installation beyond approved profile;
- deployment/test-environment access;
- external integration calls;
- secret access;
- cross-module mutation request.

## Inter-worker/module communication

Preferred model: structured coordination/query boundary, not arbitrary SSH/filesystem access.

Potential query types:

- `CAPABILITY_STATUS`
- `CONTRACT_DISCOVERY`
- `DEPENDENCY_STATUS`
- `IMPLEMENTATION_EVIDENCE`
- `ROADMAP_INTENT`
- `BLOCKER_QUERY`
- `COMPATIBILITY_QUERY`
- `DATA_OWNER_QUERY`
- `PROPOSAL_REQUEST`
- `CLARIFICATION_REQUEST`

Canonical projections should answer deterministic questions without waking another AI worker when possible.

## Worker proposals

Workers may submit non-authoritative insights such as:

- `ARCHITECTURE_IMPROVEMENT`
- `ROADMAP_RESEQUENCING`
- `DEPENDENCY_DISCOVERY`
- `MISSING_CAPABILITY`
- `DUPLICATION_DISCOVERY`
- `RISK_DISCOVERY`
- `SCOPE_CONFLICT`
- `OWNERSHIP_CONFLICT`
- `TECHNICAL_DEBT`
- `SIMPLIFICATION_OPPORTUNITY`

Proposal != execution authority.
