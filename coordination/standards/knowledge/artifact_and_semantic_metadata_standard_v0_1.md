# ForPrint Artifact and Semantic Metadata Standard v0.1

## Principle

Do not manually encode facts deterministic tooling can derive reliably.

Metadata preserves semantic meaning, authority and traceability; it should not duplicate the parser.

## Source code

Prefer automatic extraction of path, symbols/classes/functions, signatures, imports/references,
tests, hashes and Git history.

Do not require a semantic record for every private helper.

Create richer semantic records for system-significant/public/reusable capabilities and contracts.

Candidate semantic fields:
- stable capability/document id;
- canonical owner;
- purpose;
- business/design intent;
- public symbol/interface;
- reuse policy;
- authority/status;
- dependency refs;
- design/rationale refs;
- test/evidence refs;
- limitations;
- confidence.

## Markdown/policy/design artifacts

Candidate front matter:
- `document_id`
- `artifact_type`
- `owner`
- `authority`
- `status`
- `created`
- `updated`
- `capability_refs`
- `dependency_refs`
- `supersedes`
- `superseded_by`
- `tags`

Large canonical documents may use stable section anchors/ids for section-level drift detection.

## Structural versus semantic validation

Structural checks can prove required fields, unique ids, existing references and parse validity.
They cannot prove that a description is semantically true.

Keep structural validity distinct from semantic verification.

Do not freeze a large mandatory schema before the first Blueprint inventory shows which fields
actually reduce ambiguity and rework.
