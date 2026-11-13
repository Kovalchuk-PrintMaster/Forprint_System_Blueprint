# AGENTS.md Fresh-Context Handoff Specification

Blueprint AGENTS.md must let a fresh assistant understand:
- mission and current phase;
- hard gates;
- canonical read order;
- portfolio identity facts;
- inventory program;
- archive workflow;
- analysis standards;
- per-module progress;
- stop conditions;
- exact next action.

It should point to canonical sources instead of duplicating all policy text.

## Fresh-context acceptance test
With only AGENTS.md plus the canonical files it points to, a new assistant must answer:
- What are we doing?
- What are we forbidden to do?
- Which module and batch are current?
- Where are completed reports?
- Which architecture rules are agreed?
- How is the roadmap updated?
- When may real implementation begin?

If not, the handoff is insufficient.
