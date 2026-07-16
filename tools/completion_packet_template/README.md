# Completion Packet Template

Status: reference template v0.1

## Purpose

This template defines the preferred ForPrint module workflow for completing prompts with a small structured YAML packet instead of manually editing every coordination file.

The template is contract-first, not script-first.

Blueprint provides:

- a required completion packet shape;
- validation expectations;
- idempotency rules;
- coordination update expectations;
- a reference implementation that modules may adapt.

Modules may adapt the scripts to their local coordination schema, but must preserve the contract.

## Required workflow

A module assistant should complete a prompt using this flow:

```text
completion packet YAML
  -> validate completion packet
  -> apply completion packet
  -> generate/update completion report
  -> update reports index
  -> update current status YAML/Markdown
  -> update next questions for Blueprint when present
  -> run check-report/check/governance-check
Required packet fields

The packet must include:

completion_id
module_id
module_name
phase
prompt_id
report_id
report_path
created_at
summary
implemented
checks
instruction_sources_reviewed
standards_reviewed
standards_alignment_notes
boundary_confirmation
current_outputs
next_recommended_steps
next_questions_for_blueprint
Required metadata

The packet must include non-empty lists for:

instruction_sources_reviewed
standards_reviewed
standards_alignment_notes

This ensures every completion record can answer:

which assistant instruction sources were reviewed;
which Blueprint/module standards were reviewed;
how the work aligned with those standards.

standards_reviewed may include specific files or thematic standards packages.

Examples:

standards_reviewed:
  - forprint_system_blueprint/coordination/standards/index.yaml
  - forprint_system_blueprint/coordination/standards/module_prompt_completion_protocol.md
  - forprint_system_blueprint/coordination/standards/modular_topology_and_resilience/
  - forprint_system_blueprint/coordination/standards/third_party_reuse/
Boundary confirmation

The packet must include machine-readable boundary confirmation.

Required baseline flags:

boundary_confirmation:
  no_production_api: true
  no_live_external_integrations: true
  no_real_1c_sync: true
  no_production_write: true
  no_automatic_posting: true

Modules may add stricter local flags, such as:

  no_accounting_payment_truth: true
  no_crm_dashboard: true
  no_telegram_runtime_ui: true
  no_calculator_final_price_ownership: true
  no_library_catalog_ownership: true
  no_warehouse_stock_truth: true
Idempotency requirements

Completion automation must be idempotent.

Running the apply command twice for the same packet must not:

duplicate reports/index.yaml entries;
append duplicate Markdown blocks;
rewrite files only because of timestamps;
create meaningless git diffs;
change generated runtime reports under reports/.

Timestamp fields should come from the packet, not from datetime.now() during every apply run.

Expected module Make targets

Modules adopting this template should expose:

completion-packet-validate
completion-packet-apply

Recommended usage:

make completion-packet-validate PACKET=coordination/completion_packets/examples/example.yaml
make completion-packet-apply PACKET=coordination/completion_packets/examples/example.yaml
Expected check-report rows

Modules adopting this template should add check-report rows equivalent to:

Completion packet automation files
Completion packet example validation

If the module also has Blueprint snapshot sync, it should add an idempotency check equivalent to:

Blueprint sync idempotency
Standards packages

Completion packets should gradually report reviewed standards packages when relevant.

Important packages include:

forprint_system_blueprint/coordination/standards/modular_topology_and_resilience/
forprint_system_blueprint/coordination/standards/third_party_reuse/

Modules that touch runtime integration, Gateway, data ownership, queues, databases, external tools, BI, authentication or cross-module handoff should normally include these packages in standards_reviewed.

Reference implementation

This template includes reference scripts:

validate_completion_packet.py
apply_completion_packet.py

They are intentionally simple and deterministic.

Modules may copy and adapt them, but must keep:

packet validation;
safe boundary flags;
instruction/standards metadata;
deterministic report rendering;
no duplicate report entries;
no timestamp-only churn;
explicit check-report integration.

<!-- blueprint-side-completion-intake-v0-1:start -->

## Blueprint-side completion intake

The module-side completion packet is also the preferred evidence source for Blueprint review.

The cross-repository lifecycle is:

```text
module completion packet
-> module validation and push
-> Blueprint intake preview
-> Blueprint acceptance or return decision
-> Blueprint review packet
-> Blueprint prompt queue update
-> Blueprint roadmap evidence update
-> next-work suggestion
```

Blueprint-side commands are owned by the Blueprint repository:

```text
make completion-intake-preview MODULE=<module> MODULE_ROOT=<path> PACKET=<packet>
make completion-accept MODULE=<module> MODULE_ROOT=<path> PACKET=<packet>
make completion-return MODULE=<module> MODULE_ROOT=<path> PACKET=<packet> REVIEW_NOTES="..."
make next-work-suggestion MODULE=<module>
```

The Blueprint intake tool is read-only toward the module repository. It may inspect the packet, report, Git commits and remote containment, but it must not modify module files.

Acceptance does not automatically generate or activate the next prompt.

The next-work resolver uses this order:

```text
active approved prompt;
matching draft candidate;
next roadmap step;
undefined-work warning.
```

All promotion and activation decisions remain explicit Blueprint actions.

<!-- blueprint-side-completion-intake-v0-1:end -->

## Reporting evidence contract v0.1

Completion packets may include a top-level `reporting_evidence` mapping.
The mapping is conditional: use it when the module has reporting, audit or
status-output work.

Recommended fields:

```yaml
reporting_evidence:
  compact_check_report: make check-report
  full_diagnostics: make check-report-full
  artifact_paths:
    - reports/<module>_check_report.json
    - reports/<module>_check_report.md
  no_color_verified: true
  read_only_checks_verified:
    - make coordination-check
    - make module-policy-check
  recovery_document: docs/operations/<reporting-change>-recovery.md
  deviations: []
```

Rules:

- do not invent artifacts that the module does not produce;
- preserve target names and exit codes;
- keep failures visible in compact output;
- record `NO_COLOR=1` only when color exists;
- record read-only verification only for commands documented as read-only;
- list known deviations instead of hiding them.
