# CF-10 / r051 — Root-owned PRECLAIM witness for Task70

**Status:** NON_AUTHORIZING_SOURCE_NATIVE. Independent legacy signed release and
existing production Make / systemd quarantine remain unchanged.

## Exact boundary

`r045.collect` samples live facts only while Make and backend remain quarantined.
Once the exact Task70 attempt becomes `READY_FOR_WORKER_LAUNCH`, the privileged
`r051.issue` may capture its exact report and r050 snapshot into the existing
`/var/lib/forprint/cf10_s01_single_use` root-owned store. This is one immutable,
create-only JSON witness (0600) with fsync; `owner_launch.lock` serializes
capture against the existing PAM launch claim. No duplicate claim store exists.

Readback verifies canonical bytes, root ownership, mode, file type, hardlink
count, duplicate JSON keys, exact field set, current HEAD/task/attempt, report
semantics and snapshot SHA by independent recomputation. A partial or damaged
file never authorizes retry, removal or replacement. Recovery is read-only.

`r046.inspect(phase="LAUNCH_WINDOW")` reads r051's root-owned record instead of
recollecting r045 facts. `phase="PRECLAIM"` retains historical behavior. r051
never writes a release receipt, writer activation, canonical Worker Result,
terminal ledger, operator claim or systemd service. It does not authenticate PAM.
Its output is not trusted release authority, even after an exact verified read.

## Operator sequence (DO NOT execute before source cutover code is final)

1. Finish and publish all source changes, obtain a new original Task70 attempt
   with frozen source inputs and `READY_FOR_WORKER_LAUNCH`.
2. From root, with explicit operator review of task/attempt:
   `CF10_TASK=<task70> CF10_ATTEMPT=<fresh-attempt> make -s cf10-r051-preclaim-issue`
3. Read-only: `CF10_TASK=... CF10_ATTEMPT=... make -s cf10-r051-preclaim-inspect`.
4. Later LAUNCH_WINDOW read-only: `CF10_TASK=... CF10_ATTEMPT=... make -s cf10-r051-launch-window-proof-inspect`.
5. No actual Worker run until real, exact r046/r047 proof issuance, independent
   verifier, source-bound pilot Make/backend route, operator PAM, single-use
   claim before spawn, writer lock and canonical finalizer are separately
   tested and explicitly approved.

No `tmp/` dependency: all durable PRECLAIM bytes are under existing root state;
`tmp/` is only staging/delivery. No other independent services or Hestia paths
are touched. No automatic retry, acceptance, release or publication.

## Negative controls

Tests cover incomplete/changed r045, source drift during capture, duplicate
issue, wrong attempt/HEAD, partial/corrupt/missing record, unsafe permission,
symlink/hardlink, JSON duplicate key, SHA mismatch and non-authorizing replay.
