# Standards and method basis

This master package is a pragmatic ForPrint method. It does **not** claim formal compliance or certification.

It borrows useful concepts from:

- **ISO/IEC/IEEE 29148:2018 — Requirements engineering**: lifecycle information items, requirement-like records and traceability.
- **ISO/IEC/IEEE 42010:2022 — Architecture description**: separating architecture concerns/views from the system itself and keeping architectural relationships explicit.
- **W3C PROV-O / PROV-DM**: provenance entities, activities, agents, derivation/revision, generation/invalidation and time-qualified provenance.
- **OMG ReqIF 1.2**: portable exchange of requirements-like objects and their relationships between tools/organizations.
- **JSON Schema 2020-12**: machine-validatable structured interchange.
- **Git's content-addressed immutable object model**: immutable source packages are hashed; derived indexes can be rebuilt from them.
- **Event-sourcing pattern**: keep immutable historical events/source facts and derive current projections instead of overwriting history.

## Applied design rules

1. **Lossless source layer** — every per-dialogue DFTB package is preserved unchanged, plus its hash.
2. **Derived global layer** — chronology, indexes, concept chains, conflict clusters and audit backlog can be regenerated.
3. **Three truth layers remain separate**:
   - A: dialogue evidence;
   - B: normalized historical interpretation;
   - C: current implementation verification.
4. **No silent overwrite** — later decisions refine/supersede earlier ones through relations; historical IDs remain.
5. **Partial temporal order** — ambiguous/overlapping exports are marked instead of forcing invented timestamps.
6. **Current-state claims require current baseline** — historical PASS/READY filenames never equal current proof.
7. **Human + machine views** — machine YAML indexes are paired with concise human reading files.
