# Prompt: Telegram Bot Dialogue Audit Events v0.1

## Target module

`telegram_bot`

## Prompt ID

`telegram_bot_dialogue_audit_events_v0_1`

## Purpose

Add consistent local dialogue audit events for key Telegram Bot ORDER intake transitions.

The goal is to improve observability, operator review, restart debugging and future training data review without changing Telegram Bot ownership boundaries.

Telegram Bot remains a Tier 1 client communication channel and intake assistant.

Telegram Bot must not create canonical orders or write to ForPrint business-owner services.

## Current context

Telegram Bot has completed and Blueprint accepted:

- analysis draft handoff preview v0.1;
- SQLite-backed conversation state v0.1.

Telegram Bot has also completed reply keyboard support in module history, and the current smoke test already checks keyboard behavior.

The latest accepted module-side completion commit for SQLite state is:

```text
682217e merge: sqlite conversation state v0.1

The SQLite state checkpoint confirmed:

MemoryState compatibility remains intact;
conversation state is persisted to local SQLite;
SQLite fallback restore works for safe states;
analysis draft handoff preview still works;
no canonical order, Gateway write, 1C write, Calculator call or production launch was added.
Blueprint guidance on restart restore policy

For v0.2 planning, Telegram Bot may treat the following state categories as safe candidates for automatic restore when context is valid and fresh:

ID_SOURCE
ID_ASK_PHONE
HELLO
AN_CLASSIFY_PRODUCT
ANALYZE_INTRO
AN_SUMMARY
AN_DRAFT_HANDOFF

Telegram Bot must use safe clarification or restart behavior for:

unknown states;
unlisted states;
stale states;
states without valid context snapshot;
states with missing correlation/session metadata;
final order form states;
payment states;
stock states;
production states;
external handoff states;
any one-shot/action-triggering state.

State persistence may later become a reusable channel-runtime pattern for Website or future Mobile App, but only as a Blueprint-level pattern or contract.

Do not copy Telegram Bot implementation directly into other modules.

Architecture boundary

Telegram Bot may own and audit only channel-local runtime data:

Telegram profile identifiers;
conversation sessions;
conversation states;
phrase bank interactions;
temporary intake drafts;
local handoff preview / outbox;
local audit events;
ProductClassifier route hints as local channel hints.

Telegram Bot must not own:

canonical clients;
canonical orders;
product registry;
price calculation;
payments;
stock;
production registry;
accounting / 1C;
vendor execution;
contractor execution.
Required implementation

Add or expand local audit event coverage for key live dialogue transitions.

Required local audit events:

identification_started
client_identified
product_classified
analysis_started
analysis_summary_rendered
draft_handoff_created
state_restored_from_sqlite
state_restore_rejected
final_form_requested

These events must be local Telegram runtime audit events only.

They must not be sent to Integration Gateway, Operational Registry, 1C, Calculator or any production service.

Expected event payload fields

Each audit event should include enough channel-local metadata for debugging without creating canonical ownership.

Suggested fields:

event id;
event type;
timestamp;
Telegram chat id;
Telegram user id when available;
session id or correlation id when available;
dialogue state before event when available;
dialogue state after event when available;
ProductClassifier route hint when available;
local intake draft id when available;
local handoff outbox id when available;
safe restore decision when relevant;
short reason when restore is rejected.

Do not persist secrets.

Do not persist canonical business ownership fields.

Do not persist final price truth.

Do not persist payment or stock truth.

Expected technical direction

Suggested branch:

feature/dialogue-audit-events-v01

Likely files to inspect or update:

bot.py
source/education/bot_brain/app/core/state.py
source/education/bot_brain/app/storage/state_repository.py
source/education/bot_brain/app/storage/local_runtime/sqlite_store.py
source/education/bot_brain/app/storage/local_runtime/schema.py
source/education/bot_brain/app/models/order/analysis.py
source/education/bot_brain/app/models/order/handoff.py
source/education/bot_brain/app/models/order/flow.py
source/education/bot_brain/app/models/order/product_classifier.py
source/tools/project_inspection/app_smoke_test.py
source/tools/project_inspection/local_runtime_storage_check.py

The assistant may add a small focused helper module if it improves clarity, for example:

source/education/bot_brain/app/services/dialogue_audit.py

or:

source/education/bot_brain/app/storage/local_runtime/audit_repository.py

Do not add broad framework rewrites.

Required behavior

When key dialogue transitions happen, Telegram Bot should write local audit events to local runtime SQLite.

When SQLite restore succeeds, Telegram Bot should write state_restored_from_sqlite.

When SQLite restore is rejected as unsafe, stale or incomplete, Telegram Bot should write state_restore_rejected.

When unresolved summary creates local operator draft handoff, Telegram Bot should write or preserve draft_handoff_created.

When user asks for final form / final-form-like path, Telegram Bot may audit final_form_requested, but this must not mean canonical order creation or production launch.

Required tests / checks

The module assistant must update or confirm:

python -m py_compile ...
python -m source.tools.project_inspection.app_smoke_test
python -m source.tools.project_inspection.local_runtime_storage_check
python -m source.tools.project_inspection.phrase_bank_check
make telegram-bot-check

The smoke test should cover:

normal live flow still works;
reply keyboards still work;
SQLite state fallback still works;
analysis draft handoff preview still works;
draft_handoff_created audit event is created or preserved;
state_restored_from_sqlite audit event is created on safe restore;
state_restore_rejected audit event is created on unsafe restore.

The local runtime storage check should cover:

audit event insertion;
audit event lookup or count by event type if supported;
conversation state save/load still works;
StateRepository fallback restore still works;
intake draft save/load still works;
handoff preview still works.
Required completion and reporting workflow

At the end of this task, the module assistant must prepare a module-side completion packet inside the Telegram Bot repository.

The module assistant must not write directly into the Blueprint repository.

Required steps:

Run all required checks.
Inspect available completion/reporting automation before manual report edits.
Prefer automation over manual editing where available.
Update module-side status files.
Create or update the completion report.
Update the module-side reports index if present.
Keep all report files inside the Telegram Bot repository.
Commit and push the module-side changes.
Report the final commit hash to Blueprint.

Required module-side files:

coordination/reports/completion/<prompt_id>_completion.md
coordination/reports/index.yaml
coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/status/next_questions_for_blueprint.md

Before doing manual report edits, inspect available automation:

find scripts -maxdepth 3 -type f | sort | grep -E 'completion|coordination|report|status|packet' || true
find source/scripts -maxdepth 4 -type f | sort | grep -E 'completion|coordination|report|status|packet' || true
find coordination -maxdepth 3 -type f | sort
make help 2>/dev/null | grep -E 'completion|coordination|report|status|packet' || true

Telegram Bot may temporarily keep module-side coordination automation scripts under:

source/scripts/coordination/

This is accepted as a transitional path for Telegram Bot because the module has existing source-oriented project layout.

However, canonical Make target names should wrap or call these scripts.

If automation does not exist or is incomplete, manual updates are allowed for this checkpoint, but the completion report must explicitly say:

Completion packet automation was not available or was deferred for this module step.
The required module-side coordination files were updated manually inside the Telegram Bot repository.
No files were written directly into the Blueprint repository.

Required final validation:

git diff --check
make telegram-bot-check
git status --short
git log -5 --oneline

Required completion report content:

prompt id;
branch;
final commit hash;
implementation commit hash if different from final merge commit;
summary of implemented work;
files changed;
checks passed;
known warnings;
explicit boundary confirmation;
confirmation that no Blueprint files were written directly;
open questions for Blueprint, or explicit “No open questions”.

Status/report formatting requirements:

keep current_status.yaml valid YAML;
keep current_status.md valid readable Markdown;
close all Markdown code fences;
do not append stale questions from previous checkpoints into the current question file;
move old answered questions into historical report notes instead of repeating them as current questions;
ensure all text files end with a newline.
Blueprint reporting boundary

Telegram Bot may read Blueprint prompts and standards.

Telegram Bot must not write directly into:

/srv/software_development/forprint-project/forprint_system_blueprint/

Blueprint-side incoming report registration and Blueprint review are separate Blueprint-owned actions.

Explicit non-goals

Do not implement:

canonical order creation;
Supabase canonical orders write;
Operational Registry write;
Integration Gateway write;
1C write;
automatic posting;
Calculator call;
final price calculation;
vendor execution;
contractor execution;
production task creation;
payment status changes;
stock reservation;
broad ORDER flow rewrite;
full replacement of MemoryState;
cross-module reusable package extraction;
direct Website or Mobile App changes.
Definition of done

The prompt is complete when:

required local audit events are written for key dialogue transitions;
SQLite state restore success and reject paths are audited;
analysis draft handoff preview remains green;
reply keyboard smoke coverage remains green;
local runtime storage check remains green;
no canonical order is created;
no forbidden integration is added;
Telegram Bot completion report is created in the Telegram Bot repository;
Telegram Bot current status is updated in the Telegram Bot repository;
current questions for Blueprint are clean and specific to this checkpoint;
final module commit hash is reported back to Blueprint.

---
