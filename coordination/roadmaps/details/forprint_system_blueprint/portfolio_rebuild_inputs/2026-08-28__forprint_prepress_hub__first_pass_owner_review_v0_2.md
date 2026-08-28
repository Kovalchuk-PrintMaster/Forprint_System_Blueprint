# ForPrint Prepress Hub — evening first-pass owner review

Module: `forprint_prepress_hub`

Status: `FIRST_PASS_OWNER_DIRECTION_RECORDED / SYNTHETIC_MICROSTEPS_PENDING_SECOND_PASS`

## AGREED_WITH_OWNER

Prepress Hub is the automated file-readiness and print-preparation system. It should inspect client files
against structured job/product requirements, apply bounded safe corrections, build production-ready derivatives,
explain remaining risks in friendly language, obtain approval where required and escalate genuinely ambiguous
cases to a human prepress specialist.

External engines such as Acrobat/PitStop/Quite Imposing/Photoshop/Illustrator may be controlled through
adapters/actions/presets.

## Working boundary

Prepress owns file readiness, preflight verdicts, fix/derivative lineage and production-ready package evidence.
Calculator owns job spec/pricing; Library owns technical/reference requirements; external tools are execution engines,
not business truth owners.

## Synthetic roadmap expansion for pass 2

Everything below is `SYNTHETIC_CANDIDATE` unless explicitly described as owner direction.

### PRE-R0 — Inventory old evidence/tools/files
- recover older owner discussion if available
- inventory PitStop/Quite Imposing/Adobe scripts/actions/presets
- collect representative good/bad client files
- classify deterministic vs judgment-heavy transformations
### PRE-R1 — File/job/readiness model
- master vs preview/working/production copy
- job-spec and product-requirement refs
- blocker/warning/advisory taxonomy
- tool/preset/version provenance
### PRE-R2 — Core preflight checks
- format/pages/dimensions/orientation
- resolution/effective DPI
- bleed/safe zone/trim
- color spaces/spot colors/transparency/overprint
- fonts/embedding/text risks
- compare against job spec
### PRE-R3 — Safe normalization/fixes
- bounded PDF normalization
- approved color/profile conversions
- bleed/trim/imposition fixes
- reversible output + before/after evidence
### PRE-R4 — Production tool adapters
- Quite Imposing-like imposition workflows
- Acrobat/PitStop actions
- Photoshop/Illustrator adapters where needed
- preset/version pinning
### PRE-R5 — Preview + client report
- render proofs/thumbnails
- highlight problem areas
- plain-language fixed/unresolved issue report
- approximate print-result preview with limitations
### PRE-R6 — Approval/rework/escalation
- client accept
- replacement upload
- bounded automated retry
- human prepress escalation
### PRE-R7 — Production-ready package
- hashes/refs to approved input/derivatives
- readiness evidence
- downstream production asset package
- CRM/Telegram status projection
### PRE-R8 — Regression/performance
- large-file limits
- good/bad regression corpus
- false-positive/negative tracking
- tool upgrade compatibility

## Dependencies

Calculator job spec; Library requirements; file/asset storage; Telegram/Website for client interaction;
future production runtime.

## Open questions for pass 2

Native transforms vs tool adapters; automatic-fix approval boundaries; printed-preview uncertainty;
licensing/runtime constraints; historical long-form dialogue reconciliation.

## Target milestone

Most standard client files reach a proven production-ready package automatically; risky changes are visible,
reversible and approved/escalated.

## Steady state

Continue measured improvement after the target milestone; the module is not considered permanently finished.
