# CF-10 Project-native Pilot Cycle — R068 bounded integration candidate

Status: **SOURCE CANDIDATE — NOT PRODUCTION-VERIFIED**. Exact baseline:
`bfe29b2b3135c769afaf612c0dc19629bd1be29f` on
`audit/blueprint-inventory-refresh-2026-07-29`.

## Inventory and ownership

- Canonical transition and status: `governed_worker_cycle.py`.
- Operator PAM and no-retry launch: `cf10_owner_operator_console_v0_1.py`,
  `cf10_owner_pam_launch_v0_1.py`.
- Existing Make controls: `governed-worker-cycle-prepare`,
  `governed-worker-cycle-ack`, `governed-worker-cycle-authorize-dispatch`,
  `cf10-r051-preclaim-issue`, `cf10-s01-pilot-launch-preflight`,
  `cf10-s01-pilot-owner-run`, `cf10-resume`.
- Proof boundary: r045 admission, r051 root PRECLAIM, r046/r047 source lineage;
  **independent proof issuance and PAM review remain separate**.
- R013 contract: `cf10_supervisor_binding_candidate_v0_1.py`; canonical binding
  in `cf10_r030_canonical_systemd_route_v0_1.py`; provider argv in
  `worker_runtime/invocation_adapter.py`.

## Verified integration gap

The invocation adapter puts a full multiline Copilot task prompt after `-p`,
while R013 rejected all newlines and arguments longer than 2000 characters.
R068 permits only the exact `-p`/`--prompt` value to be multiline up to 64 KiB
and the structured MCP config up to 8 KiB, with an aggregate argv budget.
Other arguments remain <= 2000 bytes without newline. A real frozen invocation
must still pass canonical `bind_contract` and the backend; passing the R068
structural fixture is **not** Worker launch authorization.

## Canonical operator commands

Scope is deliberately exact Task70 and attempt; other Work Fronts are not
implicitly admitted. Use environment variables in one Make call, e.g.:

```
make cf10-pilot-status GOVERNED_WORKER_TASK=cf10-validation-check-pipeline-profile-and-optimization-v0-1 GOVERNED_WORKER_ATTEMPT=cf10-u180j-a053
make cf10-pilot-plan GOVERNED_WORKER_TASK=cf10-validation-check-pipeline-profile-and-optimization-v0-1 GOVERNED_WORKER_ATTEMPT=cf10-u180j-a053
make cf10-pilot-resume GOVERNED_WORKER_TASK=cf10-validation-check-pipeline-profile-and-optimization-v0-1 GOVERNED_WORKER_ATTEMPT=cf10-u180j-a053
make cf10-pilot-launch-once GOVERNED_WORKER_TASK=cf10-validation-check-pipeline-profile-and-optimization-v0-1 GOVERNED_WORKER_ATTEMPT=cf10-u180j-a053
make cf10-pilot-report GOVERNED_WORKER_TASK=cf10-validation-check-pipeline-profile-and-optimization-v0-1 GOVERNED_WORKER_ATTEMPT=cf10-u180j-a053
```

`launch-once` triggers only after the current canonical source, frozen attempt,
root store, absence of claim/ledger, PRECLAIM and independently reviewed r046
proofs are checked. It then calls the **existing** Make guard and existing PAM
console. There is no retry on nonzero exit. The `resume` command without
launch permission prepares and advances to the next unresolved human gate.

When r046 proofs are missing, the command must stop with
`INDEPENDENT_ROOT_PROOF_REVIEW_REQUIRED`: historical 22/22 fixture closure is
not a signature or authorization and is not recreated here.

After the first publication of R068, existing a052 remains frozen at the old
HEAD. **Do not rebind it to new source or replay its ACK/dispatch.** First
reconcile a052 from actual s01 durable state; then explicitly select a new
attempt on the new published HEAD. Preserve a051 consumed claim forever.

`tmp/` is used only for delivery/staging. The installed code and docs are
tracked in Git; runtime receipts live outside tmp. Hestia and sudoers are out
of scope. No automatic acceptance, merge, commit, push or release is enabled.

## Runtime provisioning and irreversible boundaries

- `make cf10-pilot-runtime-provision` is an explicit root-TTY source command:
  it may create only an absent durable `control_plane/root_receipts` (root:0700)
  and an absent attempt `logs` directory before PRECLAIM. No chmod/rewrite of
  occupied stores, no root receipt emission, no Worker/ledger/claim mutation.
- The existing `cf10_owner_pam_launch_v0_1.launch_once()` invokes the R068
  preclaim guard **before operator PAM** and again while holding owner lock
  immediately **before** the irreversible O_EXCL owner claim. A missing root
  receipt store, unsafe logs or R013 parser regression cannot spend a claim.
- `run`/`resume` never enter worker launch by default. A separate explicit
  `cf10-pilot-launch-once` enters the existing source-pinned Make/PAM once,
  only after independently verified r046/r047 proof is available.

## Completion gates

1. `make cf10-pilot-check` and existing R013, governed-cycle, owner and r055
   suites must pass; verify real integrated source/Make behavior on s01.
2. Independent inventory confirms no critical source drift and relevant
   contract hashes; commit and push on the governed branch only after review.
3. Freeze a *new* attempt at the published HEAD; complete existing independent
   proof review and explicit operator PAM launch once.
4. Verify real systemd STARTED/terminal and immutable result return.
5. Use existing S3 `resume` for closeout and separate operator review.

This patch does **not** claim that a real worker has started or that the
external proof issuer has been migrated into the repository. Full end-to-end
one-command operation remains blocked on those source/native integrations.
