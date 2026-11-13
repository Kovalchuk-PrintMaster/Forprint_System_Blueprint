# ForPrint Legacy Compatibility and Retirement Policy v0.1

Status: active standard / v0.4.1 forward-architecture policy.

Owner: `forprint_system_blueprint`.

## Principle

Current architecture moves forward. Deprecated compatibility assets MUST NOT
define, constrain, or block the active release merely because they encode an
older workflow.

Legacy support exists only when it has concrete operational value.

## Classification

Every legacy component is classified in
`coordination/legacy/compatibility_registry_v0_1.yaml`.

- `current`: part of the active runtime and blocking current gates.
- `compatibility_supported`: intentionally supported for a bounded migration.
- `deprecated_candidate`: retained for forensic/manual compatibility, visible
  as an advisory, but non-blocking for current release gates.
- `historical_frozen`: retained as evidence/history and never executed by
  current gates.
- `retired`: preserved only in an immutable historical baseline or archive and
  removed from the current working architecture.

## Gate rule

`make check` and other current-release gates MUST exercise the current release
architecture. Deprecated compatibility tests/tools may be skipped or excluded
and MUST NOT turn the current release red solely because old assumptions no
longer hold.

A deprecated component may still block only when the current release explicitly
declares it as a compatibility dependency.

## Preservation and later cleanup

Do not delete legacy assets impulsively. First mark them, record their
replacement and retirement condition, and keep them available for forensic or
manual migration use.

After ecosystem rollout is complete, run an explicit retirement audit. Where a
legacy runtime must remain reproducible, prefer an immutable Git tag, dedicated
compatibility branch, or self-contained archive. Do not require the main current
tree to carry and continuously maintain every historical runtime forever.

## No backward architectural pressure

No new feature may be weakened or reshaped merely to satisfy a deprecated test,
validator, script, index shape, or protocol. If an active foundational rule is
too narrow for the current system, update the foundational rule.
