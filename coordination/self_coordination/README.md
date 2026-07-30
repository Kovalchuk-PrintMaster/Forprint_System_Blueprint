# Blueprint Self-Coordination

This package gives Blueprint its own canonical roadmap, prompt queue, completion workflow, validation and managed-module planning.

## Authority

- `roadmap.yaml` is the canonical Blueprint coordination roadmap.
- The inventory refresh plan is a subordinate detailed workstream plan.
- The self-prompt queue authorizes Blueprint work.
- Exactly one self-prompt may be approved.
- Completed self-prompts require a completion packet.
- Draft prompts do not authorize execution.
- External module repositories are never modified by self-coordination work.
