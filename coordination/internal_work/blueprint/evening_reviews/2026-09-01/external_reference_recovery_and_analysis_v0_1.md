# Calculator / Constructor External Reference Recovery and Analysis v0.1

Date: 2026-09-01
Status: `OWNER_REFERENCE_SET_RECOVERED / RESEARCH_INPUT / NOT_EXTERNAL_AUTHORITY`

## Owner priority

PRIMARY calculator:
- `https://sborka.ua/`

SECONDARY calculators:
- `https://www.fastprint.pro/?utm_source=fastprintua&utm_medium=fastprintua&utm_campaign=fastprintpro_page#/CreateOrder/Sheetcut`
- `https://wolf.ua/uk/category/calc-polygraphy/`

Constructor references:
- `https://vizitka.com/uk/creator/universal`
- `https://www.fatline.com.ua/ua/products/constructor.html?gad_source=1&gad_campaignid=21944915723&gbraid=0AAAAADofqFsWsNStwjI1wEsxA-veD7ZSz&gclid=Cj0KCQjw79nUBhCgARIsADSHka05AlJIGb8gFc1HqJpIYlWges3j6e9trtymYMJS4QREHkHrogd_I10aAsz-EALw_wcB&validate=1`
- `https://maikoff.ua/konstruktor.html?srsltid=AfmBOorh0s1Xwt1juB0r9TX8l6BiVqsxEyc2_zGNvyWWVpFyDAoblaZ_`

## Research evidence

### Sborka — PRIMARY
Publicly visible evidence confirms an online professional print-ordering service with
registration/login and largely automated order processing. The authenticated calculator field
workflow was not publicly observable in this research pass.

Rule: keep Sborka PRIMARY, but do not invent hidden fields. Capture authenticated/manual workflow
later before feature-by-feature comparison.

### FastPrint Pro — SECONDARY
Public documentation shows:
- a product catalog as entry point;
- empty calculator or prefilled template/example;
- three main calculator blocks: parameters, price/lead time, order management;
- progressive/dependency-aware parameter choice;
- save-before-submit;
- production order lifecycle/status;
- dynamic price/lead-time selection near submission.

### Wolf — SECONDARY
Public calculator entry exposes multiple workflow/product families such as:
sheet printing/cutting, product sets, staple/PUR/wire binding, notebooks, packaging and calendar
families. This supports a product-family architecture rather than one flat form.

### Vizitka
Public evidence shows a reusable editor model with layouts/templates, text, photos/uploads,
clipart/icons, shapes, background/color/texture, layers, save/autosave/share and product settings.

### FATLINE
Public evidence shows product selection, image/clipart/text personalization, layer positioning and
sizing, live preview and order/cart flow. AI image generation appears in some public constructor
contexts; treat it as optional inspiration only.

### Maikoff
Public documentation shows product/base, color, image/photo/logo upload, text/shape placement,
resize/reposition/remove, live preview, print-method selection and order submission.

## Roadmap implications
1. Sborka remains PRIMARY but needs authenticated/manual field-level capture.
2. FastPrint is strong evidence for progressive/dependency-aware input and save-before-submit.
3. Wolf is useful for product-family decomposition.
4. Vizitka/FATLINE/Maikoff support a reusable constructor foundation with product-specific rules.
5. Do not clone external visual design; ForPrint uses its own Library design system.
6. External contractor ordering is isolated behind provider adapters.

## Gap resolution
Historical Calculator reference-URL GAP is resolved by owner-supplied exact URLs.

Residual research gap:
`GAP-CALCULATOR-SBORKA-AUTHENTICATED-WORKFLOW-001`.
