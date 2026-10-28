# CF-10 Make surface transition: Q1 (non-authorizing)

**Reason:** Blueprint operational capability grew beyond an experimental scratch workspace. The primary Makefile must be a stable, versioned command map that is not dependent on ephemeral scratch checkouts, outputs, proof inputs or system scratch roots.

**Migration rule:** Code lives in Git-owned `scripts/`; immutable historical evidence remains unchanged and is referred to only via reviewed provenance; generated reports live under ignored `generated/`; writable service runtime state lives under dedicated `/srv/software_development/forprint-*-runtime` roots. Neither reports nor new runtime directories are automatic acceptance evidence.

**Compatibility:** Existing targets are retained where possible; default paths have changed. Files from previous runtime locations are **not** copied, accepted, or rebound automatically. The invocation of old gate-related Make targets is **QUARANTINED** until independent operator action, reference release migration, validated coverage evidence, signature renewal, and a separately reviewed replacement launch gate are complete.

**Blocked targets:** `cf10-s01-runtime-launch-preflight`, `cf10-s01-runtime-binding-inspect`, and by dependency `governed-worker-cycle-launch`, `governed-worker-cycle-reconcile-result-return`, and `governed-worker-cycle-advance`. They must fail closed, not fall back to local release sources or an unsigned approval.

**New check:** `make cf10-make-surface-policy-check`. **New notice:** `make cf10-make-surface-notice`. These do not grant dispatch, launch, closeout, renewal, signing or publication authority.

**Input changes:** `CF10_ACCEPTANCE_REQUEST` and `CF10_ZERO_DELTA_PROOF` now require explicit paths. Do not point them to deleted scratch records; historical proof remains immutable and may require independent rebind. Old source-level validators and non-Make direct entrypoints may still use scratch paths internally and require separate transitive inventory. A clear, reviewable result is mandatory before any workspace cleanup.

**Operator decisions not made by Q1:** Whether generated records are sufficiently retained for audit, release checkout provisioning, writer coverage re-attestation, Root-owned signature production, source/head freeze, and final A049 launch. This is **not** a Go-live approval.

**Original Git base:** `f23adc29a6f781ac56b37abe8288765717147168`.
