# ForPrint Module Sources Registry

## Purpose

This directory stores the registry of ForPrint module repositories and local paths.

The goal is to let ForPrint System Blueprint / future Control Plane know where to pull module repositories from and where to read their coordination status.

## Main file

```text
coordination/module_sources/module_git_sources.yaml
What this registry contains

For each module it records:

module_id
module_name
priority
development_status
local_path
repo_url
branch
coordination_root
status_file
prompt_index
report_index
repo_status
notes
Repo status values
confirmed
confirm_required
planned_not_created
Current use

For now this registry is maintained manually.

The owner / Blueprint assistant can use it to know:

which repositories exist;
where they are located locally;
which repositories still need path/remote confirmation;
where coordination/status files should appear;
which modules should be pulled later.
Future use

Later this registry can be used by a sync/status script or ForPrint Control Plane.

Future flow:

read module_git_sources.yaml
↓
git pull confirmed modules
↓
read coordination/status/current_status.yaml
↓
read coordination/prompts/index.yaml
↓
read coordination/reports/index.yaml
↓
generate ecosystem status report
Safety

This file must not contain secrets, tokens, passwords or private data.

Only repository paths, repository URLs and safe coordination metadata are allowed.


---
