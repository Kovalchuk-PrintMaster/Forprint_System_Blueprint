# Anomalies & Open Loops

## Anomalies

### ANOM-OPREG2905-0001 — new_unique_cross_module_source (normal)
No message IDs overlap any prior loaded source; generic placeholder text is the only superficial textual overlap.

### ANOM-OPREG2905-0002 — attachment_heavy_partial_capture (high)
44 visible message blocks survive, but only four assistant messages contain substantial synthesized state; most intermediate work is represented by pasted attachment placeholders.

### ANOM-OPREG2905-0003 — long_span_filename_label (high)
Filename says 29.05.26, while visible repository files are dated June 8 and active Blueprint prompt/alignment is dated June 19.

### ANOM-OPREG2905-0004 — accounting_vs_operational_truth_boundary (critical)
Bootstrap intentionally separates Operational Registry truth from Accounting/1C truth, but later Blueprint history records ambiguity around Accounting vs Operational Registry naming/ownership. Current authority must reconcile the boundary explicitly.

### ANOM-OPREG2905-0005 — foreign_blueprint_pull_policy (high)
Historical module-start performs `git pull --ff-only` in Blueprint. Later project policy increasingly separates module writes from Blueprint/foreign repos; current allowed freshness mechanism must be verified.

### ANOM-OPREG2905-0006 — stale_packet_during_alignment_checkpoint (normal)
Historical module-validate temporarily checks the old local_launch_readiness packet because the new task-specific packet does not yet exist; this is acceptable only for the isolated alignment checkpoint.

### ANOM-OPREG2905-0007 — prompt_path_drift (high)
Initial outgoing prompt path was wrong and discovery too broad; actual observed June structure used module-specific approved outgoing prompts.

### ANOM-OPREG2905-0008 — timestamp_only_churn_risk (high)
Blueprint explicitly requests idempotent snapshot/completion automation so repeated checks do not dirty Git solely from timestamps.

## Open loops

### LOOP-OPREG2905-0001
Verify current Operational Registry vs Accounting Registry/1C ownership boundary.
**Last known:** Historical bootstrap says Operational Registry owns operational truth while Accounting owns accounting/1C truth; later Blueprint history records naming/ownership ambiguity.
**Verify:** Resolve current release/ADRs/module inventory and assign payment/accounting/client/order facts to one authoritative owner each.

### LOOP-OPREG2905-0002
Verify current data-foundation policy implementation and whether policy docs remain authoritative.
**Last known:** Historical files include master data, operational fact, event log, projections, external refs, raw/normalized values, 1C boundary and entity cards.
**Verify:** Audit live schemas/code/docs and classify each historical policy as current, superseded, or archival.

### LOOP-OPREG2905-0003
Verify current make-first prompt discovery/sync topology and foreign Blueprint freshness mechanism.
**Last known:** Historical June alignment uses outgoing_prompts/<module>/approved and Blueprint pull.
**Verify:** Resolve current prompt resolver/module-start policy before using historical paths or pull behavior.

### LOOP-OPREG2905-0004
Verify snapshot and completion automation is idempotent with no timestamp-only churn.
**Last known:** Explicit Blueprint clarification requires this behavior.
**Verify:** Run repeated current sync/completion generation and compare hashes/git diff.

### LOOP-OPREG2905-0005
Verify `make check` remains non-mutating and alignment gate still composes correct validators.
**Last known:** Historical corrected Makefile uses `check: lint test`; alignment reports 232 passed.
**Verify:** Inspect current Makefile and controlled mutation tests.

### LOOP-OPREG2905-0006
Verify task-specific completion packet replaced the temporary old packet and main readiness task reached proper completion/review state.
**Last known:** Alignment checkpoint intentionally used old packet; main task packet was only a future target.
**Verify:** Trace current/history for local_operator_command_query_readiness_v0_1 completion packet and Blueprint review/acceptance.

### LOOP-OPREG2905-0007
Verify historical alignment checkpoint `a6ca69f` and its Blueprint report were ingested without conflating alignment with business implementation.
**Last known:** Commit pushed; detailed alignment report prepared for Blueprint.
**Verify:** Check Git ancestry and Blueprint incoming/review records if historical provenance matters.
