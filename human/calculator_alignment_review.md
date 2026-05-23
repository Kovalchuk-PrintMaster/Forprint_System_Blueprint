# Calculator Engine Alignment Review

## Status

Reviewed.

## Source report

coordination/incoming_requests/calculator_engine/new/2026-05-23-calculator-engine-alignment-report.md
Main conclusion

Calculator Engine is moving in the correct direction.

It is still primarily a calculation-focused service and already has useful structures for:

quote/configurator draft flow;
configuration preview;
quote preview;
price breakdown;
calculation job persistence;
human/external report projection;
local catalog sync foundation from ForPrint Library.

There is no need for urgent large refactoring.

Accepted direction

Calculator Engine should remain focused on:

quote_draft
price_breakdown
product_configuration
material_consumption_estimate
calculation execution/report snapshots
calculation-specific pricing rules
Important boundary decision

Local catalog-related tables inside Calculator Engine are acceptable only as:

imported calculation input
local projection
cache / snapshot

They are not canonical truth.

This applies to:

MaterialCategory;
Material;
OperationType;
ProductType;
ProductTemplate;
UiBrand;
UiSkin;
imported catalog structures;
template visibility metadata.

Canonical ownership should remain outside Calculator, primarily in ForPrint Library.

Controlled drift risks

The following risks are real but manageable:

Local catalog tables may be treated as source of truth.
UiBrand / UI visibility config may drift into global brand registry.
Customer/order references may drift toward local CRM behavior.
Imposition foundation may drift into Prepress file ownership.
Direct external intake may drift into general backend behavior.
Required safe corrections
1. Classify local catalog tables as non-canonical

Calculator documentation and manifest should clearly say:

Library-sourced catalog tables = projection/cache/imported calculation input.
2. Define material_consumption_estimate as first-class contract

Current material consumption information exists inside quote lines, but should become a dedicated output contract before Warehouse, CRM, Accounting or Registry start depending on it.

3. Keep customer/order context as snapshot only

Calculator may receive request context, customer reference or external customer id, but it must not become the canonical client/order registry.

4. Keep ImpositionJob technical

Calculator may estimate or prepare a technical job shell, but Prepress Hub should own actual file analysis/preparation lifecycle.

5. Move production external intake behind Integration Gateway later

Current direct intake is acceptable for development, but production usage should move toward approved Integration Gateway contracts.

Blueprint questions created from report
Who owns brand/channel defaults?
Who owns machine capabilities and print modes?
Which product template operation rules belong to Library, and which are Calculator overlays?
Should material_consumption_estimate become a system-level contract now?
Should CalculationJob stay local, or should a summary be mirrored into Operational Registry?
Should trusted site-to-calculator handoff be owned by Integration Gateway?
Where should imposition/prepress orchestration live long-term?
Decision

Proceed with Calculator Engine development, but with boundary corrections.

Do not pause the module.

Do not perform large refactoring immediately.

Next Blueprint action:

define material_consumption_estimate as first-class data object / contract
and then continue with CRM alignment.