# Module Policy — ForPrint System Administration

## Module ID

```text
forprint_system_administration
```

## Priority

```text
p2
```

## Development status

```text
planned_non_blocking_support
```

## Strategic role

Central IT/workplace administration surface for approved software, endpoint operations, backups, disk health and workstation consistency.

## Main goals

- `Provide the FP Administration web portal.`
- `Use a constrained Device/Endpoint Agent for typed local operations.`
- `Maintain approved/tested software, version and configuration profiles.`
- `Integrate existing backup and disk-health capabilities instead of duplicating them.`
- `Prepare future workstation onboarding and operational-readiness controls.`

## Owns

- `administration_portal`
- `approved_software_catalog`
- `endpoint_operation_contract`
- `workstation_profile`
- `administrative_health_view`

## Must not own

- `business_workflow`
- `accounting_truth`
- `canonical_order_registry`
- `arbitrary_remote_shell_authority`
- `license_entitlement_outside_authorized_policy`

## Next focus

- `Remain non-blocking for current core development.`
- `Become a future workplace/operational readiness gate before broad rollout.`

## Adoption rule

This module policy is strategic guidance. It does not automatically authorize large refactors or broad rewrites. The module should compare this policy with its current implementation and report alignment, conflicts or questions to Blueprint.
