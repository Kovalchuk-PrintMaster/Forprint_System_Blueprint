# Calculator Engine Revision-1 Owner Review — Rebuild Input — 2026-08-27

Status: AGREED OWNER/THEORY INPUT; FINAL EXECUTION ROADMAP DEFERRED UNTIL DEEP INVENTORY.

# Calculator Engine — Revision 1 Owner Notes

Status: `REVISION_1_DISCUSSED`
Next: `INVENTORY_FIRST_TARGET_DIRECTION_CLEAR`

## Inventory-first rule — AGREED_WITH_OWNER

Calculator is old and already significantly developed.

Do not rebuild its roadmap from zero.
Sequence:
1. deep structural + semantic Knowledge Inventory;
2. identify implemented/reusable/obsolete/partial functionality;
3. map actual state to Target State;
4. then build the final detailed roadmap.

## Strategic role — AGREED_WITH_OWNER

Calculator is a central order decision engine.

It must answer:
- what can currently be produced;
- what it costs;
- how long it requires;
- what materials/operations/equipment are needed;
- what structured order/job specification should move onward.

## Dynamic pricing — AGREED_WITH_OWNER

Pricing must react to:
- material;
- quantity;
- technology;
- technical waste;
- urgency;
- currency;
- supplier/material shortage;
- staff shortage;
- equipment breakdown;
- production congestion;
- temporary commercial policy.

Example:
temporary staff shortage on thermal binding may justify a time-limited price coefficient increase to reduce demand instead of promising impossible delivery.

## Dynamic commercial & availability control — AGREED_WITH_OWNER

This deserves a deep dedicated roadmap section.

Candidate states:
- AVAILABLE
- CONSTRAINED
- TEMPORARILY_UNAVAILABLE
- HIDDEN
- MANUAL_QUOTE

Owner must be able to quickly apply temporary operational/commercial adjustments, potentially through a governed administrative Telegram path.

Examples:
- +25% coefficient for 48 hours;
- gray out unavailable material/product;
- hide a product while critical equipment is down.

## Library boundary — AGREED_WITH_OWNER

Calculator owns no foundational truth.

Library is canonical for:
- material types/names;
- product/material configurations;
- technical/reference facts;
- long-lived project rules and revisions;
- freshness/deprecation/retirement state.

Calculator reads permitted canonical facts from Library.

## Production queue / lead time — AGREED_WITH_OWNER

Customer ETA is not only normative process duration.

Current direction:
- production/print queue remains in Calculator for now because it is directly used in lead-time calculation;
- do not invent a separate scheduling module yet;
- revisit extraction only if scheduling becomes a sufficiently large independent domain.

Dynamic behavior:
- cancellation recalculates queue;
- equipment failure recalculates affected ETA;
- Calculator emits earlier/later readiness events;
- Telegram informs customers.

## Planned materials / write-off — AGREED_WITH_OWNER, boundary refinement later

Calculator knows planned material demand including technical waste.

Example:
100 production sheets + 5 setup/waste = 105 planned.

Later passes must separate:
- planned need;
- physical actual consumption;
- accounting posting.

## Visual constructors / Prepress — AGREED_WITH_OWNER

Calculator owns/orchestrates product visual constructors and previews and, where appropriate, production-ready design assistance.

Calculator and Prepress will have close bidirectional interaction.

## Channel interaction — AGREED_WITH_OWNER

Website: structured self-service configuration.
Telegram: conversational collection/clarification -> structured request -> Calculator -> structured quote/order form -> Telegram renders price/timing/confirmation.

Accepted order becomes a structured job/order package for operational execution.

## Warehouse relationship — AGREED_WITH_OWNER

Calculator sees real material availability.
Unavailable material must make affected options unavailable/gray/hidden rather than promising impossible production.

## Accounting relationship — AGREED_WITH_OWNER

Calculator can provide:
- client/order ID where available;
- calculated price;
- planned materials;
- line items/specification;
- accounting action inputs.

Accounting owns accounting/business-registry consequences.

## Human role — AGREED_WITH_OWNER

Normal mode should be automatic.
Human involvement is mainly for abnormal conditions:
- equipment failure;
- staff shortage;
- exceptional material state;
- special commercial policy;
- unresolved data conflict.

## Stabilization — AGREED_WITH_OWNER direction

Candidate:
about one month of stable live operation after tuning.

Do not use one global 5% tolerance.
Separate metrics are needed for:
- critical pricing;
- availability;
- ETA;
- waste coefficients;
- other prediction classes.

## Benchmark — SYNTHETIC_CANDIDATE

`zborka.ua` remains a future functional/UX reference baseline, not authority or ceiling.
Perform a dedicated benchmark later.

## Remaining gray zones

- actual current implementation until Knowledge Inventory exists;
- exact write-off ownership;
- long-term scheduling ownership if the domain grows;
- exact admin UX/channel for coefficients/availability;
- product-class-specific acceptance metrics.

<!-- calculator-owner-addendum-reference-examples-v0-1:start -->

## Owner addendum — reference examples for Calculator and constructors — 2026-08-27

Classification:

- `AGREED_WITH_OWNER`: keep external calculator/ordering services as comparative references;
- `AGREED_WITH_OWNER`: `sborka.ua` is the current primary working reference, but is explicitly
  non-final and may lose priority after later analysis;
- `AGREED_WITH_OWNER`: constructor capability should grow into a family of product constructors,
  not a single product-specific tool;
- `AGREED_WITH_OWNER`: prefer a shared reusable constructor architecture/UX foundation with
  product-specific rules and templates;
- `FUTURE_RESEARCH_TASK`: analyze real market/user demand before fixing the constructor backlog
  and implementation order.

Reference set currently supplied by the owner:

Calculator/service examples:
- `https://www.fastprint.pro/`
- `https://wolf.ua/`
- `https://sborka.ua/`

Constructor examples:
- `https://shop.foxminded.ua/en/constructor`
- `https://vizitka.com/uk/creator/universal?productId=5425&productComponentId=11893`

Candidate constructor families to investigate include business cards, apparel, mugs/cups,
thermoses, wall art/canvas and other common personalized-print products. This is not yet the
final ranked list.

No external reference is canonical ForPrint truth, a mandatory feature clone, or an architecture
authority.

<!-- calculator-owner-addendum-reference-examples-v0-1:end -->
