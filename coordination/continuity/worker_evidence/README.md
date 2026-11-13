# ForPrint CF-10 — durable Worker evidence

This directory is Git-tracked project history, **not a working cache**. Source artifacts in `tmp/` and `forprint-worker-runtime/` may be deleted *only after* the attempt's evidence snapshot has been persisted, validated, inspected and committed. Never modify immutable Worker results, Execution Attempt Ledger entries or operator decisions to point at new locations.

Each attempt has an append-only directory `<attempt_id>/` containing:

- `manifest.yaml` — repository-relative evidence references, original SHA-256, reviewed commit, and provenance. Its `canonical_git_reference` entries resolve through the pinned `git_anchor_commit`, not today's working tree.
- `objects/` — exact-byte copies of evidence that originally lived in `tmp/` or the isolated Worker runtime.
- `supplemental/` — frozen Handoff origin and dispatch inputs, recorded separately because they were **not** among the original eleven accepted evidence bindings.

The canonical ACCEPT decision and pair of ledger events are referenced, **not duplicated**. This snapshot is derived audit material and never creates operator authority, a new ACCEPT, Worker promotion, commit, push or publication attestation.

## Project-native tool

`python -B scripts/coordination/control_plane/persist_worker_acceptance_evidence_v0_1.py --decision-record coordination/continuity/worker_result_decisions/<decision>.yaml --check`

Then, on PASS:

`python -B scripts/coordination/control_plane/persist_worker_acceptance_evidence_v0_1.py --decision-record coordination/continuity/worker_result_decisions/<decision>.yaml --persist`

Verify in the current checkout, and again after `tmp/` or Worker runtime is cleaned:

`python -B scripts/coordination/control_plane/persist_worker_acceptance_evidence_v0_1.py --decision-record coordination/continuity/worker_result_decisions/<decision>.yaml --verify`

Commit the tool, tests, this README, and the resulting attempt directory in a **separate bounded Git commit** following staged scope review. Do not use `git add -A`. A script in `tmp.py` is not an archival mechanism.

Per-file protection: SHA-256 against the original ACCEPT bindings, file size caps, basic credential detection, no symlinked sources, no overwriting existing snapshots, and no source/ledger mutation. All copies are subject to code review before remote publication. The snapshot supports reproducible **acceptance audit**, not an unsupported claim of bit-for-bit replay of the entire external Worker runtime.
