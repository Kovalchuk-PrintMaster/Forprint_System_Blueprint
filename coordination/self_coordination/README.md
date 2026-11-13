# Blueprint Self-Coordination

This package preserves the historical Blueprint self-coordination roadmap, prompt
queue, completion records, validation records and managed-module planning evidence.

## Authority

Current Blueprint execution authority is defined by:

`coordination/releases/current.yaml`

That current release explicitly classifies:

- `coordination/self_coordination/roadmap.yaml`
- `coordination/self_coordination/prompt_queue/index.yaml`

as `historical_non_authoritative_projections`.

Therefore:

- `roadmap.yaml` is retained as historical/self-coordination evidence;
- the self-prompt queue does not authorize current Blueprint execution;
- released historical prompts and completion evidence remain immutable;
- current work selection and progression must follow the effective release authority;
- external module repositories are never modified merely because this historical
  package contains a prior roadmap or prompt queue.

If historical self-coordination records conflict with the effective current release,
`coordination/releases/current.yaml` wins.
