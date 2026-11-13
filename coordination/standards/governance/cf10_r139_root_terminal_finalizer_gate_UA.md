# CF-10 R139 — root terminal evidence prerequisite for existing canonical finalizer

**Source-only, no live admission.** Base: `18c8ee0a8b4bf45daed43cc2b4bb1169fdcb8ba7`.

R138 has already joined the root-side R035 PRE+POST, R015 and one immutable `STARTED/PENDING` ledger fact. R139 closes the *next* seam in the existing `governed_worker_cycle.advance_cycle()`: first-time terminal finalization for a pending attempt requires that **same** root-only readback, exact systemd unit/invocation, source HEAD, Handoff and baseline. No worker-supplied root certificate is trusted. The readback happens only as root; if called unprivileged it blocks. It calls the existing R138 verifier rather than inventing a second ledger writer or a new Worker Result validator.

This guard executes **after** the existing R037 independent candidate validation and **before** the existing `dispatch_intent.finalize_cf10_workspace_result_artifact` commit/ledger append. A missing root receipt, incorrect invocation, an already terminal row, a dirty/corrupt root chain, or a conflicting ledger digest produces `R139_ROOT_TERMINAL_GATE:...` BLOCKED. Existing terminal replay remains its existing no-second-append path. Incomplete historical PENDING attempts without new root proofs are deliberately blocked for manual reconciliation rather than grandfathered into success.

The gate only establishes prerequisite root lineage. It does **not** attest G1–G5, credentials/inference/tool egress, accept Worker Result, authorize retry, or perform a ledger write itself. The existing finalizer remains authoritative for full Handoff, workspace-delta, freshness and append. `LIVE_CUTOVER_ENABLED=False` remains unchanged; R115 legacy IPC rejection remains unchanged. No changes to Hestia, `/etc/sudoers.d/hestiaweb`, systemd, PAM or durable runtime stores.

Operator: apply the exact pinned Git package using the provided Make/CLI wrapper, retain unrelated dirty paths, run focused regression before one normal fast-forward Git commit. On HOLD, do not rerun, clean worktree, or invent terminal ledger proof.
