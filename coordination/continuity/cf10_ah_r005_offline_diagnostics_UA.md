# CF-10 / AH r005 — offline Copilot failure diagnostics (Ukrainian)

## Baseline
AH r004 committed at `47e1635df4df9d6c4c08fc61cde9513232d34b7b`. Server regressions **971 PASS + 60 subtests**; one physical delegated Worker trial HOLD at `DELEGATED_WORKER_CGROUP_POPULATED_1`. That evidence did not establish whether real Copilot exited nonzero, timed out, lacked filesystem access or its proof frame was unavailable. No inference, no provider credentials, no production claim.

## Change
Retain one canonical Dispatcher API → AG nonce → AE delegated Worker physical lifecycle. The existing pinned CLI `--version` remains the *only* Copilot argv. Add an exact, bounded `COPILOT_OFFLINE_VERSION_HOLD` child frame when the CLI fails. Root verifies the nonce, unit, allowed failure code, numeric exit/errno, output byte counts and SHA-256 of at most the first 4 KiB. **Never include raw stdout/stderr, environment or credential contents.** Explicit failure is a HOLD; it cannot be accepted as a result or terminal success. The systemd unit is stopped and disposable runtime cleaned as before. Unknown crashes stay unavailable/unknown, not reclassified as success.

No production launcher, root service, Hestia, systemd unit installation, claim ledger or provider networking is changed. `tmp/` only for disposable delivery/evidence. No automatic re-execution, no automated fallback and no retry within the physical batch. Existing AE and AG default modes remain unchanged. G1–G5 remain OPEN.

## Acceptance
- Full relevant regression suite before/after source install; source-only Make check; exact dirty tracked hashes and pinned Git tree; commit/push only after tests.
- One physical disposable run with `--version`; success requires real CLI version + IPC result + kernel 1→0 + retained/stop. If HOLD, evidence includes only allowlisted diagnostic metadata and preserves the validated commit.
- Never interpret real subprocess failure as Copilot inference or successful Worker.
