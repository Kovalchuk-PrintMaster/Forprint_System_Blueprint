# File and Production Artifact Governance v0.1

Status: agreed direction with explicit proposed implementation details
Date: 2026-08-31

## Core decision

The historical ForPrint filename convention is preserved as a human-readable production
projection, but filename/path text is not canonical business truth.

Target layering:

1. physical source/production files;
2. legacy file catalog/index;
3. canonical structured ProductionFileDescriptor / Job Specification;
4. short human production filename;
5. Job Ticket / Operations Assistant projection.

## Legacy client archive

Existing client folders and date-based history remain supported. Do not mass-rename the legacy
archive merely to normalize it.

Legacy parser/indexing must tolerate:

- person/organization names;
- one or multiple historical contact numbers;
- phone formatting inconsistencies;
- date folders;
- mixed source formats;
- historical spelling/alias errors.

CRM identity remains canonical. Phone is a strong lookup identifier, not immutable person
identity.

## Human production filename

Human typing and reading speed are first-class requirements.

Canonical display convention:

- `_` separates semantic blocks;
- no mandatory double-underscore separator;
- ASCII `x` is preferred for generated multiplication/dimension syntax;
- legacy parser may accept `x`, Cyrillic `х`, `×`, `*` and known historical variants;
- common/default information may be omitted from the human filename when the active naming
  profile defines it unambiguously.

The second quantity in `copies x N` is physical sheets per copy, not abstract PDF pages.

Example interpretation:

`10x8_320x450_300_4+4_lamMat_...`

means 10 copies, 8 physical sheets per copy, 320×450 material format, standard coated 300 gsm,
4+4 print and default matte lamination for the active sheet-print naming profile.

For the Ricoh sheet-print profile, `lamMat` represents the agreed default thin matte roll
lamination (25 µm) without forcing the human operator to type `25`.

## Device/profile semantics

The same short token may mean different things in different production profiles. Context must
therefore be explicit in structured data.

Distinguish:

- required device capability;
- eligible device group/queue;
- concrete physical device instance;
- actual device used.

Library owns reusable capability/naming semantics. System Administration owns physical device
inventory/model/serial/availability. Operations Control Registry owns planned execution
assignment. Production Runtime Inspector records actual device/runtime evidence.

Legacy directory placement (for example Epson/Ricoh folders) is evidence for parser context,
not canonical device truth.

## Ownership

### Library

Owns canonical reusable semantics:

- material IDs;
- operation IDs;
- aliases and common misspellings;
- naming profiles;
- short human tokens;
- profile-specific defaults;
- device capability definitions.

### Calculator Engine

Primary implementation owner for:

- parse legacy/manual production filenames;
- normalize parsed production intent;
- render the active human filename projection;
- validate filename quantities against structured job/file evidence;
- reconcile manually created/offline production files into the canonical flow.

Calculator does not own the Library vocabulary.

### Contract Registry

Owns the versioned inter-module contract for ProductionFileDescriptor / Job Specification
representation where cross-module exchange is required.

### CRM

Owns person/organization/contact identity and normalized phone identifiers/display projection.

### Prepress Hub

Provides reusable deterministic file probes, including PDF page/size/readiness evidence. It
does not invent customer/business semantics.

### Operations Control Registry

Owns order/job identity, execution state, Job Ticket revision, HOLD/priority/reprint/proof
workflow and production gates.

### Operations Assistant

Displays the current Job Ticket, teaches workers how to read a production filename, exposes
visual instructions and can request a reprint of the current paper ticket.

## Legacy operational markers

Historical markers are parsed as legacy evidence and mapped into structured state instead of
remaining the future control mechanism.

- `$` — historical hint that a human believed the work was entered in accounting; future truth
  is order/accounting state.
- `A_`, `R_` — historical preparer/reviewer hints; future truth is prepared_by/competency/review
  policy.
- `!` — attention required; future state requires an explicit reason.
- `wait` — ready/prepared work whose START gate is held; map to explicit HOLD reason.
- `first` — priority/expedite class, not absolute ordering among all `first` jobs.
- `reprint` — child reprint workflow with reason, responsibility, material impact and billing
  consequence.
- `proba` — proof/sample purpose; billing can independently be FREE, INCLUDED or PAID.
- `add` / `Addon` — known foreign/customer-side legacy semantics; preserve raw token but do not
  assign ForPrint business meaning without an explicit mapping.

## Job Ticket direction

The filename remains a compact operational label. Detailed production meaning moves to the
versioned Job Ticket.

Job Ticket may include:

- order/job/revision;
- material/format/quantity/color;
- ordered production operations;
- visual finishing geometry where useful;
- priority/HOLD state;
- QR identifiers;
- current file revision;
- manual manager note/image attachment when no standardized Library instruction exists.

QR identifies a job/operation but is not permission.

A stale paper ticket must warn and offer the current revision.

## CRM/Telegram customer context

One person may simultaneously:

- place a personal order;
- actively represent one or more organizations.

Telegram should lightly state the currently selected billing/customer context, for example
"оформляю на Medicom", and allow the person to switch to a personal order.

When representation ends, its temporal relationship closes and is no longer proposed for new
orders. Historical orders preserve a representation snapshot.

Order-relevant confirmations should be reconstructible from structured conversation/decision
evidence even if the channel UI later changes or a message is removed.

## Legacy index and duplicate analysis

Proposed implementation direction:

- read-only initial crawler over legacy SMB trees;
- stable file identity + original path/name;
- hashes for exact duplicate detection;
- searchable normalized text/phone/date/device/material candidates;
- parser confidence and warnings;
- no automatic deletion;
- distinguish exact duplicate, same-name-different-content, derived export and unknown relation.

SQLite FTS5 / RapidFuzz are implementation candidates, not architecture authority.

## JDF / XJDF / PDF metadata

Future interoperability direction:

- database/Operations Control Registry remains canonical truth;
- human filename remains operational projection;
- PDF production metadata may carry stable portable production properties;
- JDF/XJDF may be used as an external print-workflow/device interchange format;
- runtime state such as payment/HOLD should not become authoritative merely because it is
  embedded in a PDF.

This is a future adapter direction, not a requirement for the first Calculator milestone.
