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

Completion packet workflow v0.2

Status: preferred workflow for new module completion automation.

The v0.1 YAML-frontmatter completion report remains supported for legacy module templates. For new module rollout work, the preferred workflow is a completion packet.

A completion packet is a small structured YAML file that contains enough information to generate or update all required coordination records.

Required packet fields:

completion_id:
module_id:
module_name:
phase:
prompt_id:
report_id:
report_path:
created_at:
summary:
implemented:
checks:
instruction_sources_reviewed:
standards_reviewed:
standards_alignment_notes:
boundary_confirmation:
current_outputs:
next_recommended_steps:
next_questions_for_blueprint:

Required automation targets:

completion-packet-validate
completion-packet-apply

Required coordination outputs:

coordination/reports/completion/<report>.md
coordination/reports/index.yaml
coordination/status/current_status.yaml
coordination/status/current_status.md when present
coordination/status/next_questions_for_blueprint.md when questions are present

Required validation rules:

packet root is a YAML mapping;
all required fields are present;
report_path is under coordination/reports/completion/;
checks include check_report, tests, and governance_check;
instruction_sources_reviewed is non-empty;
standards_reviewed is non-empty;
standards_alignment_notes is non-empty;
standards_reviewed may include specific standard files or thematic standards package directories;
modules that touch runtime integration, Gateway, data ownership, queues, databases, external tools, BI, authentication or cross-module handoff should include modular_topology_and_resilience and third_party_reuse when relevant;
boundary_confirmation contains machine-readable safe boundary flags;
next_questions_for_blueprint is a list.

Required idempotency rules:

applying the same packet twice must not duplicate report index entries;
applying the same packet twice must not duplicate Markdown blocks;
applying the same packet twice must not rewrite files only because of timestamps;
automation must avoid generated runtime reports under reports/;
timestamps should come from packet fields, not from current wall-clock time.

Blueprint reference template:

tools/completion_packet_template/

Modules may adapt the reference scripts to their local coordination schema, but must preserve the packet contract, validation behavior, idempotency behavior, boundary confirmation, reviewed instruction metadata and reviewed standards metadata.

Recommended standards metadata example:

```yaml
standards_reviewed:
  - forprint_system_blueprint/coordination/standards/index.yaml
  - forprint_system_blueprint/coordination/standards/module_prompt_completion_protocol.md
  - forprint_system_blueprint/coordination/standards/modular_topology_and_resilience/
  - forprint_system_blueprint/coordination/standards/third_party_reuse/

standards_alignment_notes:
  - "No destructive rewrite was performed."
  - "Reviewed modular topology and resilience standards for ownership and handoff boundaries."
  - "Reviewed third-party reuse policy; no new production third-party dependency was introduced."
