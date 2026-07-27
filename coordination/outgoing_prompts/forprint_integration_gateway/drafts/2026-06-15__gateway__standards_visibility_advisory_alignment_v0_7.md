# Prompt: ForPrint Integration Gateway v0.7 — Blueprint Standards Visibility and Advisory Alignment

Generated: `2026-06-15T16:27:07.642237+00:00`

## Purpose

Align `forprint_integration_gateway` with Blueprint standards visibility and advisory requirements while preserving module boundaries and avoiding live integration changes.

## Target module

`forprint_integration_gateway`

## Source

This prompt is issued by `forprint_system_blueprint`.

Read it through:

```bash
make blueprint-prompts-list
make blueprint-prompt

Purpose

Gateway v0.7 must learn to continuously see and read Blueprint standards.

This prompt does not require Gateway to fully implement every Blueprint standard immediately.

Standards are advisory / gradual-alignment guidance unless they are explicitly referenced by an active prompt or active directive.

Gateway must add a standards visibility layer so the module can:

list Blueprint standards;
confirm Blueprint standards index is readable;
record that standards were reviewed;
include standards visibility in governance/check-report;
gradually align with standards in small safe steps.

This checkpoint is still offline / contract-only / governance-only.

Do not implement live runtime delivery.

Accepted baseline

Accepted Gateway baseline:

7d74ec1 Add Gateway contract release and consumer acceptance
3690cc3 Add Gateway v0.6 coordination report
5813c65 Fix Gateway v0.6 coordination records

Expected current state:

current_phase: contract_release_consumer_acceptance_v0_6
last_completed_step: gateway_contract_release_ready
make check: OK
make check-report: OK
contract-release-preview: OK
consumer-acceptance-preview: OK
backward-compatibility-preview: OK
Blueprint standards baseline

Blueprint now owns a standards index:

coordination/standards/index.yaml
coordination/standards/module_standards_awareness_protocol.md

Gateway must read this as advisory guidance.

Required targets

Add module-side targets:

make blueprint-standards-list
make blueprint-standards-check
make blueprint-standards-sync
blueprint-standards-list

Must show:

standards index path;
number of standards;
standard id;
file path;
status;
adoption mode.
blueprint-standards-check

Must verify:

Blueprint repository path is configured/reachable;
coordination/standards/index.yaml exists in Blueprint;
standards index is valid enough for Gateway visibility;
standards files referenced by index exist;
advisory semantics are explicit;
no hard enforcement is implied by standards alone.
blueprint-standards-sync

Must create or refresh a local Gateway snapshot, for example:

coordination/standards/blueprint_standards_snapshot.yaml

The snapshot must be source-controlled and include:

source Blueprint path;
snapshot timestamp;
standards index version;
standards count;
reviewed standards list;
advisory semantics confirmation;
Gateway-specific alignment notes.

This sync must not copy all standards documents unless explicitly needed.

It should be a lightweight visibility snapshot.

Required Gateway behavior

Gateway must understand this distinction:

outgoing_prompts = concrete work to do now
standards        = continuously readable guidance and target direction
directives       = mandatory rule when explicitly active/blocking
global_policy    = ecosystem-wide constraints and doctrine

Gateway must not treat standards as automatic destructive refactor orders.

Gateway should report standards conflicts instead of applying large rewrites.

Required check-report integration

Extend make check-report so it includes:

Blueprint standards visibility: OK

The check should pass when Gateway can read the Blueprint standards index and local standards snapshot is current enough.

This check is not full compliance with every standard.

It is a visibility/advisory-awareness check.

Required governance integration

make governance-check should include or call standards visibility validation.

Existing governance outputs may remain lightweight, but the result must show that standards are reachable/readable.

Required completion report fields

Gateway v0.7 completion report must include human-readable text and machine-readable/structured content that mentions:

standards_reviewed:
  - coordination/standards/index.yaml
  - coordination/standards/module_standards_awareness_protocol.md
  - coordination/standards/module_governance_protocol.md
  - coordination/standards/module_make_target_contract.md

standards_alignment_notes:
  - "Gateway added standards visibility without forcing full compliance."
  - "Standards remain advisory unless activated by prompt/directive."
  - "No destructive refactor was performed."
Required coordination update

Update:

coordination/status/current_status.yaml
coordination/prompts/index.yaml
coordination/reports/index.yaml
coordination/status/next_questions_for_blueprint.md

Expected phase:

blueprint_standards_visibility_advisory_alignment_v0_7

Expected completed step:

gateway_blueprint_standards_visibility_ready

Add completion report under:

coordination/reports/

The report must be tracked even if coordination/reports is ignored.

Required tests/checks

Add tests for:

standards index reader;
standards list output;
standards check;
standards sync snapshot;
check-report integration;
no hard enforcement of all standards.
Required validation before commit

Run:

find app tests scripts examples docs coordination reports contracts -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +

make governance-check
make check
make check-report

make blueprint-standards-list
make blueprint-standards-check
make blueprint-standards-sync

make channel-intake-preview
make adapter-readiness-preview
make compatibility-matrix-preview
make replay-fixtures-preview
make contract-release-preview
make consumer-acceptance-preview
make backward-compatibility-preview

legacy_calculator_module_id="forprint_"'calculator_engine'
grep -R --exclude-dir="__pycache__" --exclude="*.pyc" "$legacy_calculator_module_id" -n app tests scripts examples docs coordination reports contracts || true

grep -R --exclude-dir="__pycache__" --exclude="*.pyc" -E "^[[:space:]]*(live_delivery_enabled|is_live_delivery_enabled|one_c_writes_added|automatic_posting_added|final_price_calculation_added): true" -n app tests scripts examples docs coordination reports contracts || true

git ls-files coordination/reports/index.yaml
git status --short

Expected:

all checks OK;
pytest passes;
standards list/check/sync OK;
check-report includes standards visibility OK;
all v0.3/v0.4/v0.5/v0.6 previews remain OK;
no live delivery introduced;
no 1C writes;
no automatic posting;
no final price calculation;
no database/queues/Redis/S3 ownership introduced.
Commit expectation

After checks are green:

git commit -m "Add Gateway Blueprint standards visibility"
git push

Use staged commits if needed.

Boundary

Do not implement:

live API;
database ownership;
queues;
Redis;
S3;
Telegram runtime calls;
Website runtime calls;
CRM runtime calls;
Operational Registry runtime calls;
Calculator runtime calls;
Library runtime calls;
Prepress runtime calls;
Accounting runtime calls;
1C writes;
automatic posting;
final price calculation;
full forced implementation of every Blueprint standard.

Gateway remains offline / contract-only / validation-routing / standards-visible boundary.
