# Prompt: Library Configurable Product Workbench v0.1 — Business Card Skeleton

## Target module

`forprint_library`

## Purpose

This prompt directs ForPrint Library away from blind product/template generation and toward a real configurable product model.

The goal is to create the first visual, inspectable, owner-defined configurable product skeleton using one simple product family:

```text
business_card / Візитка
```

This step must help the project understand how products should be structured before importing or comparing data from 1C.

Strategic direction

ForPrint Library must not behave as a random catalog generator.

Library should define stable semantic product structures that can later be used by:

Calculator Engine;
Website;
CRM;
Operational Registry;
future channel assistants;
production workflow;
accounting/1C mapping.

The correct direction is:

configurable product family
+
option schema
+
multilingual names
+
offer presets
+
preview payloads
+
reviewable Workbench UI

not:

flat list of generated product names;
uncontrolled product combinations;
1C-driven model inheritance;
automatic canonical approval.
Important terminology note

In some prior operator notes, the word viber may appear accidentally because of keyboard autocorrection.

For this prompt, interpret such occurrences as library when the context is product catalog, product schema, nomenclature or Library work.

Do not implement Viber/channel functionality in this milestone.

Scope

Implement a first read-only configurable product Workbench for one product family:

business_card

The milestone should demonstrate:

stable product family ID;
multilingual product names;
language-specific aliases;
option groups;
option values;
input types;
default values;
required fields;
sort/display order fields;
offer presets;
naming preview;
Calculator Engine payload preview;
production steps preview;
order line preview;
source/provenance metadata;
schema validation;
read-only visual Workbench.
Non-goals

Do not implement:

1C import;
direct 1C database parsing;
PostgreSQL;
production databaselanguage-specific aliases;
option groups;
option values;
input types;
default values;
required fields;
sort/display order fields;
offer presets;
naming preview;
Calculator Engine payload preview;
production steps preview;
order line preview;
source/provenance metadata;
schema validation;
read-only visual Workbench.
Non-goals

Do not implement:

1C import;
direct 1C database parsing;
PostgreSQL;
production database migration;
automatic generation of all product combinations;
automatic canonical product approval;
real Calculator Engine integration;
price calculation;
material write-off calculation;
production write;
CRM features;
client entity;
carrier/logistics entity;
Viber/Telegram/Website channel flow;
full multilingual UI framework;
large repository refactor.

This milestone is only a Library-side product schema and visual preview foundation.

Core architectural rule

Library owns semantic product structure.

Library does not own:

prices;
client orders;
payment truth;
stock truth;
production execution;
accounting truth;
1C accounting records.

Library may prepare preview payloads for other modules, but those payloads are contracts/previews only.

Product modeling rule

The first product must be modeled as a configurable product family.

Use this conceptual split:

ProductFamily
ProductConfigurationSchema
OptionGroup
OptionValue
OfferPreset
ConfiguredItemPreview
CalculatorPayloadPreview
ProductionStepsPreview

Do not model business_card as a flat list of many final products.

Stable ID rule

Technical IDs must be stable and independent from display names.

Required principle:

id is stable;
display name is editable;
aliases are searchable;
category assignment is controlled;
analytics must not depend on mutable product names.

Example:

product_family_id: business_card
display_names:
  uk: Візитка
  en: Business card
  ru: Визитка
  pl: Wizytówka

Changing display_names.uk must not change the identity of the product family.

Multilingual requirement

The product skeleton must support at least these languages:

uk
en
ru
pl

For product family, option groups, option values and offer presets, support multilingual names where practical.

At minimum, provide multilingual fields for:

display_names;
short_descriptions or descriptions;
aliases.

Example:

aliases:
  uk:
    - візитки
    - візитна картка
  en:
    - business cards
    - visiting card
  ru:
    - визитки
  pl:
    - wizytówki

Do not create separate product entities per language.

Sorting and filtering foundation

The schema should include enough metadata for future UI sorting and filtering.

Recommended fields:

category_id;
category_sort_order;
product_sort_order;
option_group_sort_order;
option_value_sort_order;
preset_sort_order;
tags;
facets;
status;
is_customer_visible;
is_operator_visible.

Do not overbuild UI filtering in this milestone, but keep the model ready for it.

Business card skeleton

Create an initial owner-defined seed for business_card.

Recommended initial product family:

schema_version: configurable_product_v0_1
product_family_id: business_card
category_id: printed_products
status: draft
source:
  source_type: owner_defined_seed
  source_note: Initial business card configurable product skeleton
display_names:
  uk: Візитка
  en: Business card
  ru: Визитка
  pl: Wizytówka

Recommended option groups:

format;
print_mode;
material;
quantity;
lamination;
corner_rounding;
foil_stamping;
embossing;
spot_uv;
file_preparation;

Recommended input types:

select;
radio;
checkbox;
number;
text;
file;

Important: not every option is a checkbox.

Use the appropriate input type for each option group.

Examples:

format -> select/radio;
print_mode -> radio/select;
material -> select;
quantity -> number/select;
lamination -> select or checkbox group;
corner_rounding -> checkbox;
foil_stamping -> checkbox with manual review flag;
embossing -> checkbox with manual review flag;
custom comments -> text.
Default and required values

The schema should support default values and required fields.

Example defaults may be used for preview only:

defaults:
  format: 90x50
  print_mode: 4+4
  material: coated_350
  quantity: 500

Required fields should include at least:

format;
print_mode;
material;
quantity.
Option constraints rule

Do not implement deep technology constraints in Library.

Library should not decide all material/process compatibility rules.

However, Library may mark options with simple metadata:

requires_manual_review;
calculator_owned_constraints;
production_owned_constraints;
customer_visible;
operator_visible.

Example:

foil_stamping:
  customer_visible: true
  requires_manual_review: true
  calculator_owned_constraints: true

Detailed compatibility logic belongs to Calculator Engine and/or production rules.

Offer presets

Implement a small number of offer presets.

Offer presets are not a replacement for the product configurator.

They are quick-start configurations for price lists, website cards or operator shortcuts.

Example presets:

business_card_standard;
business_card_standard_lamination;
business_card_premium;

Each preset should reference product_family_id: business_card and provide a predefined configuration.

Do not generate all possible combinations.

Naming preview

Implement naming preview for configured product selections.

Provide at least:

customer-facing name preview;
internal configuration key preview.

Example customer-facing Ukrainian preview:

Візитка 90×50 мм, 4+4, крейдований папір 350 г/м², матова ламінація, скруглення кутів

Example internal generated configuration key:

business_card__90x50__4x4__coated_350__lamination_matte__rounded_corners

The internal generated configuration key is not the primary product family ID.

Calculator payload preview

Implement a preview payload for Calculator Engine.

This is not a live integration.

Example:

product_family_id: business_card
language: uk
configuration:
  format: 90x50
  print_mode: 4+4
  material: coated_350
  quantity: 500
  finishing:
    lamination: matte
    rounded_corners: true
    foil_stamping: false
    embossing: false

The preview should demonstrate how Calculator Engine could later receive structured product configuration data.

Production steps preview

Implement simple production steps preview.

This is not production execution.

Example:

base_steps:
  - prepress_check
  - print
  - cutting
  - packing

option_added_steps:
  lamination_matte:
    - lamination
  rounded_corners:
    - corner_rounding
  foil_stamping:
    - foil_stamping_prepare
    - foil_stamping
  embossing:
    - embossing_prepare
    - embossing

The Workbench should show a combined preview for selected options.

Workbench UI

Create a minimal read-only visual Workbench.

It may be simple HTML/Jinja/HTMX/FastAPI or another lightweight existing Library-compatible approach.

Required pages or equivalent views:

product family list;
business_card product card;
option groups view;
offer presets view;
configured item preview;
Calculator payload preview;
production steps preview.

Suggested local route names:

/library-workbench
/library-workbench/products
/library-workbench/products/business_card
/library-workbench/products/business_card/preview

The UI must be read-only.

No production writes.

No 1C writes.

No canonical auto-approval.

Validation

Add validation for the seed/model.

Validation should check at least:

stable product_family_id exists;
required multilingual names exist for uk/en/ru/pl;
option groups have stable IDs;
option values have stable IDs;
sort orders are numeric where present;
default values reference allowed options;
offer presets reference existing product family and options;
preview payload can be generated;
production steps preview can be generated.
Makefile expectations

Use the existing Library Makefile style.

Do not perform a large Makefile refactor.

Add small targets only if they fit safely into the current structure.

Recommended target names:

product-workbench-check
product-workbench-preview

If the current Library Makefile already has better naming conventions, follow the existing module style.

Testing requirements

Add automated tests for:

business_card seed validation;
multilingual fields;
stable ID vs display name separation;
option group parsing;
offer preset validation;
naming preview generation;
Calculator payload preview generation;
production steps preview generation;
Workbench route smoke test if UI is implemented.

The module should remain green after implementation.

Documentation requirements

Add a short development note explaining:

why Library uses configurable product families;
why business_card is a skeleton, not a flat product list;
how offer presets differ from generated combinations;
what Calculator Engine may later consume;
why 1C import is intentionally deferred.
Completion report requirements

Prepare a completion report that states:

what files were added;
how the business_card skeleton is represented;
how to run the Workbench preview;
what tests were added;
what is intentionally deferred;
whether any questions require Blueprint decision.
Acceptance criteria

This prompt is complete when:

business_card configurable product seed exists;
schema/model validation exists;
read-only Workbench preview exists;
multilingual names are represented;
stable IDs are separated from mutable display names;
offer presets are represented;
Calculator payload preview works;
production steps preview works;
tests pass;
no 1C import is implemented;
no blind catalog generation is implemented;
no production write is implemented;
completion report is prepared.
Future steps after this milestone

After this milestone, possible next steps are:

owner review of the business_card skeleton;
adjust naming and option structure;
manual handoff of business_card config schema to Calculator Engine;
later 1C comparison import as a separate controlled milestone;
later real product families after the skeleton is accepted.
