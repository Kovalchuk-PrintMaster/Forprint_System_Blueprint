# ForPrint Module Coordination Records Protocol

Status: draft v0.1
Created: 2026-06-12T14:33:44.165569+00:00

Purpose

This protocol defines machine-readable coordination records every active module should maintain.

Required files
coordination/status/current_status.yaml
coordination/prompts/index.yaml
coordination/reports/index.yaml
coordination/status/next_questions_for_blueprint.md
Required checks

Coordination records must be valid YAML where applicable and must not contain unresolved placeholders.

Forbidden placeholder tokens:

{now}
{branch}
{commit}
{module_id}
{phase}
{completed_step}
{{now}}
{{branch}}
{{commit}}
Required report index tracking

Even if coordination/reports is ignored, this file must be tracked:

coordination/reports/index.yaml

Use:

git add -f coordination/reports/index.yaml
Required validation

A module-side checker must validate:

- module_id matches the manifest;
- current_status.yaml is machine-clean;
- prompts/index.yaml is machine-clean;
- reports/index.yaml is machine-clean and tracked;
- completed prompt status is not pending;
- required boundary flags are present;
- no forbidden live integration flags are enabled;
- no non-canonical module IDs are present;
- no unresolved placeholders remain.
