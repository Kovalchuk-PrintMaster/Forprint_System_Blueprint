# ForPrint Standards

## Purpose

This directory stores technical, structural and architectural standards for ForPrint modules.

Standards define the target direction for gradual module alignment.

They are not automatically equivalent to an active implementation prompt.

## Adoption mode

Blueprint standards are advisory by default unless a module-specific prompt, directive or architecture decision explicitly makes a standard mandatory for a checkpoint.

Module assistants should:

```text
read the standards;
compare them with the current repository;
report what already matches;
report what can be safely aligned in small steps;
report what is risky or impractical now;
ask Blueprint before large restructuring.
```

Unless a module-specific directive explicitly approves implementation, standards should be treated as:

alignment target;
discussion baseline;
future normalization direction;
not an immediate command to rewrite the project.
Standards organization

Root-level standards may remain directly under:

coordination/standards/

Large new standards topics should be grouped into thematic subdirectories.

Current standards groups:

coordination/standards/governance/
coordination/standards/modular_topology_and_resilience/
coordination/standards/third_party_reuse/

The root index remains the global entry point:

coordination/standards/index.yaml
Important standards packages
Governance
coordination/standards/governance/

Defines how standards themselves are grouped, indexed and maintained.

Modular topology and resilience
coordination/standards/modular_topology_and_resilience/

Defines ForPrint modular topology, data ownership, local-first storage, reliable handoff, Gateway responsibility, degraded mode and module global context.

Third-party reuse
coordination/standards/third_party_reuse/

Defines how ForPrint may evaluate, sandbox, reuse or depend on third-party tools without losing ownership of the domain core.

Core root-level standards

Important root-level standards include:

repository_structure_baseline.md
project_structure_standard.md
make_command_standard.md
module_assistant_start_protocol.md
module_standards_awareness_protocol.md
module_prompt_completion_protocol.md
module_governance_protocol.md
module_pre_commit_protocol.md
testing_and_check_report_standard.md
configuration_policy.md
How to use

Module assistants should read standards after pulling Blueprint updates.

Recommended starting point:

coordination/standards/index.yaml
coordination/standards/README.md
coordination/standards/module_assistant_start_protocol.md
coordination/standards/module_standards_awareness_protocol.md
coordination/standards/modular_topology_and_resilience/README.md
coordination/standards/third_party_reuse/README.md

If a standard can be applied safely in small steps, the module may apply it gradually.

If a standard conflicts with current module architecture, the module should report the conflict in:

coordination/status/next_questions_for_blueprint.md

or in the relevant completion report.

Completion reports

When relevant, completion reports should list reviewed standards or standards packages.

Example:

standards_reviewed:
  - coordination/standards/index.yaml
  - coordination/standards/module_standards_awareness_protocol.md
  - coordination/standards/modular_topology_and_resilience/
  - coordination/standards/third_party_reuse/
Safety

Do not perform large destructive restructuring only because a standard exists.

Prefer small, tested, reversible alignment steps.

Large migrations require a dedicated Blueprint-approved checkpoint.
