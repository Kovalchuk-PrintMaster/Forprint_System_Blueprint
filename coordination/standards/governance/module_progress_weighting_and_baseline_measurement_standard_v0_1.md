# Module Progress Weighting and Baseline Measurement Standard v0.1

## Purpose

Provide a simple, transparent progress measure without pretending that every roadmap item has equal
difficulty or that early estimates are perfectly objective.

## Work weight

Each roadmap outcome receives an estimated work weight.

A possible starting scale:

- `tiny = 1`
- `small = 2`
- `medium = 5`
- `large = 10`
- `major = 20`
- `epic = 40`

The exact scale may be revised after real delivery data accumulates.

## Weighted progress

For a stable roadmap snapshot:

`progress = accepted_completed_weight / planned_weight`

Raw step count must not be used as the primary completion percentage.

## Weight is not value

`work_weight` estimates delivery effort/complexity.

`portfolio_value` estimates importance to ecosystem progress.

They are different informational axes.

## One-year manual baseline

Before automated portfolio development begins in earnest, create a baseline for each module:

- baseline date;
- roadmap snapshot/version;
- estimated total weight;
- already completed accepted weight;
- estimated progress percentage;
- confidence (`low|medium|high`);
- assessment notes;
- evidence references.

The first baseline may be partly expert judgment. Its uncertainty must be explicit.

## Monthly snapshots

After the new operating model starts, preserve periodic snapshots (for example monthly) to observe:

- weighted work delivered;
- progress delta;
- spend;
- cost per weighted unit;
- lead time;
- rework;
- acceptance quality;
- executor/provider/model attribution.

## Interpretation warning

Weighted units are a governance approximation, not universal physical units.
Do not use them to claim false precision or compare unrelated work without context.
