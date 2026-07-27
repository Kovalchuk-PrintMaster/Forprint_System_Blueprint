# Calculator Engine Role Boundaries

## Module ID

```text
calculator_engine
```
Status

Active module policy

Calculator owns

Calculator Engine owns calculation-specific logic and outputs.

Allowed ownership:

calculation execution;
calculation snapshots;
price breakdown;
material consumption estimate;
quote draft;
commercial offer draft;
order draft;
order creation draft;
calculation output package;
calculation warnings;
manual/custom operation draft;
calculation-facing validation;
calculation reports.
Calculator must not own

Calculator Engine must not become:

canonical client registry;
canonical order registry;
canonical product catalog;
canonical material catalog;
canonical service catalog;
canonical operation catalog;
Operational Registry;
ForPrint Library;
Accounting Registry;
1C synchronization adapter;
warehouse stock truth;
prepress lifecycle owner;
CRM workflow owner;
Integration Gateway runtime router;
customer channel adapter.
Relationship with ForPrint Library

ForPrint Library is the canonical semantic/catalog authority.

Calculator may temporarily hold local projections or fixtures, but should eventually reference Library-owned canonical IDs for:

product_id;
service_id;
material_id;
operation_id;
template_id;
technical_card_id.

If Calculator detects product/service/material ambiguity, it should not invent permanent canonical names.

Ambiguity should be reported to Blueprint/Library.

Relationship with Operational Registry

Operational Registry is the internal ForPrint DB/data custodian.

Calculator may produce structured order draft packages, but it must not become the canonical order database.

Future flow:

Calculator OutputPackage
↓
Operational Registry stores operational order/request records
Relationship with Accounting Registry

Accounting Registry owns accounting/1C sync boundary.

Calculator may produce accounting line drafts or calculation-based accounting hints.

Calculator must not perform real accounting posting, 1C synchronization, payment truth management or invoice ownership.

Relationship with Prepress

Calculator may describe prepress requirements.

Calculator must not own file lifecycle, prepress processing status, station sync, technical prepress verification or production file management.

Relationship with CRM

CRM is future human dashboard/workflow coordination layer.

Calculator may serve both external customer and internal manager calculation flows, but must not become CRM or workflow dashboard owner.

Manual override policy

Calculator should support internal manager/manual adjustments where needed.

Manual/custom adjustments must be visible, structured and auditable.

External customer-facing flows must not expose unrestricted manual override controls.

Large or unusual manual operations should be represented as manual/custom operation drafts and may require human review.


---
