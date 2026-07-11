# Prompt: Library Configurable Product Workbench v0.1 — Business Card Skeleton

## Target module

`forprint_library`

## Prompt ID

`library_configurable_product_workbench_business_card_skeleton_v0_1`

## Purpose

Create the first controlled configurable product reference in ForPrint Library using one product only: business cards / візитки.

The goal is to make the first visible and machine-readable product card that downstream modules can understand without making Library responsible for pricing, orders, production, stock, 1C or runtime workflows.

This checkpoint should prove that Library can describe a configurable рекламно-інформаційний продукт as a stable reference object with aliases, constructor parameters, example values and a human-readable preview.

## Current context

Library has completed and Blueprint accepted or is now accepting:

- Make-first semantic reference readiness v0.1;
- Reference contract foundation v0.2;
- Coordination foundation alignment v0.1;
- Reference consumption pilot v0.3.

Library currently owns:

- canonical catalog semantics;
- stable catalog IDs;
- aliases;
- reference contracts;
- product/material/print-mode semantic references.

Library must not own:

- clients;
- orders;
- payments;
- stock truth;
- production runtime;
- 1C synchronization;
- CRM workflow;
- Telegram runtime;
- Calculator logic.

## Strategic direction

Do not build a full product catalog in this checkpoint.

Do not create a broad product database.

Do not import real 1C nomenclature.

Do not model all products.

Create one high-quality skeleton product card for business cards and make it useful as a pattern for future products.

The product card must be practical enough that a human can read it and downstream modules can later consume it as a stable reference.

## Required product

Create one configurable product reference:

```text
product.business_card
```

## Human names should include:

uk: Візитки
en: Business cards

## Aliases should include at least:

візитки
візитка
business cards
business card

If existing historical or downstream hints use a different form such as product:business_cards, keep that only as a legacy/channel hint or compatibility alias. The canonical Library ID for this checkpoint should remain stable and explicit.

## Required product card content

The business card product card must include at minimum:

stable product_id;
product kind/type, for example configurable_product;
status, for example draft_reference;
human-readable display names;
aliases;
category or product family reference if existing Library structures support it;
constructor/configurable parameters;
consumer usage notes;
boundary notes;
version or schema marker.

## Minimum configurable parameters:

size
sides
material_ref
print_mode_ref
quantity
finishing_refs

## Recommended parameter meanings:

size: choice parameter, for example 90x50 mm and 85x55 mm;
sides: one-sided or two-sided;
material_ref: reference to Library-owned material where possible;
print_mode_ref: reference to Library-owned print mode where possible;
quantity: numeric input context, not a price;
finishing_refs: optional list of Library finishing references.

## Optional but useful parameter:

artwork_source

This can describe whether the customer provides a print-ready file, needs design, or needs prepress check. Do not implement prepress runtime logic.

Required artifacts

The assistant should inspect the current Library structure before deciding exact names.

## Suggested artifacts:

catalog/configurable_products/business_card.yaml
schemas/configurable_product.schema.yaml
examples/product_cards/business_card_product_card.yaml
docs/architecture/configurable_product_workbench.md
docs/architecture/business_card_skeleton.md
scripts/product_workbench/preview_business_card_product.py
tests/content/test_business_card_product_card.py

The exact names may be adjusted to fit existing repository conventions, but the checkpoint must remain focused and small.

## Required preview

Add a human-readable product card preview.

The preview may be implemented as:

a small script;
a Makefile target wrapping that script;
or a checked-in example generated from the product card.

Preferred command if it fits the current Makefile style:

make product-card-preview

or:

make business-card-preview

The preview should show something like:

Product card: Візитки
Product ID: product.business_card
Kind: configurable_product
Status: draft_reference

Constructor parameters:
- size
- sides
- material_ref
- print_mode_ref
- quantity
- finishing_refs

Consumer notes:
- Telegram Bot may use aliases and product_id as route hints.
- Calculator Engine may later use parameters as pricing input context.
- Operational Registry may store product_id as a foreign-domain reference.
Required schema / validation

Add validation for the business card product card.

## Validation should confirm:

product ID is present and stable;
aliases are present and non-empty;
configurable parameters are present;
required parameters exist;
Library references are represented as references, not redefined downstream semantics;
no price formula is included;
no stock truth is included;
no production task logic is included;
no 1C import data is included.
Required consumer examples

Add or update examples showing how downstream modules may consume this product card.

At minimum, include notes or examples for:

Telegram Bot: may use product.business_card and aliases as route hints only;
Calculator Engine: may later use constructor parameters as pricing input context, but no formula is implemented here;
Operational Registry: may store product.business_card as foreign-domain reference metadata.

Do not implement real cross-module integration.

## Required documentation

Document:

what a configurable product card is;
why business card is the first skeleton product;
which fields are Library-owned;
which fields are consumer-owned;
how this differs from orders, pricing, stock and production;
why this is not a 1C import;
how future products should copy the pattern.
Required Makefile/check-report visibility

If a new validator or preview script is added, expose it through existing make-first workflow where practical.

The Library check report should include visibility for the business card skeleton validation or preview if possible.

Do not rewrite the Makefile broadly unless needed.

Required tests / checks

Run:

make check
make check-report
make governance-check
make module-validate
git diff --check

The tests should cover:

product card file exists;
product ID is stable;
aliases exist;
required configurable parameters exist;
product card validates against schema or validator;
preview script renders expected product ID and constructor parameters;
no forbidden ownership fields are introduced.
Required completion and reporting workflow

At the end of this task, the module assistant must prepare a module-side completion packet inside the Library repository.

The module assistant must not write directly into the Blueprint repository.

## Required module-side files:

coordination/reports/completion/<report>.md
coordination/reports/index.yaml
coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/status/next_questions_for_blueprint.md

Before manual report edits, inspect available automation:

find scripts -maxdepth 3 -type f | sort | grep -E 'completion|coordination|report|status|packet' || true
find coordination -maxdepth 3 -type f | sort
make help 2>/dev/null | grep -E 'completion|coordination|report|status|packet' || true

If completion packet automation exists, use it.

If completion packet automation is missing or incomplete, manual updates are allowed for this checkpoint, but the completion report must explicitly say:

Completion packet automation was not available or was deferred for this module step.
The required module-side coordination files were updated manually inside the Library repository.
No files were written directly into the Blueprint repository.

## Required completion report content:

prompt id;
branch;
final commit hash;
implementation commit hash if different from final merge/report commit;
summary of implemented work;
files changed;
checks passed;
known warnings;
explicit boundary confirmation;
confirmation that no Blueprint files were written directly;
open questions for Blueprint, or explicit “No open questions”.

## Status/report formatting requirements:

keep current_status.yaml valid YAML;
keep current_status.md readable Markdown;
close all Markdown code fences;
keep only current open questions in next_questions_for_blueprint.md;
ensure all text files end with a newline.
Blueprint reporting boundary

Library may read Blueprint prompts and standards.

Library must not write directly into:

/srv/software_development/forprint-project/forprint_system_blueprint/

Blueprint-side incoming report registration and Blueprint review are separate Blueprint-owned actions.

## Explicit non-goals

Do not implement:

full product catalog;
product modeling UI;
production catalog database;
live API;
1C import;
1C synchronization;
Calculator integration;
Telegram Bot integration;
Operational Registry write;
CRM write;
Website write;
price calculation;
final price formula;
material write-off logic;
warehouse stock truth;
production task creation;
real client/order data;
production runtime.
Definition of done

## The prompt is complete when:

one business card configurable product reference exists;
canonical product ID is stable;
aliases are present;
constructor parameters are present;
product card schema or validator exists;
human-readable preview exists;
consumer usage notes exist;
tests are green;
check report is green;
no forbidden integration or ownership is added;
completion report is created inside Library repository;
Library current status is updated inside Library repository;
final module commit hash is reported back to Blueprint.

---
