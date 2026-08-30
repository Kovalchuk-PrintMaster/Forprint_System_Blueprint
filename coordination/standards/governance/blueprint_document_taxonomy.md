# Blueprint Document Taxonomy and Placement Policy

## Purpose

This policy defines where current Blueprint information belongs so paths remain
predictable and different lifecycle classes do not look equally authoritative.

## Current placement

- `machine/` — current machine-readable architecture/control truth only.
- `docs/architecture/` — stable human explanations of architecture.
- `docs/operations/` — operator/developer operational guidance and recovery/runbooks.
- `coordination/releases/` — effective release projection and release evidence.
- `coordination/roadmaps/` — current/detailed planning.
- `coordination/standards/` — normative standards and policies.
- `coordination/internal_work/` — bounded analysis, migration evidence and history.
- `reports/` — generated reports/evidence; not authority merely because a path says current.
- `indexes/` — derived non-authoritative navigation.
- `adr/` — durable decision history.
- `diagrams/` — generated or explicitly maintained explanatory diagrams.

## One concept, one authority

A concept may have multiple representations only when their roles are explicit.

Preferred model:

```text
canonical source
  -> human explanation
  -> generated/derived view
  -> historical snapshots/evidence
```

A copied document must not silently become a second manually editable authority.

## Legacy `human/`

Top-level `human/` is retired.

Historical files formerly stored there are preserved under:

`coordination/internal_work/blueprint/legacy_alignment/`

Current human-readable architecture belongs in `docs/`.

No new file may be introduced under top-level `human/`.

## Historical references

ADR, released prompts, dated snapshots and historical evidence may contain old paths or
old identifiers. They are not rewritten merely for cosmetic consistency.

When a historical artifact has been relocated, its archive index must preserve the
original path and content hash.

## Generated/derived copies

When a self-contained distribution package needs a physical copy of canonical content:

- the canonical source is declared;
- the derived destination is declared;
- generation/synchronization is deterministic;
- drift is checked automatically;
- the derived copy does not gain authority.

## Move/merge/delete rule

Do not move or delete content based only on filename or hash similarity.

Before removing a current-looking artifact, determine whether it is:

- current authority;
- explanatory documentation;
- generated/derived;
- immutable/released evidence;
- historical evidence;
- obsolete compatibility surface;
- harmful duplicate.

Structural normalization must preserve required history while removing duplicate current
authority.
