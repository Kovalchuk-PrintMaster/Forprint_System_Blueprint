# ForPrint CF-10 S01 – inert source staging (r005, 2026-10-30)

State: **STAGED_REVIEW_CANDIDATE_NON_AUTHORIZING**.

This source checkpoint records candidate `cf10_s01_live_pilot_corridor_v0_1.py` and its
isolated negative tests, and nothing more. It does NOT patch `Makefile`,
`governed_worker_cycle.py`, the ledger, signing/permission material or launch routes.

## Nonactivation invariants

- Existing Make `cf10-s01-runtime-launch-preflight` remains literal quarantine.
- Existing two Python entrypoints in `governed_worker_cycle.py` remain fail closed.
- Calling the staged corridor `launch` directly must block before claim, because
  `_assert_reviewed_live_source` rejects the absent approved Make binding.
- The code is a CANDIDATE, not a cryptographic review/acceptance of 04F 8/8.
- This step does not sign receipts, create trust, claim the one-shot slot or launch Worker.

## Next independent review and cutover

1. Confirm 182-pass r004 `PASS_SHADOW_INTEGRATED_NON_AUTHORIZING` in full s01 shadow.
2. Independently review the candidate code, source guards, claim durability,
   two Python entrypoints, 04F proof freshness, race/TOCTOU/concurrency, and authorized Make wiring.
3. If accepted, prepare one *separately reviewed* exact patch that binds the
   source to the two Python entrypoints and a governed Make target; rerun
   the complete integrated tests on a shadow of the then-current HEAD.
4. Publish final HEAD; only then issue current independent signed activation
   and release decisions for one worker/task/attempt. Do not re-sign beforehand.
5. Verify external proof matrix, bounded receipt, live release review and
   Make acceptance before any real launch, then collect and validate result.

The persistent one-shot marker is irreversible by design. Source staging must
never trigger claim or any background launch. `tmp/` artifacts are not authority.
