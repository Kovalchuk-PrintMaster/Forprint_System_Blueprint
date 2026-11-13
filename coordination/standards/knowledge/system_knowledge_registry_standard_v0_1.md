# ForPrint System Knowledge Registry Standard v0.1

## Purpose

ForPrint must maintain a recoverable, searchable model of what the system contains, what important
artifacts mean, where authoritative information lives, why major capabilities exist, how components
depend on one another, and what remains unknown.

This is broader than documentation inventory. It is the project self-knowledge layer.

## Questions the system should answer

- What exists?
- What does it do?
- Why was it introduced?
- Where is it?
- When did it appear or materially change?
- Who owns the capability or semantic truth?
- Who consumes it?
- What does it depend on?
- Is it canonical/current/generated/legacy/deprecated/inferred/unknown?
- How may it be reused correctly?
- Which decision/roadmap/evidence explains it?
- Which knowledge is stale, conflicting or unresolved?

## Canonical truth and projections

Canonical governance and project knowledge remains Git-readable and reviewable in governed
Markdown/YAML or equivalent repository artifacts.

Generated indexes may later use SQLite, FTS or another derived store for fast lookup, joins,
dependency traversal, dashboards and search.

A generated database is a rebuildable projection/cache. It must not silently become an independently
mutable second authority.

This standard does not activate live SQLite.

## Target knowledge surfaces

1. System Knowledge Index.
2. Module Registry.
3. Capability Registry.
4. Symbol/Artifact Index.
5. Standards Registry.
6. Dependency/Execution Map.
7. History/Rationale/Decision Index.
8. Knowledge-health/unresolved queue.
9. Structured lookup.
10. Full-text search.
11. Semantic/vector retrieval later when justified by real search evidence.

## Retrieval order

Prefer the least ambiguous mechanism:
1. structured exact registry;
2. symbol/reference lookup;
3. lexical/full-text search;
4. semantic/vector retrieval.

**RAG discovers; authoritative registry decides.**

## Deterministic versus semantic knowledge

Do not manually maintain facts that deterministic tooling can reliably derive.

Machine-derived candidates include paths, file types, hashes, symbols, signatures, classes,
imports/references where detectable, headings, Make targets and Git history.

Semantic knowledge includes purpose, business/design intent, canonical owner, reusable capability
meaning, rationale, authority/lifecycle, intended use, limitations and dependency meaning.

Maintain a complete machine symbol inventory, but richer semantic records only for
system-significant/public/contractual/reusable capabilities rather than every private helper.

## Reuse

Before non-trivial implementation, executors should be able to discover whether similar capability
already exists and how it may be reused.

Finding code in another repository does not authorize copying or runtime use. Governed reuse may be
through a published contract/API, shared package, service interface, or explicit reimplementation
decision.

## Knowledge completeness

Knowledge completeness is maintained, not completed.

**Unknown is acceptable. Invisible unknown is not.**

Unknown/stale/conflicting knowledge must be visible and triageable.

Health is risk-weighted. One unknown canonical standard can matter more than one hundred old reports.

## Module model

Each module maintains its local semantic knowledge under central Blueprint standards.
Blueprint maintains the system/portfolio view.

Modules may read published knowledge from one another and submit dependency/improvement advisories;
reading does not grant authority over another module.

## Improvement loop

When manual reconciliation repeatedly finds the same gap class, record the pattern and decide
whether deterministic tooling can detect it next time. Improve the collector/Inspector where
justified so manual work falls over time.
