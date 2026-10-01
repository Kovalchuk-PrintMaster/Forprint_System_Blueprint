# ForPrint Graphic Design Lab — Blueprint Horizon Package v0.1

## Purpose

This package is a **Prepress-owned planning/request package** for System Blueprint.

It does not activate implementation by itself.

`SYSTEM_BLUEPRINT_ACCESS_FROM_PREPRESS=READ_ONLY_STRICT`

The package asks System Blueprint to:

1. review the proposed GDL development horizon against current ForPrint architecture, ownership, roadmap, Human Intent, existing contracts, and current module state;
2. register the future contours as a governed queue/horizon rather than one monolithic executable prompt;
3. publish only the first executable contour after reconciliation;
4. keep later contours in planned/queued state;
5. before releasing every later contour, reconcile it against the then-current Prepress/GDL state and empirical findings;
6. incorporate approved amendments before converting a planned contour into an executable worker prompt.

## Strategic shift

The immediate priority is **not more scripts for their own sake**.

The priority is to create a disciplined empirical-learning loop around real customer design work:

customer request
→ operator/manager intake dialogue
→ structured questions
→ creator prompt
→ creator result
→ operator/customer outcome
→ empirical case
→ patterns / anti-patterns / failure modes
→ improved future prompts and workflow decisions

The engineering worker should build the repeatable mechanics around this loop.
Human + assistant work should concentrate on real cases, quality observations, customer acceptance, prompt effectiveness, and identifying where Creator, local deterministic tools, or human confirmation perform best.

## First proposed executable contour

`prepress_gdl_creator_empirical_learning_foundation_v0_1`

This first contour should establish a light but governed knowledge-capture and manual experimentation surface. It should support manual operator-facing wizard experiments for simple products such as menus, business cards, and flyers without prematurely building a production runtime.

## Important authority boundary

System Blueprint is strictly read-only from Prepress.

Any Blueprint-side registration, queue mutation, prompt publication, lifecycle transition, or policy update must be performed from Blueprint context.

Prepress may only submit this package and later read the published result.
