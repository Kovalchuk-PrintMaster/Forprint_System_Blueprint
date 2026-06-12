# ForPrint Module Prompt Completion Protocol

Status: draft v0.1
Created: 2026-06-12T14:33:44.165569+00:00

Purpose

This protocol defines how module assistants complete Blueprint prompts without manually editing every coordination file.

A module completion report must contain strict machine-readable YAML frontmatter and optional human-readable text below it.

Required report location
coordination/reports/<prompt-or-step-id>_completion.md
Required YAML frontmatter
---
report_id: gateway_example_report
prompt_id: gateway_example_prompt
target_module: forprint_integration_gateway
phase: example_phase_v0_1
completed_step: example_step_ready
status: completed_in_module

implementation_commit: abc1234
completion_report_commit: abc1234

checks:
  governance_check: ok
  make_check: ok
  make_check_report: ok
  coordination_records_check: ok

boundary_confirmation:
  production_api_added: false
  live_external_integrations_added: false
  database_ownership_added: false
  operational_data_ownership_added: false
  queue_or_cache_dependency_added: false
  one_c_writes_added: false
  automatic_posting_added: false
  final_price_calculation_added: false

next_questions_for_blueprint:
  - "Accept completed prompt and issue next allowed prompt."
---
Required automation

A module should support:

make prompt-completion-apply REPORT=coordination/reports/<file>.md
make prompt-completion-check
make coordination-records-refresh
make coordination-records-check
Files updated by automation
coordination/status/current_status.yaml
coordination/prompts/index.yaml
coordination/reports/index.yaml
coordination/status/next_questions_for_blueprint.md
Rule

Human-readable report text may be flexible. YAML frontmatter must be strict.

Completion report validation v0.1

Completion reports should be validated before they are used to update module coordination records.

The validator must check:

- frontmatter exists;
- frontmatter YAML is valid;
- report_id is present;
- prompt_id is present;
- target_module is present;
- phase is present;
- completed_step is present;
- status is supported;
- implementation_commit is present;
- required checks are ok;
- required boundary confirmations are safe;
- next_questions_for_blueprint is a list when present;
- unresolved placeholders are absent;
- forbidden non-canonical module ids are absent.

The validator may support both boundary flag styles:

production_api_added: false

and:

no_production_api_added: true

The canonical module template should keep this command available:

make prompt-completion-check REPORT=coordination/reports/<file>.md
