# ForPrint Standards

## Purpose

This directory stores technical and structural standards for ForPrint modules.

These standards are not always immediate mandatory rewrites.

They define the target direction for gradual module alignment.

## Standards currently tracked

```text
repository_structure_baseline.md
make_command_standard.md
configuration_policy.md
How to use

Module assistants should read these standards after pulling Blueprint updates.

If a standard can be applied safely in small steps, the module should apply it gradually.

If a standard conflicts with current module architecture, the module should report the conflict in:

coordination/status/next_questions_for_blueprint.md
Safety

Do not perform large destructive restructuring only because a standard exists.

Prefer small, tested, reversible alignment steps.


---
