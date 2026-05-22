
---

# 2. Файл: `coordination/outgoing_prompts/forprint_prepress_hub/drafts/2026-05-22-align-prepress-hub-with-blueprint.md`

```markdown
# Prompt: Align ForPrint Prepress Hub with ForPrint System Blueprint

## Target module

`forprint_prepress_hub`

## Purpose

This prompt aligns ForPrint Prepress Hub with the current ForPrint System Blueprint.

ForPrint Prepress Hub is responsible for file analysis, prepress checks, preparation workflows, preview generation and prepared print file lifecycle. It must not become CRM, Calculator, Library, Warehouse, or Accounting.

## Current architectural role

Prepress Hub should act as:

prepress file analysis + preparation service

It should receive a prepress job request, analyze files, determine readiness, produce reports/previews/prepared files, and return structured status to the workflow.

Prepress Hub may own

Prepress Hub may own:

prepress_job
prepress_analysis_report
prepress_job_status
prepared_print_file
preview_file
prepress processing logs
prepress preset execution results
Prepress Hub may consume

Prepress Hub may consume:

uploaded file references from CRM / Operational Registry / Gateway;
product configuration from Calculator / CRM context;
material and print constraints from forprint_library;
technical cards and print modes from forprint_library;
routed processing requests from forprint_integration_gateway.
Prepress Hub must not own

Prepress Hub must not become owner of:

client registry;
order registry;
payment status;
invoice;
product catalog as canonical source;
material catalog as canonical source;
price calculation logic;
warehouse stock;
delivery status.
Correct file-processing model

Preferred model:

incoming file reference
↓
prepress job request
↓
file analysis
↓
readiness decision
↓
optional automatic processing
↓
preview / report / prepared file
↓
structured status returned through contract

Prepress Hub can operate on files, but it should not silently move production files without traceable job status and audit/log output.

Key architectural risks
Prepress Hub starts owning order workflow.
Prepress Hub starts deciding pricing or business approval.
Prepress Hub hardcodes material/profile rules instead of consuming them from Library.
Prepress Hub silently modifies files without preview/report/audit.
Prepress Hub becomes tied too deeply to one Adobe-specific workflow too early.
Prepress Hub has no clear contract for input job request and output report.
Required alignment actions

Please review the current Prepress Hub concept/implementation and answer:

What is the current minimal processing pipeline?
What file states/directories are currently planned or implemented?
Which prepress objects should this module own?
Which constraints must come from Library?
Which requests should come through Integration Gateway?
Which statuses should be returned to CRM / Operational Registry?
Which parts are Adobe-dependent and which are generic?
Is there a clear prepress_analysis_report structure?
Is there a clear prepared_print_file lifecycle?
Are there any areas where Prepress is accidentally becoming CRM or production manager?
Expected deliverable from module assistant

Return a short alignment report:

1. Current Prepress Hub role
2. Current file-processing pipeline
3. Data/file objects owned by Prepress
4. Data consumed from Library / CRM / Gateway
5. Required input/output contracts
6. Detected architecture drift
7. Safe next implementation step
8. Open questions for Blueprint
Important rule

Do not build a full Adobe automation monster now.

The immediate goal is:

define a stable prepress job model, file states, input/output contracts and safe boundaries.