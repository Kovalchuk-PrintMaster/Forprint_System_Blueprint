# Standards Directory Policy

## Purpose

This policy defines how ForPrint Blueprint standards should be organized as the project grows.

The goal is to keep standards readable, easy to navigate, and easy for module assistants and future project inspection tools to consume.

## Core rule

Large standards topics should be grouped into thematic subdirectories.

Existing root-level standards may remain where they are until a separate migration checkpoint is explicitly approved.

New large standards packages should not be added as many unrelated files directly under `coordination/standards/`.

## Recommended structure

A standard topic package should use one directory under `coordination/standards/`.

Example:

coordination/standards/modular_topology_and_resilience/
  README.md
  index.yaml
  architecture_topology_policy.md
  data_ownership_and_storage_policy.md
  module_interaction_reliability_policy.md
  gateway_responsibility_policy.md
  module_global_context_policy.md

  Nesting rule

The normal maximum nesting depth is one topic directory below coordination/standards/.

Allowed:

coordination/standards/<topic_group>/<standard_document>.md

Avoid by default:

coordination/standards/<topic_group>/<sub_group>/<standard_document>.md

Deeper nesting may be used only for exceptional cases and should be approved deliberately.

Required files in a standards group

Each thematic standards directory should include:

README.md
index.yaml

README.md is the human navigation entry point.

index.yaml is the machine-readable group manifest.

Root standards index

The root file coordination/standards/index.yaml remains the global standards index.

It may reference both root-level standards and grouped standards by relative path.

Examples:

file: make_command_standard.md
file: governance/standards_directory_policy.md
file: modular_topology_and_resilience/module_interaction_reliability_policy.md
Existing standards

Existing standards should not be moved only for cosmetic reasons.

Moving existing standards requires a dedicated migration checkpoint because prompts, completion reports, validators and module snapshots may reference their current paths.

Prompt usage

Blueprint outgoing prompts should prefer referencing a standards group when a topic has multiple related documents.

Example:

coordination/standards/modular_topology_and_resilience/

Prompts may still reference individual standard documents when a specific file is required.

Future Project Inspector role

ForPrint Project Inspector should later verify that standards groups are complete and readable.

At minimum, it should be able to check:

group README exists;
group index exists;
documents listed in group index exist;
documents listed in the root standards index exist;
large new topics are grouped instead of scattered across the root directory.
Boundary

This policy defines standards organization only.

It does not define runtime architecture, database ownership, module interaction behavior, or business logic.
