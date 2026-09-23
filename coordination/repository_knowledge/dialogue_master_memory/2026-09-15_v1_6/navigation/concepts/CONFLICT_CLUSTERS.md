# Conflict / supersession clusters

These clusters keep contradictions visible instead of silently choosing one historical statement.

## CC-001 — Current authority vs stale bootstrap/continuity
**Status:** CURRENT_AUDIT_REQUIRED
Historical START_HERE/bootstrap/handoffs repeatedly retained current-looking stale phase claims. The reviewed authority front door is releases/current.yaml, but navigation surfaces need reconciliation.

Historical items: `IT-BP1708-0001`, `IT-BP2708-0001`, `IT-BP0909-0017`, `IT-BP0909-0018`, `IT-BP1009-0001`, `IT-BP1009-0002`  
Last-known review findings: `B01-F001`, `B01-F002`, `B02-F001`, `B02-F002`

## CC-002 — Completion evidence vs acceptance authority
**Status:** REFINEMENT_CHAIN_WITH_REMAINING_AUDIT
The project evolves from completion-report evidence to explicit acceptance transactions; later same-phase progression is automated, while major phase boundaries remain operator-controlled. Automatic acceptance itself must not be inferred from evidence alone.

Historical items: `IT-BP0508C-0031`, `IT-BP1708-0007`, `IT-BP1708-0008`, `IT-BP1708-0009`, `IT-BP2708-0014`, `IT-BP2708-0015`, `IT-BP0909-0009`, `IT-BP0909-0010`  
Last-known review findings: `B06-F006`

## CC-003 — Globally clean tree vs parallel bounded execution
**Status:** HISTORICALLY_SUPERSEDED_DIRECTION_CURRENT_AUDIT_REQUIRED
Early mutation/seal checks often assumed a clean worktree; later owner doctrine explicitly rejects global cleanliness as a prerequisite for safe parallel work and uses bounded baselines/owned scopes.

Historical items: `IT-BP0508-0018`, `IT-BP0508C-0004`, `IT-BP2708-0009`, `IT-BP2708-0010`, `IT-BP2708-0011`, `IT-BP0909-0015`  
Last-known review findings: `B06-F010`

## CC-004 — Fake canonical data vs bounded temporary fixtures
**Status:** NEEDS_POLICY_RECONCILIATION
Early doctrine rejects fabricated dependency truth. Later work permits bounded temporary catalogs/fixtures to exercise logic. Current policy should explicitly distinguish non-authoritative fixtures from fake canonical truth.

Historical items: `IT-BP1406-0003`  
Last-known review findings: —

## CC-005 — Synthetic planning vs accepted architecture
**Status:** KNOWN_RISK
Synthetic future steps are useful but must remain visibly synthetic/non-executable. Vocabulary/schema fragmentation can make planning artifacts look authoritative.

Historical items: `IT-BP3108-0016`, `IT-BP3108-0017`, `IT-BP0509-0005`  
Last-known review findings: `B02-F010`, `B02-F011`, `B06-F013`

## CC-006 — Logistics pilot authority and expansion gate
**Status:** LAST_KNOWN_RULE_COHERENT_BUT_RUNTIME_VERIFY
Logistics-only pilot converges on minimum two successful real automatic runs, positive stability review and a separate expansion decision; duplicate historical pilot-gate surfaces still need effective-state reconciliation.

Historical items: `IT-BP1708-0018`, `IT-BP2708-0023`, `IT-BP2708-0024`, `IT-BP2708-0025`, `IT-BP3108-0002`, `IT-BP0909-0008`  
Last-known review findings: `B02-F005`, `B06-F002`

## CC-007 — Contract Registry vs Gateway vs domain authority
**Status:** ARCHITECTURE_DIRECTION_ACCEPTED_CURRENT_IMPLEMENTATION_VERIFY
Domain modules own meaning, Contract Registry owns versioned agreements, Gateway validates/routes runtime traffic. These responsibilities must not collapse.

Historical items: `IT-BP3108-0029`, `IT-BP3108-0030`, `IT-BP3108-0031`, `IT-BP3108-0032`, `IT-BP3108-0033`, `IT-BP3108-0034`, `IT-BP3108-0035`  
Last-known review findings: `B01-F012`

## CC-008 — Module inventory and identity drift
**Status:** CURRENT_AUDIT_REQUIRED
Historical counts move across 19/21/22 and current reviews still find identity/double-count mismatches. Machine IDs must be canonical before automated portfolio selection.

Historical items: `IT-BP3108-0006`, `IT-BP2708-0031`  
Last-known review findings: `B02-F009`, `B06-F005`, `B01-F010`

## CC-009 — Artifact/script revision identity
**Status:** CURRENT_AUDIT_REQUIRED
Old script versions and revision collisions repeatedly caused safe failures. Unique descriptive archives and strong revision/hash checks became explicit requirements.

Historical items: `IT-BP2708-0008`, `IT-BP2708-0034`, `IT-BP0909-0004`  
Last-known review findings: `B06-F007`, `B06-F008`

## CC-010 — Human docs vs machine governance parity
**Status:** CURRENT_AUDIT_REQUIRED
Several owner/theory decisions were richer than their machine-readable governance projection. Both sides need effective-state links and parity checks.

Historical items: `IT-BP3108-0008`, `IT-BP0509-0009`, `IT-BP1009-0019`  
Last-known review findings: `B06-F003`, `B06-F004`, `B06-F009`, `B06-F012`

## CC-011 — Roadmap plan vs actual execution authority
**Status:** CURRENT_AUDIT_REQUIRED

12.09 makes the long-running roadmap lag explicit. CF-02 intends lifecycle/event-store state to drive generated roadmap execution projections, eliminating manual double-write. Final CF-02 PASS is not preserved.

## CC-012 — Whole-mutator rerun vs state-aware partial recovery
**Status:** SAFETY_INVARIANT_CURRENT_AUDIT_REQUIRED

Multiple failures say `canonical_state_may_have_advanced=true` and `do_not_rerun_blindly=true`. Recovery must continue from the real state boundary, not replay already-applied source mutation.

## CC-013 — Structural PASS vs semantic freshness
**Status:** CURRENT_AUDIT_REQUIRED

08.09 Logistics evidence explicitly separates structural validation from semantic freshness.

## CC-014 — Local module health vs portfolio strategic alignment
**Status:** ARCHITECTURAL_INVARIANT

A module needs project-course/dependency/runtime evidence before final disposition.

## CC-015 — Generated PASS/projection vs reconciled source truth
**Status:** CURRENT_AUDIT_REQUIRED

Reconcile authority/provenance first; only then regenerate guides, diagrams and status projections.

## CC-016 — Stale diagnostic log vs current-tree / isolated-check truth
**Status:** CURRENT_AUDIT_REQUIRED

A public-check report can be stale relative to current source/test pins. Confirm current-tree truth and snapshot/report provenance before repairing source.

## CC-017 — Stale handoff plan vs durable current state
**Status:** ARCHITECTURAL_INVARIANT

A handoff is not execution authority. Revalidate Git/release/lifecycle state before mutation and skip work already proven closed.

## CC-018 — Focused tests green vs semantic/governance candidate correctness
**Status:** CURRENT_AUDIT_REQUIRED

CF-02 candidate v0.1 passed mechanical checks but semantic review found seven blockers. Local tests alone are not an acceptance gate for control-plane changes.
