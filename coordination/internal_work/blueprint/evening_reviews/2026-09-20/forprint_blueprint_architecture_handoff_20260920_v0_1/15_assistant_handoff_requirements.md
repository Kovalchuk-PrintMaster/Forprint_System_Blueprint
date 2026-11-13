# Assistant Handoff Requirements

Any future assistant working on this architecture should be told explicitly:

1. **Coverage first, ordering later.** Current H numbering is not guaranteed to be final execution sequence.
2. **Do not create duplicate control planes.** Audit existing Blueprint mechanisms before implementation.
3. **Reuse-first is mandatory for architectural capabilities.** Use `REUSE/EXTEND/ADAPT/REPLACE/NEW`.
4. **Execution profiles are an existing foundation.** Extend/reconcile rather than replace unless audit proves otherwise.
5. **Worker context can be broad; worker execution authority must be narrow and machine-enforced.**
6. **Indexes remain useful.** Graphs complement indexes; C4/UML/BPMN/WBS are views/projections, not new sources of truth.
7. **Publication is separate from execution.** `WORK_COMPLETED != MERGED`.
8. **Publication Control Plane starts inside Blueprint and must be extraction-ready.**
9. **Dispatcher provides execution facts; it is not the final Git promotion authority.**
10. **Capability publication is review-driven, not forced-upgrade driven.**
11. **Old implementations should be lifecycle-managed and discoverable, not casually deleted or left cluttering active source.**
12. **Far-horizon references are not backlog.** They inform future design and must later be selectively promoted through governance.
13. **Multi-mutation-worker parallelism per module is far horizon and low priority until the architecture stabilizes.**
14. **Formal Blueprint intake/governance is authority.** Chat transcripts/packages are planning context until formally accepted.
15. **One bounded engineering step per turn/work item.** Preserve unrelated dirty state; do not bulk stage.

## Temporary work/report convention to preserve

Prefer one repository-root `tmp.py` overwritten per bounded step and one report directory per major workstream:

```text
tmp/assistant_work/<workstream_id>/
```

with monotonically numbered reports, e.g.:

```text
0101__initial_audit.txt
0102__reuse_matrix.txt
0103__repair_result.txt
```

Do not create a new temporary directory for every minor audit.
