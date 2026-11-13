# ForPrint Library — evening delta

Canonical source for:
- stable IDs;
- names/aliases;
- units;
- shared reference values;
- revisions;
- lifecycle;
- deprecated/superseded/blocked states;
- semantic definitions used across modules.

Dynamic reference data must be supported.

Possible update modes:
A. direct fetch from trusted simple source;
B. specialized connector fetches, Library canonizes;
C. automatic detection + human approval for high-impact changes.

Revision lifecycle:
CURRENT -> SUPERSEDED_BUT_ALLOWED_FOR_EXISTING_WORK -> BLOCKED_FOR_NEW_WORK -> HISTORICAL/ARCHIVED.

Large assets: Library may own metadata/checksums/semantic identity while official object storage / Cloud Backup handles physical files.
