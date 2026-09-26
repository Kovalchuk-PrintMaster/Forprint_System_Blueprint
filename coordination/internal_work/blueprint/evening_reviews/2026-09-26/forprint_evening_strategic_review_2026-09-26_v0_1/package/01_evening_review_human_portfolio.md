# ForPrint Evening Strategic Review — 2026-09-26

## Status
This package preserves strategic and internal-infrastructure agreements from the evening discussion.
It is not execution authority, implementation authorization, or a frozen technical design.

## Planning horizons
1. Living practical roadmap — real near-horizon execution.
2. Detailed farther horizon — structured future practical development.
3. Strategic horizon — long-range theses and agreements to re-evaluate before implementation.

A separate internal service improvement pool exists for developer/assistant infrastructure improvements that do not expand ForPrint business capability.

## Internal service improvement pool
Do not execute these now as isolated micro-tasks; accumulate and later bundle:
- optimize `assistant-pack` as whole-project onboarding;
- optimize `assistant-context-pack` as scoped module/topic context;
- improve freshness/authority labels and signal-to-noise;
- design a machine-readable current-position pointer that shows current phase/checkpoint/next safe action without creating authority;
- verify cold-start context explicitly preserves interaction convention: assistant=feminine, operator=masculine.

## Strategic theses

### Reliable agent execution control
Candidate chain:
`Direction → Context → Authority → Execution → Verification → Acceptance → Evidence`

Cross-cutting planes:
- State / Identity
- Observability
- Recovery
- Security / Containment
- Resource / Cost policy

Preserve stable work identity vs attempt identity; version verifier evidence; prefer replayable typed traces; test recovery/faults; reconcile unknown external effects.

### Project-side governability
Distinct rights should eventually exist for:
`propose → prepare → execute → verify → recommend acceptance → accept → release → escalate`

Execution/evidence generation does not automatically grant acceptance authority.
Evidence requirements may depend on risk.

### Evolution generations / project epochs
Potential layers:
- artifact version;
- capability generation;
- module generation;
- project governance epoch.

Numerical version alignment is not required; compatibility with the current generation/epoch is what matters.
Candidate lifecycle:
`experimental → pilot → canonical → migration available → portfolio rollout → current → deprecated → retired`

### Trust-aware execution governance
Core principles:
- content is not authority;
- instruction is not authorization;
- authorization is not physical capability;
- untrusted content must not directly trigger privileged action;
- worker/model reasoning is only one defense layer;
- enforcement boundaries must remain effective even when the worker behaves incorrectly.

Candidate trust classes:
`authoritative / controlled_input / informational / untrusted`

### External-facing security posture — HIGH IMPORTANCE
External-facing modules such as Telegram Bot, Website, Calculator/external calculation inputs and future public/customer channels need dedicated protection against:
- prompt/instruction injection;
- malicious instructions embedded in images/documents/files;
- SQL injection;
- command/code injection;
- path traversal;
- schema/payload abuse;
- MIME/content spoofing;
- resource-exhaustion payloads;
- other channel-specific attacks.

Security must be continuously regression-tested, not treated as a one-time audit.
A verification/crash/security surface should periodically probe these modules for regressions.

### Consumer-declared contract expectations
Provider owns provider interface; consumer owns its expectation.
Known consumer expectations should participate in compatibility checks before integration.
Contract Registry/governance tracks the relationship.
Gateway is a runtime boundary, not the sole contract authority.
Syntactic compatibility does not prove semantic compatibility.

Candidate stack:
`schema/syntax → consumer expectation → semantic compatibility → business invariants`

### Typed verification and evidence semantics
A generic green `PASS` must not imply universal correctness.

Candidate evidence types:
- structural
- schema
- contract
- behavioral
- integration
- governance
- security
- migration
- recovery

Acceptance is a separate lifecycle decision.
Future evidence should preserve verifier identity/version, oracle source/validity, feedback role, evaluation independence, scope, what is proven, and what is not.

### Trustworthy Change and Responsibility Topology
Candidate lifecycle:
`INTENT → AUTHORIZED → EXECUTED → VERIFIED → INTEGRATED → ACCEPTED → OPERATIONALLY_PROVEN`

Each transition may have its own authority owner and evidence requirements.
Cross-domain changes may require multi-anchor acceptance.
Operational proof is distinct from pre-release acceptance.

### Capability-mediated domain data access
Assistants should not receive broad direct database access by default.

Preferred model:
`assistant → authorized domain capability → domain-owned contract → runtime policy enforcement → canonical result`

Authorization may depend on identity, capability, purpose, context and data scope.
Read/propose/mutate capabilities should remain distinct.
Transport/protocol is not frozen.

### Graph-first project knowledge architecture
Prefer structured machine-readable project knowledge and queryable graphs over exhaustive prose.

Human-authored layer:
- WHY
- policy
- intent
- rationale
- ADR
- concise system/portfolio overviews

Machine-readable layer:
- modules
- capabilities
- ownership
- contracts
- data objects
- dependencies
- workflows
- validators
- evidence
- lifecycle state

Generated views should eventually support module graphs, cross-module dependencies, end-to-end flows, contract-consumer graphs, execution flows and impact graphs.

Core pattern:
**local truth, central projection**

Do not create a new documentation/graph module now.

### CI/CD as governance enforcement
CI should be adopted after the worker/governance baseline becomes stable.

CI Gen 1:
- syntax/schema
- unit tests
- contract tests
- diff checks
- governance checks

CI Gen 2:
- consumer-driven contracts
- cross-module compatibility
- generated-artifact drift
- typed verification evidence

CI Gen 3:
- security regression
- adversarial input testing
- recovery/fault-injection checks for high-risk surfaces

Core rule:
`CI PASS ≠ ACCEPTED ≠ MERGED ≠ RELEASED`

CD belongs to a later horizon after mature acceptance, release authority, staging, observability and rollback/recovery.

## Integration rule
All strategic theses above are long-range design inputs, not direct implementation tasks.
They must be re-evaluated against the then-current architecture before implementation.
Preserve both machine-readable representation and concise human chronological rationale.
