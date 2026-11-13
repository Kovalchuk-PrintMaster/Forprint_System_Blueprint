# Deferred Module Disposition Register v0.2

Status: `DEFER_UNTIL_PORTFOLIO_PASS`

No module here is retired. We only postpone final role/retain/merge/retire decisions until the
main portfolio capability map is clearer.

| Module | Current hypothesis | Why defer | Later decision |
|---|---|---|---|
| `forprint_operations_control_registry` | Possible operational data/registry backbone. | Exact canonical entities and overlap with CRM, Calculator, Accounting, Library and warehouse capability remain unclear. | Retain / redefine / merge / retire after full capability map. |
| `production_runtime_inspector` | Possible runtime/production observation capability. | Likely overlap with Project Inspector, System Administration and production monitoring. | Prove unique lifecycle/ownership or merge/retire. |
| `warehouse_service` | Physical stock/availability/movement capability is likely needed. | Need to decide whether it justifies a dedicated module or belongs in another operational layer. | Resolve after Accounting/Calculator/Operations/Registry analysis. |
| `forprint_contract_registry` | Could own lifecycle/catalog of versioned inter-module contracts. | May overlap Blueprint, Library and Integration Gateway; independent value not yet proven. | Retain only if contract lifecycle/version/adoption governance is substantial enough. |

Decision test:
1. list still-unowned capabilities;
2. list overlaps;
3. re-read historical evidence;
4. define minimum durable responsibility set;
5. ask whether there is an independent lifecycle/source-of-truth boundary and enough work;
6. never invent work merely to justify an existing module name.
