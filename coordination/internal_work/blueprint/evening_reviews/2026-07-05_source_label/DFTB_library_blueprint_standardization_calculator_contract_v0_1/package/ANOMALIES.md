# Anomalies & Open Loops

## Anomalies

### ANOM-LIB0507-0001 — new_unique_cross_module_source (normal)
No message IDs overlap prior loaded sources, including the earlier Library 16.05 dialogue. This is a distinct Library history layer.

### ANOM-LIB0507-0002 — partial_attachment_heavy_capture (high)
72 visible message blocks survive, but 66 are user turns and many are attachment placeholders. Most implementation detail between checkpoints is unavailable in visible text.

### ANOM-LIB0507-0003 — long_span_filename_label (high)
Filename says 05.07.26, but visible artifacts extend through Calculator intake 2026-07-27 and completion packet 2026-07-29. Treat filename as source/start label, not endpoint.

### ANOM-LIB0507-0004 — mutating_check_surface (critical)
Intermediate Makefile makes `check` depend on `lint-fix`, conflicting with the later Blueprint read-only check invariant.

### ANOM-LIB0507-0005 — foreign_checkout_mutation_ambiguity (high)
Intermediate `blueprint-pull` mutates the local Blueprint checkout, while the owner later says Blueprint is read/reference-only and explicitly forbids repository operations such as commit/push/restore/clean there. Current policy on local pull must be resolved.

### ANOM-LIB0507-0006 — repo_boundary_correction (critical)
Owner catches ambiguity about whether the final commit could target Blueprint and explicitly reasserts Library-only commit/push ownership.

### ANOM-LIB0507-0007 — ready_for_review_not_accepted (critical)
Final module state is READY_FOR_BLUEPRINT_REVIEW while branch is unmerged and Blueprint acceptance is unset. Green local validation must not be read as acceptance.

### ANOM-LIB0507-0008 — focused_test_count_not_preserved (normal)
Focused validator tests exist, but the final visible log lacks the exact focused-test result line; only the full suite 176-pass evidence is preserved.

### ANOM-LIB0507-0009 — report_check_duplication_concern (normal)
Owner notices repeated checks in reports and questions duplicate evidence, motivating semantic deduplication of reporting surfaces.

## Open loops

### LOOP-LIB0507-0001
Verify current Library Makefile keeps `check` read-only and separates lint-fix/mutation.
**Last known:** Visible intermediate Makefile has `check -> lint-fix -> lint -> test -> check-report`.
**Verify:** Inspect live Makefile and tests; confirm read-only checks cannot mutate source.

### LOOP-LIB0507-0002
Resolve current Blueprint-read policy for Library, especially local `blueprint-pull`.
**Last known:** Intermediate workflow pulls Blueprint locally; owner later states Blueprint is read/reference-only and forbids write/commit/push operations.
**Verify:** Use current Blueprint/module policy to decide whether pull/fetch is allowed and make foreign-repo mutation boundaries explicit.

### LOOP-LIB0507-0003
Verify Calculator Input Contract implementation/completion/governance-fix lineage and Blueprint acceptance.
**Last known:** Historical final state READY_FOR_BLUEPRINT_REVIEW; branch unmerged; accepted_by_blueprint unset.
**Verify:** Resolve current Library git history plus Blueprint intake/acceptance records; do not infer acceptance from local green state.

### LOOP-LIB0507-0004
Verify completion packet validator uses explicit packet identity and remains idempotent.
**Last known:** Historical governance fix adds validator/Make PACKET target and reports two no-op idempotent applies.
**Verify:** Run current focused validator/idempotency tests against current completion packet schema.

### LOOP-LIB0507-0005
Verify repository structure rules are captured in durable current policy.
**Last known:** Owner establishes thematic grouping and generally one-level nesting for new high-volume areas.
**Verify:** Inspect current Library/Blueprint structure standards and confirm this historical module-local rule is still applicable.

### LOOP-LIB0507-0006
Recover or supersede missing Blueprint working-rules attachment from turn 151.
**Last known:** Attachment body is absent from MHTML.
**Verify:** Prefer current module policy/AGENTS/release authority; only recover old attachment if historical provenance is specifically needed.

### LOOP-LIB0507-0007
Verify reporting pipeline deduplicates semantically identical checks without hiding distinct evidence classes.
**Last known:** Owner flags repeated checks as potentially redundant.
**Verify:** Audit current check-report generation and classify each repeated check by unique evidence purpose.
