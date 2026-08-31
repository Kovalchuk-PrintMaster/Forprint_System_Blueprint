# ForPrint Portfolio Rendering and Content Specification v0.1

Status: active_standard
Scope: internal portfolio review projection
Authority: ForPrint System Blueprint
Date: 2026-08-31

## Purpose

Define a reproducible, stable visual/content contract for the expanded ForPrint portfolio.
The PDF is a human review projection, not release authority. Canonical authority remains in
structured Blueprint governance, contracts, roadmaps, Human Intent ledgers and evidence.

## Required portfolio layers

The expanded portfolio MUST preserve three kinds of information together:

1. Technical header / balanced portfolio view.
2. Full-horizon roadmap view.
3. Human Intent context grouped against roadmap steps.

A regenerated portfolio MUST NOT collapse many active Human Intent entries into one generic
paragraph.

## Per-module section order

Each module section SHOULD contain, in this order:

1. module display name + canonical module_id;
2. priority;
3. current portfolio state / confidence;
4. role in ecosystem;
5. current step / next checkpoint;
6. blocker for the next integration stage;
7. dependencies;
8. downstream capabilities/modules unlocked;
9. canonical ownership boundary;
10. target/end state;
11. full-horizon roadmap;
12. Human Intent entries grouped by roadmap step;
13. visible PROPOSED / SYNTHETIC / GAP review items;
14. review notes area.

## Full-horizon roadmap rule

The portfolio SHOULD show a rough route from the current step to the target state even when
later steps are not yet fully discussed.

Synthetic future steps are allowed and useful. They MUST be explicitly marked and MUST NOT be
presented as release authority, approved business rules or implementation commitments.

Recommended maturity labels:

- AGREED — explicit human/Blueprint agreement exists.
- RECOVERED — recovered from prior project evidence.
- PROPOSED — concrete proposal requiring review.
- SYNTHETIC — future projection created to make the route visible.
- GAP — known unresolved detail; do not invent a replacement.

Synthetic roadmap rows SHOULD also carry:

- confidence: LOW | MEDIUM | HIGH;
- evidence_basis;
- needs_review: true.

Synthetic content SHOULD be visually distinct. The current preferred review palette is:

- AGREED: green;
- RECOVERED: warm yellow/beige;
- PROPOSED / SYNTHETIC: pink/powder;
- GAP / UNKNOWN: gray or muted red.

Color alone MUST NOT carry meaning; the text label must remain visible.

## Human Intent grouping

Human Intent entries MUST be grouped under the roadmap step they explain whenever a useful
association exists.

Each visible entry SHOULD retain:

- intent_id;
- status;
- human-readable text;
- context/excerpt;
- roadmap reference when known.

Older intent MUST NOT be deleted merely because a later decision supersedes it. Supersession
must remain traceable.

## Layout safety

A4 portrait is the default review format.

- minimum safe left/right page margin: 5 mm;
- preferred left/right margin: 12 mm;
- no text or table may cross the printable page boundary;
- long identifiers must wrap;
- tables must not force text outside the right page edge;
- page numbers are required;
- module boundaries must remain obvious.

The 2026-08-30 comprehensive portfolio used 12 mm side margins specifically to eliminate the
previous right-edge clipping defect.

## Portfolio history policy

Generated review PDFs are small internal artifacts and SHOULD be retained historically in the
Blueprint project.

Rules:

- never overwrite an older portfolio PDF;
- use date + semantic version in filenames;
- preserve the PDF even when it is no longer current;
- preserve the source representation when available;
- keep a current rendering specification so the visual structure can be reproduced;
- the PDF is a projection/history artifact, not the canonical source of module state.

Recommended location:

`coordination/internal_work/blueprint/portfolio_reviews/history/`

## Regeneration principle

A future generator should be able to reproduce the same recognizable structure from structured
project state plus this specification without depending on one assistant's memory.

The generator may improve typography, spacing or pagination, but changes to the required
content blocks, status semantics or history policy require an explicit standard revision.

<!-- portfolio-rendering-v0-1-residual-closure-2026-08-31:start -->
## Recovered reproducible rendering baseline — 2026-08-31 closure

The following details are recovered from the accepted v1.0 evening-review rendering
specification and are part of the reproducible baseline for this revision.

### Page geometry and typography

- Minimum safe margin: never less than 5 mm.
- Preferred reproducible margins:
  - left: 12 mm;
  - right: 12 mm;
  - top: 11 mm;
  - bottom: 12 mm.
- No text clipping on the right edge.
- Tables must fit within printable width.
- Header/footer must not reduce usable body width below the safe area.
- Page number is rendered in the footer.
- Unicode-capable sans-serif font is required; the working baseline is
  **Liberation Sans** or a metrically safe Unicode-capable equivalent.

### Recovered status palette

- main blue heading: `#2E4F88`
- light blue structural cells: `#DDE8F7`
- AGREED / confirmed: `#D9E4D2`
- RECOVERED / present in project evidence: `#F2E7BD`
- SYNTHETIC / PROPOSED: `#E8C9CC`
- GAP / unknown: `#E1E1E1`
- blocker / attention when needed: `#E9C7C7`

Synthetic material remains useful and visible; it must not be visually presented as
confirmed implementation.

### Evidence and status discipline

If exact runtime/module status cannot be proven from current evidence, render the
literal label **`status sync needed`** and do not invent an implementation percentage
or exact current step.

### Render and history acceptance

Before a portfolio projection is accepted:

- long IDs must wrap without clipping;
- proposed module candidates remain visibly marked;
- the output must open and be render-checked across all pages;
- the PDF SHA-256 must be recorded in portfolio metadata when the projection is
  retained/committed;
- generation baseline / source refs must be recorded;
- the rendering/content specification revision used must be recorded.

### Deterministic generator

The repository-local generator is:

`python scripts/portfolio/render_human_intent_portfolio.py`

It consumes the Human Intent index and append-only module ledgers. It must fail if the
generated source does not contain every indexed intent ID exactly once. The generated
PDF remains a human review projection, never architecture/release authority.
<!-- portfolio-rendering-v0-1-residual-closure-2026-08-31:end -->
