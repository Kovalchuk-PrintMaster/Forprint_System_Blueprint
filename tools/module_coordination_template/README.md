# ForPrint Module Coordination Template

This directory contains the canonical template area for module-side coordination automation.

The final scripts should support:

make coordination-records-refresh
make coordination-records-check
make prompt-completion-apply REPORT=coordination/reports/<file>.md
make prompt-completion-check

The completion report parser should rely on strict YAML frontmatter, not free-form human prose.

## Completion report validator

Template script:

```text
tools/module_coordination_template/validate_prompt_completion_report.py

When copied into a module, the expected module-side path is:

scripts/validate_prompt_completion_report.py

Expected usage:

python scripts/validate_prompt_completion_report.py coordination/reports/<file>.md --module-id <module_id>

The validator reads strict YAML frontmatter from a completion report and does not parse free-form human prose.
