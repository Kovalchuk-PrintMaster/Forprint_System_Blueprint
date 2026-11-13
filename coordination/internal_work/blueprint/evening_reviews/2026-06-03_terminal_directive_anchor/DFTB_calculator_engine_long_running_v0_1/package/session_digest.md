# Session Digest — Calculator Engine long-running module history

## Duplicate result

Unique source. No shared message IDs/source hash/exact substantive transcript reuse was found against clean master v2.8.

## Chronology warning

Filename: `Asistant_Calculator_Engine_09.10.26.mhtml`

MHTML export saved:
`Tue, 15 Sep 2026 15:33:42 +0300`

The filename label `09.10.26` falls **after** the export date. Internal evidence includes:
- 2025-era documentation/migrations/backups;
- server/quarantine artifacts from May 2026;
- a Blueprint directive named `2026-06-03__calculator_engine__directive__final-coordination-checkpoint-and-pause-v1`.

Therefore this is treated as a **long-running Calculator history with a terminal checkpoint after the 2026-06-03 directive**, not as an October 2026 source.

## Provenance layers

The source mixes three evidence classes:

1. **Turn 3 imported prior ChatGPT conversation** — useful but secondary historical evidence.
2. **Direct owner/terminal dialogue** — stronger evidence for requirements and decisions.
3. **Historical assistant reports/bug summaries** — useful implementation/diagnostic evidence, not current proof.

These are not collapsed.

## Calculator mission

The original problem is bigger than a static price list.

Owner needs:
- editable prices without code changes;
- Telegram-facing calculation/output;
- future Website/mobile usage;
- audience-specific B2B/B2C presentation;
- bulk/group price policies;
- a scalable product/material/property model.

This points toward Calculator as a **data-driven calculation engine**.

Later Blueprint architecture independently confirms the stable domain boundary:
**Calculator owns calculation logic.**

## Development style

Owner explicitly asks to move slowly in bounded steps and avoid receiving ten implementation steps/code blocks at once.

Documentation is a first-class requirement:
code/functions/sections should remain understandable after years of project growth.

## Pilot before catalog explosion

Rather than model every product immediately, the owner chooses a few representative products:
- business cards;
- flyers;
- booklet-like product.

The purpose is to stabilize:
- schema;
- relationships;
- admin workflow;
- calculation;
- external integrations;
before scaling the catalog.

## Catalog relationship model

A key owner correction is to avoid manually listing every allowed material/finishing relationship per product.

Historical requirements introduce reusable selectors:
- product type;
- material class/category;
- grammage/density range;
- finishing/option groups;
- other reusable constraints.

Example logic:
a product can accept all coated papers **within an allowed grammage range** rather than storing dozens of material IDs manually.

This is strong historical domain intent.

## Admin surface

Owner concludes that Calculator needs a serious admin/data-management surface rather than disposable temporary tools.

Historical expectations include:
- managing tables/relationships;
- supporting multiple administrators;
- future extensibility;
- efficient catalog/price editing.

The implementation history then uses Django Admin over database tables.

Important later correction:
this does **not** mean Calculator admin is allowed to become the admin/canonical database for the whole ForPrint ecosystem.

Later Blueprint/Library boundaries supersede that early broad idea.

## Database/schema ownership

Historical architecture:
- PostgreSQL for Calculator data;
- Alembic for schema migrations;
- Django models as admin projections over existing tables (`managed=False`);
- explicit backup/restore tooling.

Historical restore output includes per-table:
- before count;
- rows/data in dump;
- after count.

This reflects a strong requirement for visible/non-silent data operations.

## Repository architecture and paths

Owner repeatedly requires:
- modular repository layout;
- separate Docker/Django/API/DB/docs/test concerns;
- informative names;
- centralized paths/settings;
- no hard-coded filesystem paths inside scripts;
- composable path variables;
- portability across disks/servers.

Historical repo cleanup also used `_quarantine` for legacy state.

This strongly aligns with later Blueprint project-relative-path policy.

## Historical validation evidence

One visible checkpoint:
- Django system check: no issues;
- support tests: **12 passed**.

A later quote/intake checkpoint shows:
- **35 passed / 1 failed**;
- failure is the idempotency test because the first request unexpectedly returns `reused=true`.

That failure is preserved as a test-state/isolation risk, not erased.

## External quote intake

Historical runtime evidence shows a fairly rich Calculator API:
- external source/brand;
- idempotency key;
- product/material/quantity/selected operations;
- job_public_id;
- locale/currency;
- line-item material and operation costs;
- subtotal/total;
- human report;
- external report.

A conflicting re-use of the same idempotency key with a changed payload returns an explicit conflict.

Another visible response returns:
`material_not_found`
with request_id and retryability metadata.

## Owner safety requirements for external channels

If Website/external data is malformed:
- Calculator must not simply crash;
- invalid input should be filtered/validated;
- significant conflicts should not disappear into silent logs;
- a compact Telegram alert should be generated;
- detailed logs should remain available server-side.

The alert transport itself should be reconciled with current observability/Operations architecture.

## Mobile

Owner explicitly requires that Calculator's backend design remain usable from future mobile clients.

This reinforces channel-neutral calculation contracts.

## Blueprint coordination

Late historical process:
1. receive/clarify Blueprint prompt;
2. reconcile Calculator direction;
3. complete bounded work;
4. send new report/intent to Blueprint;
5. adjust plan;
6. continue.

Owner also asks to organize coordination through Git.

## Historical terminal checkpoint

Visible terminal evidence:

`eba5384 (HEAD -> main, origin/main) Add final coordination checkpoint and controlled pause`

The following assistant message records the module in a controlled pause pending Blueprint resume.

This is **historical terminal evidence**, not current repository state.

## Directive sync bug — important cross-module feedback

Calculator's local importer:
`make blueprint-sync-directives`

could return an apparently successful result while importing nothing.

Root cause:
the parser searched old/top-level shapes like:
- `directives`
- `prompts`

while the actual Blueprint index used:

`module_directives.active`

The final bug report says the parser was updated to:
- consume `module_directives.active`;
- retain deliberate legacy fallbacks.

A second issue:
commands using paths such as `scripts/...` depended on being run from repository root.

Stable lesson:
**coordination tooling must validate canonical schema and resolve repository-root paths independently of cwd.**

## Canonical authority reconciliation

Historical Calculator contains a large local product/material catalog and direct Website/Telegram assumptions.

Later project architecture changes the interpretation:
- Calculator owns calculation math/output;
- Library owns canonical definitions/contracts;
- a temporary local Calculator catalog is allowed only as a development bridge;
- Gateway/Contract Registry/CRM may own current runtime channel/routing boundaries.

Therefore healthy historical Calculator code must not be promoted directly into current canonical ownership without live audit.

## Current-audit priorities produced by this source

1. Current Calculator repo/HEAD and `eba5384` ancestry.
2. Calculator ↔ Library Calculator Input Contract.
3. Quote/intake/idempotency/error/report contract correctness.
4. Gateway/Contract Registry/channel routing.
5. CWD-independent/project-relative path tooling.
6. Alembic/Django/restore ownership and safety.
7. Telegram/operational alert path.
8. Blueprint directive-index schema validation.
