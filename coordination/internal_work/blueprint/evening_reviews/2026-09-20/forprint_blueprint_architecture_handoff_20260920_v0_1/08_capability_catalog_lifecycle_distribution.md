# Reusable Capability Lifecycle, Catalog & Distribution

## Strategic goal

Build a memory of implementations and a controlled mechanism for project-wide reuse without copying arbitrary code between modules.

## Lifecycle model

Candidate lifecycle vocabulary:

- `EXPERIMENTAL`
- `ACTIVE`
- `STABLE`
- `DEPRECATED`
- `SUPERSEDED`
- `ARCHIVED`

Deprecated/superseded implementations should remain discoverable even when removed from the active runtime tree.

## Reuse safety classification

Possible future statuses:

- `DIRECT_REUSE_ALLOWED`
- `ADAPT_REVIEW_REQUIRED`
- `MIGRATION_REQUIRED`
- `REFERENCE_ONLY`
- `SECURITY_REVALIDATION_REQUIRED`
- `DO_NOT_REUSE`

## Do not turn active source into a museum

Distinguish discoverability from active source placement. Old implementations may be represented by immutable archival records, release artifacts, commits, metadata, and known limitations without keeping every legacy variant in active source directories.

## Capability Catalog

Desired metadata:

- stable capability ID;
- owner module;
- lifecycle;
- current/relevant versions;
- implementation location/artifact;
- provided behavior/contract;
- consumers/subscribers;
- compatibility/migration information;
- supersession/lineage;
- release manifests;
- provenance/evidence.

`ForPrint Library` is a plausible host for the catalog/discovery surface because of its catalog semantics, but repository audit must confirm whether this extends or violates its current canonical boundaries.

## Release Manifest

A capability owner publishes a machine-readable manifest describing:

- old/new version;
- added/changed/removed behavior;
- compatibility/breaking status;
- migration requirement;
- recommended/known consumers;
- release/change class.

## Publication model

Capability publication is **notification-and-review driven, not forced-upgrade driven**.

Every relevant consumer should explicitly review each applicable release and record one decision, e.g.:

- `ADOPT_NOW`
- `ADOPT_PLANNED`
- `STAY_PINNED`
- `NOT_APPLICABLE`
- `BLOCKED_BY_COMPATIBILITY`
- `REQUIRES_ARCHITECTURE_REVIEW`

## Inspector role

Inspector should reconcile:

- latest catalog revision vs reviewed consumer revision;
- unreviewed releases;
- deprecated/superseded capability still in use;
- undeclared/inferred consumers;
- unsupported/stale versions;
- critical updates lacking review.

Inspector should not force all consumers onto the newest version.

## Planner integration

An `ADOPT_PLANNED` decision becomes planning input/candidate work, not immediate execution authority.

## Versioning

Prefer a standard immutable versioning discipline (e.g. SemVer semantics where applicable) rather than inventing ad-hoc version formats.
