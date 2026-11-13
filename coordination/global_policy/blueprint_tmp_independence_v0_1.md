# ForPrint Blueprint — TMP independence (global invariant)

**Owner decision: 2026-11-01.** Applies to all ForPrint System Blueprint modules, CF stages, canonical Make/CLI workflows, systemd units, Worker Runtime, durable records and recovery.

`tmp/` (including project `tmp/`, `/tmp` and `/var/tmp`) is untrusted disposable space. It can be cleared at any time. Permitted uses: ZIP delivery, preparation, isolated staging, disposable fixtures, regenerable diagnostic exports. **Forbidden:** canonical runtime code or imports, required configuration, ledger, claim/receipt, credentials, state for resume/recovery, running Worker dependencies and only copy of any required production evidence.

Production source code and configuration belong in Git-controlled Blueprint paths. Worker runtime stays under the existing `/srv/software_development/forprint-worker-runtime`, with existing namespaces preferred. A proposed root-owned receipt location under that *existing* runtime is a **candidate**, not an approved new live store or directory-creation command. Do not provision it without separate storage review. Permanent storage must have verified ownership and backup/recovery properties.

Release **fails closed** unless source/loading paths are canonical, durable state paths are authorized, and both fresh-start and reboot/recovery scenarios are tested with `tmp/` deliberately unavailable in **disposable isolation**. Never delete or rename the live server's `tmp/` for testing.

First gate is `make blueprint-tmp-independence-check`. It checks governance and critical runtime path definitions and exercises fail-closed path validation. It is **not** a blanket audit of every source dependency and **does not** by itself authorize a live release; canonical wiring and end-to-end tmp-unavailable tests remain mandatory.

Hestia and independent hosting/mail services are out of scope. Historic `s01` and blocked CF-10 attempt `a049` are unaffected by this governance installation.
