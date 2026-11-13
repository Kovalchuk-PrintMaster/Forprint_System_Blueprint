# ForPrint System Administration — evening first-pass owner review

Module: `forprint_system_administration`

Status: `FIRST_PASS_OWNER_DIRECTION_RECORDED / SYNTHETIC_MICROSTEPS_PENDING_SECOND_PASS`

## AGREED_WITH_OWNER

System Administration manages workstations, servers, network devices, printers/scanners, approved software,
drivers, configuration profiles, health, recovery and consistency.

Core design: central control plane plus a local autonomous endpoint agent that retains useful diagnostic/recovery
capability when internet or central connectivity fails.

## Working boundary

System Administration executes approved endpoint/fleet policy. Project Inspector audits compliance.
Cloud Backup Manager may later be absorbed as backup/artifact-sync capability if evidence supports it.

Avoid unrestricted remote shell as default; endpoint operations should be typed, allowlisted and auditable.

## Synthetic roadmap expansion for pass 2

Everything below is `SYNTHETIC_CANDIDATE` unless explicitly described as owner direction.

### SYS-R0 — Fleet/device/software inventory
- discover workstations/servers/network devices/printers/scanners
- hardware/software/driver/profile baseline
- approved vs unmanaged state
- new-device detection
### SYS-R1 — Central plane + local agent
- central policy/status UI
- endpoint agent with typed operations
- local emergency diagnostics
- secure privilege boundary
### SYS-R2 — Offline recovery
- minimal emergency cache
- network/driver/DNS/IP/disk diagnostics
- last-known-good profile
- fallback local cache -> LAN repo -> internet/vendor
### SYS-R3 — Driver/software/artifact repository
- stable approved versions
- device-specific bundles
- rollback/compatibility metadata
- Backup Manager distribution integration
### SYS-R4 — New-device onboarding
- identify hardware/model
- resolve driver/config
- build/install bundle
- trigger Operations Assistant documentation/media request
### SYS-R5 — Fleet consistency/rollout
- desired profiles
- drift detection
- staged rollout waves
- rollback/maintenance windows
### SYS-R6 — Health/repair
- disk/OS/network/printer diagnostics
- safe automated fixes
- confirmation-required disruptive fixes
- audit/post-repair verification
### SYS-R7 — Backup/sync absorption evaluation
- evaluate Cloud Backup Manager maturity
- preserve working code
- merge only if lifecycle becomes cleaner
- avoid duplicate implementations

## Dependencies

Project Inspector, Operations Assistant, Library, Cloud Backup Manager, Identity & Access and vendor/device sources.

## Open questions for pass 2

Local-agent autonomy; offline cache size; secrets/elevation; discovery trust; license-sensitive updates;
final Backup Manager absorption.

## Target milestone

Core IT failures can be diagnosed/recovered during connectivity loss and the fleet stays close to known-good state.

## Steady state

Continue measured improvement after the target milestone; the module is not considered permanently finished.
