# Anomalies & Open Loops

## Anomalies

### ANOM-PRE2706-0001 — new_unique_cross_module_source (normal)
No shared message IDs or meaningful normalized text overlap with previous loaded sources. This is a distinct Prepress history layer.

### ANOM-PRE2706-0002 — partial_conversation_capture (high)
Visible turns are 1,2,6,7,8,9,10; turns 3–5 are absent. Missing content is not reconstructed.

### ANOM-PRE2706-0003 — early_hub_architecture_narrowed_to_capability_discovery (high)
Earlier CRM source proposed broad Prepress Hub architecture; here owner explicitly narrows the immediate phase to practical capability discovery and product-specific tooling before integration design.

### ANOM-PRE2706-0004 — pdf_normalization_policy_may_not_be_universal (normal)
Owner states a working policy of converging outputs to PDF, but current module contracts may preserve non-PDF intermediates; treat as historical working policy, not absolute architecture law.

### ANOM-PRE2706-0005 — quality_thresholds_are_examples_not_final_constants (high)
25 DPI and 3–5% distortion appear as owner examples/configurable values, not necessarily final production thresholds.

### ANOM-PRE2706-0006 — raster_text_k_only_is_inherently_heuristic (critical)
K-only conversion for thin text in raster files risks altering dark image/design elements; requires confidence/safety gating and manual fallback.

### ANOM-PRE2706-0007 — assistant_unix_coverage_estimate_not_measured (normal)
The 80–90% Unix-native coverage statement is an assistant estimate, not measured project evidence.

## Open loops

### LOOP-PRE2706-0001
Verify current Prepress assistant decomposition and Shared Prepress Tools boundary.
**Last known:** Historical policy favors product-specific assistants + shared fact-oriented tools.
**Verify:** Inspect current Prepress/assistant repos and contracts; detect duplicated file-inspection logic or shared layer scope creep.

### LOOP-PRE2706-0002
Verify current Unix-first vs Windows Photoshop Station execution model.
**Last known:** Historical design keeps deterministic raster work on Unix and Photoshop-specific quality tasks on a bounded Windows agent.
**Verify:** Audit current runtime/deployment/adapters; verify whether station job contract exists or has been superseded.

### LOOP-PRE2706-0003
Resolve actual production thresholds for effective DPI and allowed aspect distortion.
**Last known:** Historical examples mention ~25 DPI minimum and 3–5% auto-distortion but explicitly treat them as configurable.
**Verify:** Find current Library/Prepress policy/config and acceptance criteria; never hardcode historical examples.

### LOOP-PRE2706-0004
Verify multi-candidate processing/risk comparison and preview/report contract.
**Last known:** Historical design proposes 2–3 understandable candidates with risk/confidence and previews.
**Verify:** Inspect current workflow/contracts/UI and determine whether candidate comparison is implemented, deferred or replaced.

### LOOP-PRE2706-0005
Verify raster bleed strategies and edge-risk detection against real files.
**Last known:** Historical candidates include preserve edge, crop-before-bleed, mirror and Photoshop content-aware.
**Verify:** Use controlled fixture corpus and visual acceptance tests; ensure crop/content-aware paths preserve important content.

### LOOP-PRE2706-0006
Verify safe K-only enhancement policy for raster artwork.
**Last known:** Historical proposal allows only heuristic candidate generation with manual fallback.
**Verify:** Require current color-management/print policy plus representative fixtures before enabling automatic modifications.
