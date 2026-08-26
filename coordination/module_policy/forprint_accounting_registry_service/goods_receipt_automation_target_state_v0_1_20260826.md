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
