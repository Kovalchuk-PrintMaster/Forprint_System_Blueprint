# Anomalies & Open Loops

## Anomalies

### ANOM-PRE2005-0001 — new_unique_prepress_source (normal)
No shared message IDs or meaningful normalized text overlap with previously loaded sources. Distinct early Prepress bootstrap history.

### ANOM-PRE2005-0002 — missing_attached_prior_agreements (critical)
Owner references attached `prepress_hub.docx` / prior agreements, but attachment body is not visible. Assistant's restatement is secondary evidence only.

### ANOM-PRE2005-0003 — proposal_code_without_execution_proof (critical)
Large concrete scaffold/code is present, but there is no evidence it was written, installed, tested, run or committed.

### ANOM-PRE2005-0004 — absolute_path_drift (high)
Historical settings hard-code `/srv/software_development/forprint-project/forprint_prepress_hub`, while later Blueprint governance prefers project-relative/portable paths.

### ANOM-PRE2005-0005 — local_service_all_interfaces_bind (high)
Proposed local development server binds `0.0.0.0` with reload, which may expose a development service more broadly than intended.

### ANOM-PRE2005-0006 — later_scope_refinement (high)
May source begins by scaffolding a broad local Hub; 27.06 owner direction later narrows immediate work to capability discovery/product-specific assistants and Unix-first practical tooling before broader integration.

## Open loops

### LOOP-PRE2005-0001
Determine whether the May zero-platform scaffold was ever implemented or superseded before implementation.
**Last known:** Only proposed code/config/tests are visible; no execution or Git evidence.
**Verify:** Inspect current and historical Prepress Git history/files; classify each scaffold element as implemented, moved, superseded or never applied.

### LOOP-PRE2005-0002
Recover or supersede the missing `prepress_hub.docx` agreements.
**Last known:** Attachment is referenced but body absent from MHTML.
**Verify:** Prefer later direct owner Prepress evidence/current authority; recover attachment only if historical provenance is needed.

### LOOP-PRE2005-0003
Verify current Prepress runtime binding/security policy.
**Last known:** Historical proposed dev command uses `0.0.0.0:8020 --reload`.
**Verify:** Inspect current deployment/listen configuration; ensure local-only/dev behavior follows current security policy.

### LOOP-PRE2005-0004
Verify current Prepress path/config portability.
**Last known:** Historical scaffold hard-codes an absolute server path.
**Verify:** Audit current config for project-relative/root-discovery behavior and remove machine-specific defaults if still active.

### LOOP-PRE2005-0005
Verify original-input immutability in current processing pipeline.
**Last known:** Historical next-step explicitly copies input into isolated job workspace and does not touch original.
**Verify:** Audit current job runner/file handling and tests for immutable-source behavior.
