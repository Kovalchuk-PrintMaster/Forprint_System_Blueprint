# ForPrint Project Cleanliness & Machine-Surface Normalization Standard v0.1

Status: `CURRENT_NORMATIVE`
Authority: `Blueprint governance standard`
Owner: `forprint_system_blueprint`
Conformance auditor: `forprint_project_inspector`

## 1. Core invariant

Project cleanliness is a permanent architecture objective, not a one-time cleanup task.

A ForPrint repository must remain understandable to humans and machines without accumulating a
"zoo" of equivalent document formats, duplicate rules, ad-hoc generated files, unowned temporary
artifacts or hidden alternative sources of truth.

Cleanliness is part of correctness.

## 2. Scope

The cleanliness program covers at least:

- document and machine-surface structure;
- canonical/generated/derived/historical/internal-work classification;
- filenames and directory placement;
- schema/version metadata;
- generator/source relationships;
- validators and check commands;
- duplicate capability and duplicate semantic surfaces;
- orphan/current documents;
- generated-file drift and direct manual editing;
- temporary/backup/root clutter;
- reusable helper duplication;
- stale configuration and stale compatibility surfaces;
- uncontrolled new document formats.

## 3. One class — one profile

Every recurring current document/machine-surface class must have a registered profile.

The profile defines:

- `document_type`;
- intended authority class;
- canonical source pattern;
- generated/derived relationship when applicable;
- required metadata;
- filename/path pattern;
- lifecycle;
- mutation method;
- validator/check;
- migration state.

Two files may contain different business meaning while still using the same structural profile.

## 4. Canonical vs generated

Generated/derived artifacts are projections, not authoring surfaces.

If a generated document is wrong:

1. locate its canonical source;
2. change the canonical source;
3. run the registered generator;
4. run the registered drift validator.

Directly editing a generated artifact is prohibited unless an explicit recovery procedure says otherwise.

## 5. Legacy debt rule

Existing legacy structure may be retained temporarily only when it is recorded in the active
normalization baseline/debt register.

The baseline is not permission to create more debt.

After a class is migrated to strict status, new or modified current surfaces in that class must
conform to the current registered profile.

## 6. Semantic-preservation rule

Normalization must preserve business/architectural meaning.

Migration should change structure, metadata, naming, generator boundaries or placement without
silently rewriting domain intent.

Where structural normalization exposes semantic conflicts, stop and route the conflict to the semantic owner.

## 7. Safe mutation

Repeated complex surface types should receive shared mutation helpers instead of one-off parsing
logic in every temporary script.

Priority helpers include:

- append Human Intent;
- update module policy canonical source;
- create/register a module;
- add/update roadmap step;
- register standard/contract;
- regenerate derived indexes/projections.

## 8. Inspector responsibility

Project Inspector audits cleanliness in Blueprint and other ForPrint repositories.

Inspector may detect/report:

- schema/profile drift;
- manual edits to generated surfaces;
- unregistered document types;
- duplicate capabilities/technical helpers;
- duplicate semantic definitions;
- orphan current documents;
- stale compatibility/deprecated surfaces;
- naming/folder deviations;
- temp/backup artifacts in production trees;
- missing generator/check relationships.

Inspector does not become semantic owner of the affected module. It reports evidence and routes the
finding to the responsible owner/Blueprint.

## 9. Enforcement progression

Phase A — registry + baseline debt.
Phase B — migrate machine-active classes one by one.
Phase C — strict checks for migrated classes.
Phase D — extend the same cleanliness pack to every module repository.
Phase E — continuous cleanliness score/debt review.

## 10. No-zoo rule

A new current document structure or machine-surface class is not created casually.

Before introducing one:

1. search the Document Type Registry;
2. reuse an existing profile if semantically suitable;
3. if no profile fits, propose a new type with owner, lifecycle, canonical source and validator;
4. register it before broad use.

## 11. Completion evidence

A normalization batch is complete only when:

- semantic preservation is demonstrated;
- generated drift checks pass;
- registry/debt state is updated;
- indexes regenerate cleanly;
- relevant validators pass;
- no H10/runtime/acceptance authority is widened implicitly.

<!-- cross-module-cleanliness-conformance-2026-09-01:start -->
## 12. Cross-module repository cleanliness conformance

This standard is the single project-wide cleanliness policy for every current ForPrint module
repository. Modules MUST NOT invent parallel global cleanliness standards.

Each module owns the cleanliness of its own repository. Blueprint owns the canonical policy,
portfolio conformance state and shared structural rules. Project Inspector audits conformance
across repositories but does not become owner of the audited module's business semantics.

Every module repository must eventually provide a local cleanliness pack covering at least:

- canonical/generated/derived/historical/internal-work classification;
- local document/surface profile mapping to the project standard;
- canonical-source and generator relationships;
- generated drift checks;
- validator/check registry or equivalent discoverable check surface;
- legacy/debt baseline for known non-conforming current surfaces;
- orphan/current document detection;
- temporary/backup/root clutter control;
- duplicate helper/capability/semantic-surface detection;
- filename/path and schema/version conformance;
- safe mutation path for recurring structured surfaces;
- one normal module-level check command that includes cleanliness conformance.

A module-local rule may extend this standard for domain-specific needs, but it may not redefine
project-wide classifications, lifecycle meanings or cleanliness ownership.

### Current implementation status

`forprint_system_blueprint` local automated cleanliness control is **IMPLEMENTED** and evidenced by:

- `coordination/standards/governance/document_type_registry_v0_1.yaml`;
- `scripts/validation/validate_document_surface_registry_v0_1.py`;
- `make surface-normalization-check`;
- the active normalization baseline/debt count;
- generated module-policy drift checking;
- `make check`.

Cross-repository Inspector cleanliness automation is **PLANNED / NOT YET IMPLEMENTED**.

Module-local cleanliness packs for other module repositories are **REQUIRED / PLANNED** and must be
planned before assistant distribution, then implemented under the normal module execution gates.

### Distribution and readiness rule

Assistant distribution does not itself authorize implementation.

Before future work is distributed to a canonical module, Blueprint must know that module's
cleanliness-conformance state and roadmap. Before implementation maturity is declared, the module
must provide evidence that its local cleanliness pack is operational or an explicitly accepted
temporary debt plan exists.

This requirement is a portfolio readiness condition, not a new semantic ownership layer.
<!-- cross-module-cleanliness-conformance-2026-09-01:end -->
