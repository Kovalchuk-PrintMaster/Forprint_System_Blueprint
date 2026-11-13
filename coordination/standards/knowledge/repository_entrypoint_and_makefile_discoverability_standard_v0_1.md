# ForPrint Repository Entrypoint and Makefile Discoverability Standard v0.1

## Zero-context entry path

Every repository should expose an obvious path for an assistant/executor with no prior chat context.

Preferred pattern:

`README -> START_HERE -> mission/target -> authority -> roadmap -> standards -> capabilities -> knowledge indexes -> execution commands -> relevant dependency/detail documents`

No entry document should contain the entire knowledge base. It is a navigator.

Desired test: a capable zero-context assistant can reach sufficient context for the current Work
Package in roughly 10–20 deliberate navigation steps.

## Makefile role

Makefile is a thin operational capability map/facade. It should:
- expose important high-level operations;
- provide `make help` or equivalent discoverability;
- use broadly consistent semantics across ForPrint repositories;
- delegate to canonical scripts/CLIs;
- avoid substantial business logic.

Candidate common semantic targets:
- `help`
- `check`
- `test`
- `lint`
- `validate`
- `knowledge`
- `report`

The final required set must be reconciled with existing Make/command standards rather than creating
a competing vocabulary.

Modules may add meaningful high-level domain targets.

ForPrint seeks a familiar outer shell, not byte-for-byte identical internal implementation.
