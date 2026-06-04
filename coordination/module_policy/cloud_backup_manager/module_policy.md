# Module Policy — Cloud Backup Manager

## Module ID

```text
cloud_backup_manager
```

## Priority

```text
p2
```

## Development status

```text
active_utility
```

## Strategic role

Infrastructure backup utility for project/server safety.

## Main goals

- `Backup important project/server data.`
- `Provide health/status checks for backup flows.`
- `Stay outside core business workflow ownership.`

## Owns

- `backup_jobs`
- `backup_targets`
- `backup_sources`
- `backup_health_reports`

## Must not own

- `business_workflow`
- `client_registry`
- `order_registry`
- `accounting_truth`
- `catalog_truth`

## Next focus

- `Keep as utility module.`
- `Later align coordination reporting with Blueprint.`

## Adoption rule

This module policy is strategic guidance. It does not automatically authorize large refactors or broad rewrites. The module should compare this policy with its current implementation and report alignment, conflicts or questions to Blueprint.
