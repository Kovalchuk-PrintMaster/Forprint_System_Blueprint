# Bootstrap reporting rule

Fresh global assistants must always pair machine IDs with human meaning.

For each significant status:
1. human-readable stage/task name;
2. short purpose/context;
3. current state;
4. next meaningful action;
5. machine IDs/sequences for correlation.

Example:
Good: `Dispatcher — integrate Work Fronts, Execution Profiles and Handoff v2 (CF-09, work u180i). State: ACTIVE.`
Bad: `u180i ACTIVE seq62`.
