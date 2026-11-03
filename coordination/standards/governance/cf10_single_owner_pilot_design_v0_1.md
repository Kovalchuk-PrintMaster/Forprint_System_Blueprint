# CF-10 — single-owner bounded pilot: governance reconciliation r044

**Decision (2026-11-03):** the owner selected the simpler single-owner pilot profile over creating a second human reviewer. This is an architecture choice, **not an existing runtime release, operator password, claim, acceptance, publication or approval of an unbounded Worker**.

## Historical rule and why it exists

The prior CF-10 S01 release route requires eight independent proof digests, a distinct Ed25519 release signer, verified writer activation and a separate release quarantine. It protects against unobserved bypasses, stale approvals, parallel ledger writes, source drift and unverifiable Worker outcomes. Historical receipts, decisions and evidence must remain unaltered and the existing signed-release verifier must retain its semantics.

## New owner decision

For a single low-risk **internal Blueprint Task70** pilot, one accountable owner may give an interactive PAM-confirmed, task/attempt-bound decision. It is not necessary to invent a second administrator or pretend independent human approval exists. Existing owner PAM launch and root-owned one-use claim are reused; no newly minted 8-hour authorization leases are needed. Each new attempt requires a fresh decision; partial or ambiguous prior attempts are quarantined, not retried.

The **technical verifier remains separate from the owner's human decision**. It must prove source/HEAD identity, bounded write-set, writer lock, systemd cgroup lifecycle, durable PRE/POST, trusted result/Handoff/delta, immutable ledger and safe recovery. Missing evidence must produce `BLOCKED`, never `SUCCEEDED`.

## What is not changed by r044

- `cf10-s01-runtime-launch-preflight` remains quarantined, including `governed-worker-cycle-advance` dependencies.
- `LIVE_CUTOVER_ENABLED` remains `False`.
- The existing eight-proof independent release mechanism remains intact for its original profile.
- No independent proof is forged, waived by setting a boolean, or inferred from this written decision.
- No Worker is launched and no canonical ledger or durable receipt is mutated.
- No cross-module rollout, Task80, automatic acceptance, promotion, Git commit/push or next-wave selection is granted.
- `tmp/` remains disposable, including preview/report ZIPs.

## Explicit reconciliation and release path

1. Record owner-selected design and tests (r044). Label it **non-authorizing**. Keep the previous independent release path unchanged.
2. Engineer a **separate** pilot admission adapter that verifies authoritative owner session + exactly one new attempt, pinned source, runtime prerequisites, claim before spawn and independent technical evidence. Do not reuse the old `signed_release` schema to misrepresent the signer.
3. Test positive/negative cases including tampering, HEAD drift, expired/missing authority, wrong attempt, double claim, missing PRE/POST, controller loss, tmp unavailable, false `systemd success`, rejected result and concurrent writer. Independent runtime provenance and reboot proof remain separate release criteria.
4. Obtain an explicit **single-attempt** operator cutover decision after server evidence; source-bound Make and systemd wiring must use the approved admission, never a static `True` flag alone.
5. Launch a **new** Task70 attempt. Stop at operator review, reconcile declared vs observed delta, then decide acceptance/promotion separately. Proceed to Task80 only after this cycle is proven.

## Status and ownership

`OWNER_SELECTED_DESIGN_NON_AUTHORIZING`. The owner is the authority for the design direction, but the existing runtime policy remains effective until deliberately reconciled with evidence. Old attempts and signed release data remain immutable.
