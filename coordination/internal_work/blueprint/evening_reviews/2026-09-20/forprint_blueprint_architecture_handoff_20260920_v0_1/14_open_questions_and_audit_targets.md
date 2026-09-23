# Open Questions & Repository Audit Targets

These items are deliberately unresolved and must not be silently guessed during integration.

## A. Existing execution-profile model

- What exact schemas/policies/tests already define execution profiles?
- Which permissions are currently modeled as ceilings vs grants?
- Is effective authority intersection already canonical?
- What budget/resource dimensions already exist?
- Where should runtime sandbox enforcement connect without duplication?

## B. Worker runtime / sandbox

- What worker runtime/console adapter already exists?
- Is task-worktree isolation already partially implemented?
- Which shell/network/secrets restrictions exist today?
- What can be enforced immediately on the current Debian/server environment?

## C. Reuse/novelty gate

- Where is the existing `REUSE/EXTEND/ADAPT/REPLACE/NEW` model defined?
- Is `NEW_REQUIRES_RATIONALE` already enforced or only documented?
- What lifecycle transition is the correct hard gate for reuse assessment?

## D. Graph/index foundations

- Which current dependency/index generators already provide part of the desired implementation graph?
- Which indexes should remain independent derived surfaces vs become graph-derived?
- What stable entity ID conventions already exist?
- Which semantic structure validators can be extended?

## E. Project Inspector

- Is Project Inspector canonical for cross-project read-only architecture/deprecation/reuse audits?
- What boundaries must remain read-only?
- Which new checks are `EXTEND` vs a new hosted capability?

## F. Library

- Can Library legitimately host capability catalog/discovery metadata?
- Does that conflict with its current ownership of catalog semantics?
- Should code/artifact registry metadata remain separate even if Library is the discovery surface?

## G. Publication / Git

- What current repository governance defines commit/push approval?
- Which existing rules assume commit+push after every successful step?
- Which rules require explicit operator approval?
- Are there semantic contradictions that must be resolved before canonical publication policy is changed?
- What current branch protection / provider capabilities exist?

## H. Legacy `wave` semantics

Perform semantic inventory of all `wave` references.

Do not blindly rename.

Classify each usage as:

- old planning batch;
- execution grouping;
- publication grouping;
- compatibility-only terminology;
- obsolete concept.

Expected migration targets may include:

- Strategic Horizon;
- Near-Horizon Candidate Chain;
- Execution Frontier;
- Execution Lease;
- Promotion Milestone.

## I. Promotion Controller extraction triggers

The hosted capability may become a standalone service later if several conditions emerge, such as:

- independent long-running runtime;
- own persistent state;
- independent high-value credentials/security boundary;
- high cross-repository throughput;
- external consumers of its API;
- provider/release logic becoming substantial.

Exact extraction policy remains future work.

## J. Capability lifecycle archive

- Where should immutable archived implementation records/artifacts live?
- What minimum metadata proves lineage, known limitations, compatibility, and reuse safety?
- How should code snapshots relate to Git commit history vs separate package/artifact storage?

## K. Portfolio model

- Which current roadmap fields become canonical graph properties vs compatibility imports?
- How will confidence/provenance for synthetic gaps/hypotheses be represented?
- What exact boundary separates desired planning state from derived projections?

## L. Multi-worker future

No near-term implementation required.

Later investigate:

- safe-parallelism assessment;
- semantic mutation reservations;
- integration cost measurement;
- optimal concurrency from actual history.
