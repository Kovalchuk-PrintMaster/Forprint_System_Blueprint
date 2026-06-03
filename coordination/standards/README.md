# ForPrint Standards

## Purpose

This directory stores technical and structural standards for ForPrint modules.

These standards are not always immediate mandatory rewrites.

They define the target direction for gradual module alignment.

## Adoption mode

These standards are currently target/advisory standards.

They define the preferred direction for future module alignment, but they do not automatically authorize large structural rewrites.

Module assistants should:

```text
read the standards;
compare them with the current repository;
report what already matches;
report what can be safely aligned in small steps;
report what is risky or impractical now;
ask Blueprint before large restructuring.
Unless a module-specific directive explicitly approves implementation, standards should be treated as:

alignment target
discussion baseline
future normalization direction

not as an immediate command to rewrite the project.


---

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
