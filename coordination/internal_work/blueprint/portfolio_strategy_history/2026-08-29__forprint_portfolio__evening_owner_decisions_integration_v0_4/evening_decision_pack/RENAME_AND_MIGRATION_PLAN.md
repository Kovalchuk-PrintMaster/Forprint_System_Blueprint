# Rename plan — Operational Registry -> Operations Control Registry

Old display name:
`Operational Registry`

New display name:
`Operations Control Registry`

Proposed technical ID:
`operations_control_registry`

## Next-day controlled migration

1. Discover actual project directory and all current references.
2. Use today's inventory outputs plus a fresh repository-wide search.
3. Rename the not-yet-implemented project/directory where appropriate.
4. Update current roadmap/module sheets, maps, manifests, dependencies, policies, templates, tests and indexes.
5. Do not blindly rewrite historical snapshots.
6. Add alias/migration note where compatibility requires it:
   `operational_registry -> operations_control_registry`.
7. Verify no current-looking unresolved old-ID references remain.
8. Run full Blueprint checks.
9. Publish only after clean PASS.

This rename must not modify current release authority or activate runtime capability.
