# Blueprint Incoming Requests

## Purpose

`coordination/incoming_requests/` is the Blueprint-owned intake surface for module-to-
Blueprint architecture, ownership, coordination and governance requests.

Current routing uses **canonical module IDs** from
`machine/module_identity_registry.yaml`.

Each current module route has:

```text
coordination/incoming_requests/<canonical_module_id>/
├── new/
├── reviewed/
└── archived/
```

`new/` is the intake lane. `reviewed/` and `archived/` are lifecycle organization
surfaces; they do not create a second architecture authority.

## Historical aliases

The following legacy directories are retained only because they contain or preserve
historical evidence:

```text
coordination/incoming_requests/accounting_registry_service/
coordination/incoming_requests/forprint_operational_registry/
```

They are not current routing targets.

Current requests must use:

```text
coordination/incoming_requests/forprint_accounting_registry_service/
coordination/incoming_requests/forprint_operations_control_registry/
```

Historical request documents are not renamed merely to make old evidence look current.

## Navigation and validation

Derived route coverage is available in:

```text
indexes/incoming_requests.yaml
```

The specialized index validator requires every canonical module ID to have a complete
`new/`, `reviewed/`, and `archived/` route and prevents historical aliases from regaining
current authority.

`indexes/` remains derived and non-authoritative.
