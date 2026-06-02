# ForPrint Ecosystem Checkup

## Purpose

This directory stores the planned policy and configuration for future ecosystem-level checkups.

The goal is to detect:

```text
stale high-priority modules;
modules that did not pull or acknowledge current instructions;
missing coordination files;
blocked modules;
modules moving outside priority;
modules waiting for Blueprint decisions;
modules with failed checks.
Current status
planned_skeleton

No full automation is implemented yet.

Future command

Preferred future command:

make ecosystem-check

Possible internal steps:

1. pull confirmed module repositories;
2. read module coordination files;
3. compare module activity with priority;
4. detect stale modules;
5. detect missing directive acknowledgement;
6. generate ecosystem report.
Configuration files
ecosystem_checkup_policy.yaml
module_activity_thresholds.yaml
Current approach

For now, Blueprint uses a lightweight collector for selected modules.

The first test module is:

calculator_engine

---
