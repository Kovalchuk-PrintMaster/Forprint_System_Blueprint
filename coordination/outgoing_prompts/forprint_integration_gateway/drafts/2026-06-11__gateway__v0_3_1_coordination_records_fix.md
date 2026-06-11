# Prompt: ForPrint Integration Gateway v0.3.1 — Coordination Records Fix and Self-Validation

Generated: `2026-06-11T14:45:49.474923+00:00`

## Target module

`forprint_integration_gateway`

## Source

This prompt is issued by `forprint_system_blueprint`.

Read it through:

```bash
make blueprint-prompts-list
make blueprint-prompt

Purpose

Fix Gateway v0.3 coordination records and add self-validation so future completion reports are written into module service files automatically and correctly.

This is a corrective governance prompt after Gateway v0.3 completion.

Do not change business runtime behavior.

Do not add live integrations.

Do not add database, queue, Redis, S3, external API, Telegram API, Website API, CRM API, Operational Registry API, or 1C writes.

Background

Gateway v0.3 was implemented and finalized.

Relevant commits:

3b4707a Add Gateway channel intake and handoff contracts
4b7821f Finalize Gateway v0.3 coordination and module ids

The final implementation is accepted in principle, but several module-local coordination records are not machine-clean.

Problems to fix
1. coordination/status/current_status.yaml contains placeholders

Current bad examples:

last_updated: "{now}"
branch: {branch}
last_commit: {commit}

It also marks completed checks as pending:

checks:
  make_check: pending
  make_check_report: pending
  governance_check: pending

These must be replaced with real values.

Expected:

real ISO timestamp;
branch main;
real short commit hash;
checks marked ok;
phase remains channel_intake_operational_handoff_contracts_v0_3;
last completed step remains gateway_channel_intake_contracts_ready.
2. coordination/prompts/index.yaml is malformed

Current bad shape:

"prompts: []
",

Replace it with valid YAML that records handled Blueprint prompts.

It must record:

prompt id: gateway_channel_intake_operational_handoff_contracts_v0_3;
source: forprint_system_blueprint;
status: completed_in_module;
implementation commit: 3b4707a;
finalization commit: current final Gateway commit;
phase and completed step.
3. coordination/reports/index.yaml needs finalization cleanup

It should include:

module id;
updated_at;
report id gateway_channel_intake_contracts_ready;
phase channel_intake_operational_handoff_contracts_v0_3;
status completed;
implementation commit 3b4707a;
finalization commit 4b7821f or current HEAD if this prompt creates a new finalization commit;
validation results;
explicit boundary confirmation.

It must stay tracked even if coordination/reports is ignored.

Use:

git add -f coordination/reports/index.yaml
4. Canonical module id guard

Gateway must not use non-canonical module ids.

Previously found and fixed:

forprint_calculator_engine

Canonical id:

calculator_engine

Add or keep a self-check that fails if forprint_calculator_engine appears in:

app
tests
scripts
examples
docs
coordination
reports
Required implementation

Add or update module-local automation so the assistant does not need to manually paste completion data into chat.

Suggested safe implementation:

scripts/update_gateway_coordination_records.py
scripts/check_gateway_coordination_records.py

Or equivalent existing structure.

The update script should write/refresh:

coordination/status/current_status.yaml
coordination/prompts/index.yaml
coordination/reports/index.yaml

The check script should validate:

YAML files are valid;
no unresolved placeholder tokens like now / branch / commit templates;
status phase and completed step match v0.3;
required validation fields are ok;
coordination/reports/index.yaml is tracked by Git;
no non-canonical forprint_calculator_engine string remains;
no live integration flags are enabled.

Add Make targets if appropriate:

make coordination-records-check
make coordination-records-refresh

At minimum, integrate the check into:

make check-report
Required validation before commit

Run:

make governance-check
make check
make check-report
make channel-intake-preview
git ls-files coordination/reports/index.yaml
grep -R "forprint_calculator_engine" -n app tests scripts examples docs coordination reports || true
git status --short

Expected:

all checks OK;
pytest still passes;
grep returns nothing;
coordination/reports/index.yaml is tracked;
working tree contains only intentional coordination/self-validation changes before commit.
Required commit

After checks are green:

git add coordination/status/current_status.yaml coordination/prompts/index.yaml
git add -f coordination/reports/index.yaml
git add Makefile scripts tests app docs examples
git commit -m "Fix Gateway v0.3 coordination records"
git push

Use a narrower git add if fewer files changed.

Boundary

This prompt is only about coordination records and self-validation.

Do not implement:

live API;
database;
queues;
Redis;
S3;
Telegram runtime calls;
Website runtime calls;
CRM runtime calls;
Operational Registry runtime calls;
1C writes;
automatic posting;
final price calculation.
