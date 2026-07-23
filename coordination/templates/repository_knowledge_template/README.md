# ForPrint Repository Knowledge & Direction Protocol v0.2

This package defines a lightweight, manual snapshot system for preserving technical memory and strategic direction across ForPrint repositories.

It is intentionally simple. It does not introduce a service, database, dashboard or automated inspector.

## Three recurring artifacts

1. **Repository Capability Inventory (RCI)**
   What files, directories, scripts, dependencies, contracts and capabilities exist.

2. **Repository Execution & Dependency Map (REDM)**
   How important operational chains work from trigger to result.

3. **State, Direction & Rationale Snapshot (SDRS)**
   What the repository or whole system currently is, where it is going, why current work exists, what has already been completed, what is blocked and whether work remains aligned with stated goals.

## Profiles

### Blueprint profile

Blueprint creates two SDRS streams:

```text
direction/blueprint_coordination/
direction/system_portfolio/
```

- `blueprint_coordination` covers Blueprint's own coordination machinery, standards, prompt/review workflow, automation and control-plane roadmap.
- `system_portfolio` covers the whole ForPrint system, module balance, shared goals, dependencies, strategic direction and cross-module rationale.

### Module profile

Each module creates one SDRS stream:

```text
direction/module_self_view/
```

It records the module assistant's own evidence-based view of the module, without pretending to set whole-system priorities.

## Historical rule

Every review creates new dated files. Historical snapshots are never overwritten.
