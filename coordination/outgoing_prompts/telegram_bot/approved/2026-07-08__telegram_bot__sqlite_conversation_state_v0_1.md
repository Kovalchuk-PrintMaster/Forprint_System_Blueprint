# Prompt: Telegram Bot SQLite-backed Conversation State v0.1

## Target module

`telegram_bot`

## Prompt ID

`telegram_bot_sqlite_conversation_state_v0_1`

## Purpose

Start moving Telegram Bot live conversation state from in-memory runtime state toward local SQLite-backed runtime state.

The goal is to make Telegram Bot more restart-safe without changing its architecture boundary.

Telegram Bot must remain a Tier 1 client communication channel and intake assistant.

Telegram Bot must not create canonical orders or write to ForPrint business-owner services.

## Current context

Telegram Bot has completed:

- ORDER flow modularization;
- typed ORDER context pack;
- local runtime SQLite storage;
- phrase bank / dialogue text layer;
- ProductClassifier live dialogue connection;
- analysis draft handoff preview v0.1.

The latest accepted module-side completion commit is `64e909b Clean up analysis draft handoff status`.

The previous checkpoint confirmed that unresolved ORDER analysis summaries can create:

- local `intake_draft`;
- local `handoff_outbox` preview;
- local audit event.

This remains local channel-runtime data only.

## Problem

Current live dialogue state still depends too much on in-memory state.

After bot restart or process interruption, active conversations may lose runtime state even though the local SQLite schema already supports `conversation_states`.

This checkpoint should start a controlled transition without rewriting all flows at once.

## Architecture boundary

Telegram Bot may persist channel-local conversation state.

Telegram Bot may own:

- Telegram profile identifiers;
- conversation sessions;
- conversation states;
- phrase bank;
- temporary intake drafts;
- local handoff preview / outbox;
- audit events;
- ProductClassifier route hints as local channel hints.

Telegram Bot must not own:

- canonical clients;
- canonical orders;
- product registry;
- price calculation;
- payments;
- stock;
- production registry;
- accounting / 1C;
- vendor execution;
- contractor execution.

## Required implementation

Add a small state persistence layer that keeps MemoryState compatibility while introducing SQLite-backed state persistence.

Preferred approach:

1. keep existing MemoryState behavior working;
2. add a focused StateRepository abstraction or equivalent small adapter;
3. write conversation state updates to local SQLite when state changes;
4. read from MemoryState first;
5. if MemoryState has no state, try SQLite fallback;
6. preserve existing dialogue behavior;
7. add smoke-test coverage for SQLite fallback behavior.

## Expected technical direction

Suggested branch: `feature/sqlite-conversation-state-v01`

Likely files to inspect or update:

- `bot.py`
- `source/education/bot_brain/app/models/order/flow.py`
- `source/education/bot_brain/app/storage/local_runtime/sqlite_store.py`
- `source/education/bot_brain/app/storage/local_runtime/schema.py`
- `source/tools/project_inspection/app_smoke_test.py`
- `source/tools/project_inspection/local_runtime_storage_check.py`

The assistant may add a small focused module if it improves clarity, for example:

- `source/education/bot_brain/app/storage/state_repository.py`
- `source/education/bot_brain/app/storage/local_runtime/state small focused module if it improves clarity, for example:

- `source/education/bot_brain/app/storage/state_repository.py`
- `source/education/b_repository.py`

Do not add broad framework rewrites.

## Required behavior

When Telegram Bot saves or changes dialogue state:

- state is still available through the existing live flow;
- state is also persisted to local SQLite where practical;
- persisted state includes enough data to restore the next dialogue step safely.

When the in-memory state is missing but SQLite has a matching conversation state:

- Telegram Bot should be able to restore or fallback to the stored state;
- the fallback must be conservative;
- if state cannot be safely restored, the bot should return a safe clarification or restart message rather than guessing.

## Suggested persisted data

Persist channel-local state such as:

- Telegram chat id;
- Telegram user id where available;
- current dialogue state;
- current ORDER context snapshot;
- correlation id / session id where available;
- updated timestamp;
- minimal metadata needed for debugging.

Do not persist secrets.

Do not persist canonical business ownership fields.

## Required tests / checks

The module assistant must update or confirm:

- `python -m py_compile ...`
- `python -m source.tools.project_inspection.app_smoke_test`
- `python -m source.tools.project_inspection.local_runtime_storage_check`
- `python -m source.tools.project_inspection.phrase_bank_check`
- `make telegram-bot-check`

The smoke test should cover:

- normal live flow still works;
- state is written to SQLite;
- MemoryState remains compatible;
- SQLite fallback can restore a known safe state;
- analysis draft handoff preview still works after this change.

The local runtime storage check should cover:

- conversation state save/load;
- schema still initializes cleanly;
- intake draft save/load still works;
- handoff preview still works;
- audit event insertion still works.

## Required report

At completion, Telegram Bot must report only inside its own repository.

Required module-side coordination outputs:

- `coordination/reports/completion/<report>.md`
- `coordination/reports/index.yaml`
- `coordination/status/current_status.yaml`
- `coordination/status/current_status.md`
- `coordination/status/next_questions_for_blueprint.md`

Use completion packet automation if available.

If completion packet automation is deferred in this module, the report must explicitly say so and must not fake successful packet application.

## Blueprint reporting boundary

Telegram Bot may read Blueprint prompts and standards.

Telegram Bot must not write directly into `/srv/software_development/forprint-project/forprint_system_blueprint/`.

Blueprint-side incoming report registration and Blueprint review are separate Blueprint-owned actions.

## Explicit non-goals

Do not implement:

- canonical order creation;
- Supabase canonical orders write;
- Operational Registry write;
- Integration Gateway write;
- 1C write;
- automatic posting;
- Calculator call;
- final price calculation;
- vendor execution;
- contractor execution;
- production task creation;
- payment status changes;
- stock reservation;
- broad flow rewrite;
- full replacement of MemoryState in one step.

## Definition of done

The prompt is complete when:

- MemoryState compatibility remains intact;
- conversation state is persisted to local SQLite where practical;
- SQLite fallback restore path is implemented for at least one safe dialogue state;
- existing ORDER intake flow remains green;
- analysis draft handoff preview remains green;
- local runtime storage check is green;
- no canonical order is created;
- no forbidden integration is added;
- Telegram Bot completion report is created in the Telegram Bot repository;
- Telegram Bot current status is updated in the Telegram Bot repository.

## Questions for module assistant

If implementation reveals uncertainty, report back through `coordination/status/next_questions_for_blueprint.md`:

- Which states are safe to restore automatically after restart?
- Which states should force a safe clarification/restart message?
- Should state persistence later become part of a reusable channel-runtime pattern for Website or future Mobile App?
