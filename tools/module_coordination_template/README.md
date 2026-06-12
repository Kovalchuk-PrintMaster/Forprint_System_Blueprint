# ForPrint Module Coordination Template

This directory contains the canonical template area for module-side coordination automation.

The final scripts should support:

make coordination-records-refresh
make coordination-records-check
make prompt-completion-apply REPORT=coordination/reports/<file>.md
make prompt-completion-check

The completion report parser should rely on strict YAML frontmatter, not free-form human prose.
