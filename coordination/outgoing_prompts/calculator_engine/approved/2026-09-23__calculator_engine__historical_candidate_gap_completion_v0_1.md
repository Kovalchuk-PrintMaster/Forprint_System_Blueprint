# Prompt: Complete bounded Calculator historical candidate gaps v0.1

## Target module

`calculator_engine`

## Authority and provenance

This is a Blueprint-approved bounded implementation prompt derived from the
2026-09-23 current-state reconciliation of the two historical Calculator
candidates.

Reconciled Calculator baseline:

- branch: `main`
- HEAD: `457d1a70cf9fe39351201c6452104b3d6b87a6b5`
- worktree: clean at reconciliation time
- full test suite: `108 passed`
- authority leakage review hits: `0`
- direct Telegram/Website runtime coupling review hits: `0`

The six recovered Human Intents are already published in Blueprint and the
Calculator Human Intent index count is `27`.

Historical evidence is provenance, not implementation authority. Current
Calculator code and current Blueprint ownership boundaries remain authoritative.

## Mandatory intake before implementation

Do not start implementation from chat text or from this file copied manually.

Use the established module workflow:

1. `make blueprint-pull`
2. `make blueprint-check`
3. `make blueprint-sync-directives`
4. inspect `coordination/prompts/received/`, `coordination/prompts/active/`,
   `coordination/prompts/archived/` and `coordination/prompts/index.yaml`
5. synchronize this exact approved prompt into the local prompt intake
6. verify exactly one current active prompt before changing runtime code
7. run the existing module governance/check baseline

If the approved prompt cannot be synchronized into the module prompt intake,
stop and report the coordination gap. Do not substitute chat text as authority.

## Objective

Complete only the gaps proven by current-state reconciliation. Reuse all current
working implementation. Do not redesign the Calculator architecture.

## Work package A — pricing policy / bounded admin gap completion

### Runtime gap

Implement `filtered_bulk_policy_update` using the existing Calculator pricing
and rule model.

The behavior must support, within Calculator-owned pricing policy:

- filtered scope selection;
- percentage or rule-based adjustment;
- explicit exclusions;
- preview/diff before apply;
- auditable result scope.

The implementation must not create Calculator ownership of customer identity,
canonical product/material catalog, accounting, order truth or channel UI.

### Focused tests required

Add focused tests proving:

1. data-driven prices / tiers / options / modifiers;
2. approved B2B/B2C or segment reference can affect pricing without making
   Calculator the owner of customer/segment truth;
3. filtered bulk policy update, including exclusions and preview/diff;
4. bounded Calculator admin behavior and ownership boundaries.

Use tests-first. Preserve existing behavior and existing passing tests.

## Work package B — channel-neutral quote contract gap completion

### Runtime gap

Implement `provenance_reference_versions` in the existing Calculator quote
result semantics.

The quote/result must expose stable provenance/reference-version evidence for
the Calculator-owned calculation result using existing domain structures where
possible.

Do not move Contract Registry schema-version authority or Integration Gateway
transport/correlation authority into Calculator.

### Focused tests required

Add focused tests proving:

1. same idempotency identity + same payload may safely reuse the same domain
   result;
2. structured line-item calculation evidence remains present and deterministic;
3. provenance/reference versions are present and stable in the quote result.

Preserve existing explicit conflict behavior for same identity + different
payload and existing validation/error semantics.

## Explicit non-goals

Do not:

- redesign Calculator architecture;
- restore a Calculator-local canonical catalog;
- make B2B/B2C customer classification canonical inside Calculator;
- add CRM/customer ownership;
- add Gateway transport/routing/delivery ownership;
- add direct Telegram-specific or Website-specific transport;
- rewrite already-working quote behavior merely to match historical mechanics;
- perform broad unrelated refactors;
- modify Blueprint from the Calculator implementation worktree.

## Validation

At minimum:

- all new focused tests pass;
- full existing Calculator pytest suite passes;
- `make check` passes if the module's current published check surface is healthy;
- `make module-policy-check`;
- `make governance-check`;
- `git diff --check`;
- Calculator worktree is reviewed for exact bounded scope.

If a broader governance/check fails because of an independently verified
pre-existing external Blueprint condition, report it separately and do not hide
it by broad unrelated mutation.

## Commit discipline

Use bounded commits and push after each fully working package:

1. Work package A — pricing/admin gap completion.
2. Work package B — quote provenance gap completion.
3. Coordination/completion records, if the module's established workflow
   requires a separate closeout commit.

Do not use `git add .`.

## Completion report

Return a compact completion report containing:

- implementation files changed;
- tests added/changed;
- focused test results;
- full pytest result;
- Make/governance check results;
- ownership-boundary confirmation;
- commit hashes;
- unresolved items, if any.

A completion report does not self-accept the work. Blueprint review remains a
separate step.
