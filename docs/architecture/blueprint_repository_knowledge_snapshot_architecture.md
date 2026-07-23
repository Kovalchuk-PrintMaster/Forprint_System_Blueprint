# Blueprint Repository Knowledge Snapshot Architecture

## Model

```text
RCI  → what exists, purpose, evidence, confidence and unknowns
REDM → triggers, ordered execution, side effects, failures and recovery
SDRS blueprint_coordination → Blueprint control-plane state and direction
SDRS system_portfolio → whole-system goals, balance, dependencies and rationale
```

## Profiles

Blueprint local:

```text
coordination/repository_knowledge/direction/
├── blueprint_coordination/
└── system_portfolio/
```

Module distribution:

```text
coordination/templates/repository_knowledge_template/direction/
└── module_self_view/
```

## Sources

Snapshots consume Git metadata, machine architecture, policy, registries,
queues, roadmaps, completion evidence, scripts/tests and operator validation.

They do not replace those sources.

## Rules

- New date means new file.
- Historical snapshots are immutable.
- `READY_WITH_UNKNOWNS` is valid.
- Candidate status is not deletion approval.
- No implementation file is changed by the snapshot procedure.
- Module proposals are not Blueprint decisions.

## Integration

Repository knowledge is added to the document awareness source registry with
high priority and `review_before_next_prompt`.

The current collector remains a temporary `tmp.py` operator tool. No database,
service or permanent automation front is introduced.

## Future

Project Inspector may later automate collection, reference graphs, duplicate
signals, dependency usage, flow reconstruction, comparison and unknown tracking
while preserving the same honesty model.
