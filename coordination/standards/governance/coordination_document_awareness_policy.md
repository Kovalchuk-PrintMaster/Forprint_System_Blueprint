# Coordination Document Awareness Policy

## Purpose

This standard defines how ForPrint modules should become aware of new, changed, reviewed, deferred and applied Blueprint coordination documents.

The goal is to avoid manual operator-driven instructions such as:

```text
read this one document manually
check if something changed somewhere in coordination
```

Instead, Blueprint should provide a structured document awareness layer based on:

document manifest
content hash
directory-level priority
module awareness ledger
dashboard
context bundle
Problem

ForPrint modules depend on Blueprint coordination documents such as:

global policy
standards
instruction intake
module policy
outgoing prompts
reports
templates

However, module assistants do not automatically know when new documents are added or when existing documents are changed.

Without a document awareness layer, the operator must manually tell each assistant which documents to read.

This does not scale.

Core Rule

Blueprint coordination documents must be discoverable through a generated manifest.

Modules should compare the current Blueprint document manifest with their local document awareness ledger.

The comparison should show:

new documents
changed documents
already acknowledged documents
documents in progress
applied documents
deferred documents
not applicable documents
superseded documents
Source of Truth

The source of truth for document content is the Blueprint repository.

The source of truth for module review state is the module-local document awareness ledger.

Blueprint owns:

document paths
document content
document hashes
directory-level priority defaults
document source registry
context bundle generation logic

A module owns:

whether it has acknowledged a document
whether it is applying a document
whether a document is deferred
whether a document is not applicable
module-specific notes and commits related to document adoption
Content Hash Rule

Document changes should be detected by content hash.

Preferred hash:

sha256

The content hash is the primary signal for document changes.

File modified time and file size may be recorded for convenience, but must not be treated as the source of truth.

Directory-Level Priority

Priority should usually be assigned at the directory/source level, not manually on every document.

Allowed priorities:

critical
high
normal
low
reference

Recommended meaning:

critical  = must be reviewed before continuing relevant work
high      = review before the next meaningful prompt or module checkpoint
normal    = review gradually; does not normally block the current prompt
low       = cleanup/backlog awareness
reference = read only when directly relevant
Recommended Source Categories

Blueprint should distinguish between different source categories:

coordination/global_policy
coordination/standards
coordination/instruction_intake
coordination/module_policy
coordination/outgoing_prompts
coordination/templates
coordination/reports

Recommended defaults:

coordination/global_policy              critical
coordination/standards                  high
coordination/instruction_intake          high
coordination/module_policy               critical
coordination/outgoing_prompts            critical
coordination/templates                   normal
coordination/reports                     normal/reference
Applies-To Rule

A document source should define its applicability.

Allowed applies-to values:

all
module_specific
filtered
reference

Meaning:

all             = relevant to every active module
module_specific = relevant only to the matching module
filtered        = relevant only if tags, module id, ownership domain or prompt scope match
reference       = not normally required unless directly relevant
Module Awareness Ledger

Each module may keep a local ledger such as:

coordination/blueprint_awareness/document_review_ledger.yaml

The ledger should record which Blueprint documents the module has seen and how it handled them.

Allowed module document statuses:

unseen
acknowledged
in_progress
applied
deferred
not_applicable
returned_for_fix
superseded

Status meaning:

unseen          = document exists in Blueprint but module has not reviewed this hash
acknowledged    = module has read and understood this document hash
in_progress     = module is actively aligning with this document
applied         = module has applied the relevant requirement
deferred        = module intentionally postponed adoption
not_applicable  = document does not apply to this module
returned_for_fix = module found an issue and returned it for Blueprint clarification
superseded      = document or requirement has been superseded
Important Distinction

Acknowledging a document is not the same as fully applying it.

A module may acknowledge a standard and still need gradual work to fully align with it.

Example:

Folder Architecture Policy acknowledged.
Full historical refactor deferred.
New files must follow the policy immediately.
Old structure will be aligned gradually.
Dashboard Rule

A document awareness dashboard should not print every document by default.

Default dashboard output should summarize areas and show only documents that require attention.

Recommended area summary:

Area
Total documents
New documents
Changed documents
Acknowledged documents
In progress documents
Applied documents
Deferred documents
Highest priority
Recommended action

Recommended detail section:

Priority
Status
Path
Document hash
Recommended action
Recommended Colors

Terminal dashboards may use colors.

Recommended mapping:

bright green = applied
light green  = acknowledged
yellow       = in_progress
orange       = new / unseen
red          = critical changed / blocking / returned_for_fix
gray         = unchanged / low priority
cyan         = deferred / reference / not_applicable / superseded

Markdown and JSON reports must not rely only on colors. They must include explicit status text.

Context Bundle Rule

For a new module assistant or a heavily outdated module, Blueprint should generate a context bundle.

A context bundle is a single readable document that packages required or relevant coordination documents.

Recommended output:

reports/coordination_context_bundles/<module>__<scope>__<date>.md

Recommended scopes:

bootstrap
required
changed
critical
high
module
full

Meaning:

bootstrap = minimum context for a new module assistant
required  = critical/high required sources
changed   = only documents changed since the module ledger
critical  = critical sources only
high      = critical and high sources
module    = module-specific sources
full      = broad export, use carefully
Bundle Content

A context bundle should include:

manifest summary
source priority summary
document list
document contents grouped by source area
next prompt information when available
important warnings

The bundle is a delivery format, not the source of truth.

No Full Coordination Dump by Default

Modules should not blindly read all Blueprint coordination documents on every start.

Preferred behavior:

read manifest
compare hashes
show dashboard
read only new/changed/critical/high/relevant documents
defer low/reference documents when not relevant
New Assistant Bootstrap

For a new module assistant, the recommended first context is:

global policy
active governance standards
instruction intake
module policy
module prompt queue
next prompt
critical/high document summary
current module status if available

The operator may provide this as one generated Markdown bundle.

Module Start Behavior

After migration, a mature module `make module-start` should use the
canonical H4 startup sequence:

coordination-sync-check
module-sync
module-status
prompt-notify
prompt-read-next

`module-sync` remains network-independent and is responsible for module-local
snapshot synchronization plus document-awareness, coordination, and status
refresh. `governance-check` remains network-independent and covers module
policy and governance validation.

Module-side `blueprint-pull` is deprecated and must not be part of
`module-start`.

During transition, module assistants may still receive explicit context bundles or file contents from the operator.

Manual Delivery During Transition

Manual document delivery is acceptable during early migration.

However, the decision about what changed should come from the manifest/dashboard, not from guesswork.

Acceptable transition pattern:

operator runs awareness dashboard
assistant sees changed/high-priority documents
operator provides generated bundle or selected file contents
assistant updates module ledger/status after review
Generated Outputs

Generated outputs may include:

reports/coordination_awareness/document_manifest.json
reports/coordination_awareness/document_manifest.md
reports/coordination_context_bundles/<module>__<scope>.md

These generated outputs are not the source of truth unless explicitly promoted to coordination records.

Future Project Inspector Reuse

The same hash-based method may later be reused by ForPrint Project Inspector to detect:

possibly stale scripts
unused helpers
duplicate candidate files
files not touched or referenced for a long time
configuration drift

This policy focuses only on Blueprint coordination documents.

Migration Rule

Do not migrate all modules at once.

Preferred migration order:

1. policy and templates
2. source registry
3. manifest builder
4. dashboard renderer
5. context bundle generator
6. module local ledger template
7. Library or Blueprint pilot
8. gradual module adoption
Summary

Coordination document awareness should be:

hash-based
priority-aware
module-aware
dashboard-friendly
bundle-friendly
not manually guessed
not a full coordination dump by default
