# Prompt: Library Reference Contract Foundation v0.2

## Target module

`forprint_library`

## Working directory

`/srv/software_development/forprint-project/forprint_library`

## Blueprint directory

`/srv/software_development/forprint-project/forprint_system_blueprint`

## Current baseline

The latest known Library checkpoint is:

```text
781bb30 Refresh Library Blueprint standards snapshot
```

Previous Library semantic readiness work is already completed:

```text
935e51b Record Library semantic readiness completion
28fe2d0 Align Library make-first semantic readiness workflow
```

The module already has Make-first workflow targets and semantic/reference readiness checks.

## Purpose

Implement a small **Library Reference Contract Foundation v0.2** checkpoint.

The goal is to make Library references clearer and safer for downstream modules such as:

```text
calculator_engine
forprint_operational_registry
forprint_integration_gateway
telegram_bot
future forprint_crm
```

This is not a full production catalog implementation.

The goal is to define how other modules should refer to Library-owned semantic/catalog entities without copying Library ownership or inventing local canonical IDs.

## Required start workflow

Start with the standardized Make-first command:

```bash
make module-start
```

Then inspect the current state:

```bash
git status --short
git log -5 --oneline
find docs examples app tests coordination -maxdepth 3 -type f | sort | sed -n '1,260p'
```

Before adding files, review the current folder layout and respect the Blueprint Folder Architecture Policy.

Relevant Blueprint standard:

```text
coordination/standards/governance/folder_architecture_policy.md
```

Do not add new unrelated files into overcrowded flat directories. Prefer one thematic nesting level when useful.

## Main scope

Add or improve a small reference contract layer that documents and validates how downstream modules should store and exchange references to Library-owned entities.

The checkpoint should cover at minimum:

```text
canonical Library reference id format
reference type / entity type
display label
optional alias input
reference resolution status
source module
schema/version marker
deprecation handling
ambiguous/manual-review handling
unknown/unresolved references
example downstream payloads
```

The contract should make clear that downstream modules may store references to Library entities, but must not become the owner of Library semantic/catalog truth.

## Suggested files

Use existing structure where possible. Do not duplicate concepts if suitable files already exist.

Possible new or updated files:

```text
docs/reference_contract_foundation.md
docs/downstream_reference_contract_notes.md
examples/reference_contract/library_reference_examples.yaml
schemas/reference_contract/library_reference.schema.yaml
tests/content/test_library_reference_contract.py
```

If the repository already has better existing directories, use them instead.

Keep the folder structure shallow and thematic. Do not create deep nesting unless clearly justified.

## Expected contract examples

Include examples for at least:

```text
product_service
material
operation
unit
template
technical_card
```

Each example should show a safe downstream reference pattern.

Example concept, adapt to existing project conventions:

```yaml
library_reference:
  schema_version: library_reference_v0_2
  reference_type: product_service
  reference_id: product_service.business_card.standard
  display_label: Business card / standard
  resolution_status: library_reference_confirmed
  source_module: calculator_engine
  alias_input: "візитки стандарт"
```

Also include examples for:

```text
library_reference_pending
ambiguous_manual_review_required
deprecated_reference
unknown
```

## Boundary rules

Library owns:

```text
semantic/catalog IDs
product/service meaning
material meaning
operation meaning
template references
technical card references
aliases
deprecation rules
reference resolution semantics
```

Library must not own:

```text
order state
client database
pricing logic
warehouse stock truth
payment/accounting truth
CRM workflow state
Telegram runtime behavior
Integration Gateway delivery ledger
production runtime state
```

Do not implement:

```text
production catalog database
live API
CRM integration
Telegram integration
Operational Registry write
Calculator pricing logic
warehouse stock logic
accounting/payment logic
1C sync/write
automatic posting
production runtime service
```

Allowed:

```text
local docs
local YAML/JSON examples
schema files
tests for examples/schema
check-report visibility
small preview helper only if genuinely useful
```

## Check-report requirement

If possible, add or align one check-report row:

```text
Library reference contract foundation
```

Expected result:

```text
Reference contract docs, schemas and examples validate
```

The check should be OK only if the relevant docs/examples/schema exist and validate.

## Tests

Add focused tests only. Prefer thematic location according to Folder Architecture Policy.

Suggested test path:

```text
tests/content/test_library_reference_contract.py
```

Tests should verify:

```text
example file exists
required reference examples exist
schema/version field exists
reference_id/type/status fields exist
forbidden ownership language is not introduced
expected statuses are represented
```

Use the project's existing validation style where possible.

## Required validation

Run:

```bash
make lint
make test
make check-report
make governance-check
make module-validate
git diff --check
git status --short
```

If `make module-validate` regenerates reports or Blueprint standards snapshots, include only intentional tracked updates.

Do not commit until checks are green and the operator approves.

## Final response required

Return:

```text
changed files
created/updated docs
created/updated examples
created/updated schemas
created/updated tests
check-report rows added or changed
validation results
known deferred items
git status
commit recommendation
```

## Important

This checkpoint should remain small and safe.

Do not start full catalog expansion.

Do not create a production database.

Do not implement external integrations.

Do not change other modules.

Do not perform broad structural refactors unless needed for this checkpoint and explicitly justified.
