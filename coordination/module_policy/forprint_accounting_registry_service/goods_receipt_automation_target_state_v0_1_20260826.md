# Accounting Registry — Goods Receipt Automation Target State v0.1

Status: PROVISIONAL / SYNTHETIC / OWNER REFINEMENT EXPECTED

Goal: reduce manual goods-receipt entry to a short review/confirmation workflow.

Inputs include Excel/structured supplier files, PDF documents, and scans/photos through OCR.

Target flow:

`source -> identify supplier/document -> parse/OCR -> supplier item mapping -> canonical Library material -> extract quantity/price/tax/document facts -> confidence -> operator review/correction -> confirm/post -> audit trail`

One canonical material may have many supplier descriptions/part numbers:

`supplier_id + supplier_part_number + supplier_description -> canonical_material_id`

Confirmed mappings should reduce future manual work.

OCR/fuzzy/AI matching may propose candidates, but low-confidence material, quantity, price or
financial facts must not silently post.

Preserve original source, parsed values, mapping/confidence, corrections, confirmation evidence and
final posted facts.

Canonical material semantics belong to Library.

<!-- supplier-document-business-partner-clarification-2026-09-01:start -->
## 2026-09-01 clarification

Supplier identity references the shared Business Partner master; Accounting owns financial attributes
and posting consequences.

Preserve supplier item provenance:
supplier_business_partner_id + supplier_part_number + supplier_description -> canonical Library material ID.

Incoming supplier documents may be Excel/structured, PDF, Word-like or scans/photos. Low-confidence
financial facts remain human-confirmed.

Future conditional payment mandates are later high-risk automation requiring preauthorization, limits,
duplicate prevention, idempotency, audit and staged activation.
<!-- supplier-document-business-partner-clarification-2026-09-01:end -->
