# ForPrint System Administration — concept v0.1

## Canonical working name

`forprint_system_administration`

User-facing working portal/menu label may be `FP Administration`.

## Strategic role

Central company IT/workplace administration surface for ForPrint-managed servers and employee
workstations.

The module should consolidate otherwise fragmented utilities into one controlled operational view.

## Current/non-new capabilities to integrate

Existing capabilities already available elsewhere should be referenced/integrated rather than
rewritten blindly:

- Cloud Backup Manager;
- weekly disk-health monitoring utilities for the owner's local servers.

The module may orchestrate and display those capabilities while their implementation remains separate.

## Web-first architecture

Primary administration UI is a server-hosted web application.

A Windows context-menu entry may open the relevant web portal/context.

The browser itself cannot perform privileged local actions such as installing drivers. Therefore
managed workstations may run a small trusted Endpoint/Device Agent.

Conceptual chain:

`Windows context menu → FP Administration web portal → authorization → typed endpoint operation → local agent → evidence/report`

The agent is initially an internal component, not a separate top-level module.

## Agent safety

The local agent should not expose unrestricted arbitrary remote shell execution.

Prefer typed allow-listed operations such as:

- `INSTALL_SOFTWARE`
- `INSTALL_DRIVER`
- `APPLY_PROFILE`
- `CLEAN_TEMP`
- `CHECK_DISK`
- `COLLECT_HEALTH`
- `UPDATE_PACKAGE`
- `RESTART_SERVICE`

PowerShell/Bash/installers may be implementation details inside approved operations.

## Software catalog

Maintain a controlled catalog of approved/tested software:

- product;
- version;
- installer/artifact;
- checksum;
- supported OS;
- default configuration profile;
- optional plugins;
- role applicability;
- tested/approved status;
- licensing/entitlement notes.

Multiple versions may need to remain available because printing/design workflows can depend on file
compatibility across Illustrator/Acrobat/etc versions.

## Company workstation profile

Installation can optionally/automatically apply the accepted company environment:

- hotkeys;
- palettes;
- scripts/actions;
- plugins;
- presets;
- application configuration;
- common tools.

The goal is predictable workstations rather than each employee inventing a different environment.

## Acrobat/plugin handling

Support optional plugin selection because not every role needs every plugin.

Different plugin install modes may exist:

- simple copy to plugin directory;
- installer-based;
- license/entitlement-dependent.

Licensing/compliance remains a formal boundary; the system deploys only authorized software.

## Driver/equipment deployment

Provide approved installation flows for:

- printers;
- shared office equipment;
- other managed devices.

Driver + required standard settings should be centrally controlled where practical.

## Routine workstation support

Potential low-risk functions:

- clean temp/cache files;
- empty recycle-bin according to policy;
- collect disk/OS health;
- basic diagnostics;
- approved updates;
- standard application installation/update;
- workstation onboarding/recovery.

## Dashboard direction

Future dashboard may show:

- backups;
- disk health;
- endpoint health;
- agent status;
- software compliance/version drift;
- failed deployments;
- pending updates;
- recent administrative actions.

## Blocking class

Non-blocking for current core development.

Likely future `PHASE_GATE_BLOCKING` requirement before broad workplace/production rollout.
