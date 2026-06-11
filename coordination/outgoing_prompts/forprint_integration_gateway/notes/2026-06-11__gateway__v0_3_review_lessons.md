# Gateway v0.3 Review Lessons

Created: `2026-06-11T14:17:11.237102+00:00`

## Context

During review of Gateway v0.3 `channel_intake_operational_handoff_contracts_v0_3`, two small governance/architecture issues were found and fixed before acceptance.

Final Gateway commit:

```text
4b7821f Finalize Gateway v0.3 coordination and module ids
Lesson 1 — Canonical module IDs only

Gateway examples, routes, services and tests must use canonical Blueprint module IDs.

Incorrect module id found during review:

forprint_calculator_engine

Correct canonical module id:

calculator_engine

Rule:

Before completing future Gateway prompts, search for non-canonical module IDs:

grep -R "forprint_calculator_engine" -n app tests scripts examples docs coordination reports || true

If found, replace with:

calculator_engine

Gateway must not invent module IDs. Use the IDs defined by ForPrint System Blueprint.

Lesson 2 — coordination/reports/index.yaml must be tracked

Gateway .gitignore may ignore coordination/reports.

However, the governance coordination file must still be tracked:

coordination/reports/index.yaml

If Git warns that coordination/reports is ignored, use:

git add -f coordination/reports/index.yaml

Before completion, verify:

git ls-files coordination/reports/index.yaml

Expected output:

coordination/reports/index.yaml
Required future Gateway completion checklist

Before final commit of any future Gateway Blueprint prompt, run:

make governance-check
make check
make check-report
make channel-intake-preview
grep -R "forprint_calculator_engine" -n app tests scripts examples docs coordination reports || true
git ls-files coordination/reports/index.yaml
git status --short

Acceptance rule:

checks must pass;
grep for non-canonical calculator id must be empty;
coordination/reports/index.yaml must be tracked;
no live API/DB/queue/external runtime calls may be introduced unless Blueprint explicitly approves.
