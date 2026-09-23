# Anomalies & Open Loops

## Anomalies

### ANOM-BP0508-0001 — assistant_capture_gap (high)
All 107 retained turns contain text, but only four assistant narrative blocks survive; most execution history is artifacts/pasted command output.

### ANOM-BP0508-0002 — templates_masquerading_as_analysis (critical)
Initial report contained repository-knowledge scaffolding but lacked filled evidence-backed analysis.

### ANOM-BP0508-0003 — index_vs_understanding_gap (critical)
Historical self-knowledge indexed 695/695 files while understanding only 22 and dependency-mapping only four.

### ANOM-BP0508-0004 — command_semantics_confusion (critical)
A mutating sequence was represented as `check`; owner explicitly requests separation and clearer naming.

### ANOM-BP0508-0005 — worktree_identity_confusion (high)
Owner sees duplicates in one view but not another and suspects different copies/worktrees are being processed.

### ANOM-BP0508-0006 — markdown_structural_cleanup_churn (normal)
Long markdown-fence/nested-fence/duplicate review sequence suggests validator blind spots and repeated structural cleanup.

### ANOM-BP0508-0007 — status_surface_asymmetry (high)
Status/prompt/report indexes existed for module audits while owner was unsure equivalent Blueprint self-governance surfaces existed.

### ANOM-BP0508-0008 — validation_vs_authorization_confusion_risk (critical)
Canonical gates can be fully green while pilot authorization remains false and rollout gated.

### ANOM-BP0508-0009 — historical_lineage_not_current_proof (normal)
Readiness/write-flow/contract/transparency artifacts establish chronology but not today's implementation state.

### ANOM-BP0508-0010 — local_tmp_vs_canonical_repo_risk (high)
Active development worktree lived under project tmp, requiring explicit path/branch/HEAD discipline to avoid confusion with disposable artifacts or canonical repo.

## Open loops

### LOOP-BP0508-0001
Verify current Repository Knowledge distinguishes evidence-backed understanding from file indexing.
**Last known:** Initial report rejected; later self-audit had full indexing but low understanding.
**Verify:** Inspect current repository-knowledge schemas/generators and sample claims for evidence/confidence/baseline fields.

### LOOP-BP0508-0002
Verify current Make architecture separates read-only checks from mutating operations.
**Last known:** Owner rejected mutating `check`; later read-only governance status planned.
**Verify:** Audit current Make targets, CLI side effects, docs and tests.

### LOOP-BP0508-0003
Verify module-owned workflow boundaries and Blueprint-owned inspection tooling.
**Last known:** Owner required modules and Blueprint to use their own scripts/architectures.
**Verify:** Inspect current listener/module runtime/completion contracts and Blueprint inspection paths.

### LOOP-BP0508-0004
Verify Blueprint self-status/prompts/reports indexes are canonical.
**Last known:** Owner identified possible asymmetry; transparency layer was next.
**Verify:** Inspect current status manifest/command and prompt/report indexes.

### LOOP-BP0508-0005
Verify readiness/write-flow/validator/exact-contract chain against current implementation.
**Last known:** Dedicated historical review/contract artifacts exist.
**Verify:** Locate current contracts/validators and run canonical gates.

### LOOP-BP0508-0006
Verify canonical mutation-builder contract remains current and rollback is enforced.
**Last known:** Historical commit 9caf511... reported active/canonical and 28/28.
**Verify:** Inspect current standard, validator catalog, tests and execution path.

### LOOP-BP0508-0007
Verify transparency manifest and read-only governance status were completed.
**Last known:** Immediate next bounded steps after mutation-builder integration.
**Verify:** Find current manifest/status command and verify exposed state fields.

### LOOP-BP0508-0008
Verify pilot authorization remained gated until control-layer criteria were satisfied.
**Last known:** Pilot unauthorized; external rollout gated.
**Verify:** Resolve current release/pilot authority and inspect authorization evidence.

### LOOP-BP0508-0009
Verify markdown/document structural cleanup reached a stable end state.
**Last known:** Many bounded fence/duplicate review waves occurred.
**Verify:** Run current document/fence validators and inspect exceptions.

### LOOP-BP0508-0010
Verify zero-context handoff now derives from canonical current state.
**Last known:** Owner requested a hand-written replacement-assistant prompt; later history built stronger continuity tooling.
**Verify:** Inspect current assistant-context/handoff compiler and compare output with current authority.
