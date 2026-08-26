# ForPrint Library — Canonical Catalog & External Ingestion Target State v0.1

Status: PROVISIONAL / SYNTHETIC

Library is the canonical semantic source of truth for product/material/catalog definitions it owns.
Other modules consume Library identifiers/definitions instead of inventing independent semantics.

Large reference datasets should be imported/normalized rather than manually typed when reliable
sources exist, including supplier catalogs/websites, supplier SKUs/aliases and official provider
APIs/catalogs.

External information is an import source, not automatic ForPrint truth.

Target flow:

`external source -> ingest -> provenance -> normalize -> candidate match/merge -> review where needed -> canonical Library record`

Preserve supplier-specific names/part numbers while mapping them to stable canonical material ids.
