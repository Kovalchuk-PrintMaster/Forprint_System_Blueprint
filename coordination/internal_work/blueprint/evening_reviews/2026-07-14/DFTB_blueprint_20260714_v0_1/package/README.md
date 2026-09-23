# DFTB Bundle — blueprint-2026-07-14

Mandatory outputs:
- `dialogue_memory.yaml` — 47 normalized machine items.
- `evidence_portfolio.md` — 41 evidence excerpts with stable IDs.
- `session_digest.md` — compressed human context.

Additional:
- `verification_queue.yaml`
- `implementation_audit.stub.yaml`
- `traceability_matrix.md`
- `ANOMALIES.md`
- `SOURCE_COVERAGE.md`
- `visible_transcript.md`
- `source_manifest.yaml`

Critical source limitation: only **133/877** turn containers retain message text.

Safe chain: historical evidence -> normalized item -> current implementation audit -> current authority reconciliation -> roadmap/ADR/task.
