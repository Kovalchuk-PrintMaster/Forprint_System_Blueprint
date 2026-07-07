# Prompt: Telegram Bot Analysis Draft Handoff Preview v0.1

## Target module

`telegram_bot`

## Prompt ID

`telegram_bot_analysis_draft_handoff_preview_v0_1`

## Purpose

Implement a production-safe draft handoff preview flow for Telegram Bot when the ORDER analysis summary has unresolved fields.

The goal is to close the current UX gap where the user can choose an option that looks like final order creation while Telegram Bot must remain only a Tier 1 client communication channel and intake assistant.

Telegram Bot must create only a local intake draft and handoff preview/outbox record.

Telegram Bot must not create a canonical order.

## Current context

Telegram Bot has completed the current ORDER intake stabilization work:

- ORDER flow modularization is completed.
- Typed order context pack is completed.
- Local runtime SQLite storage exists.
- Phrase bank / dialogue layer exists.
- Identification flow is connected to DialogueTextService.
- ProductClassifier is connected to live dialogue.
- Summary guard exists when unresolved fields remain.
- Local runtime storage includes `intake_drafts` and `handoff_outbox`.

Current limitation:

- The option similar to “Сформувати чернетку для оператора” still needs a dedicated safe handoff preview flow.
- Telegram Bot must not make this look like a canonical order or production launch.

## Architecture boundary

Telegram Bot is a channel assistant.

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
- vendor or contractor execution.

## Required implementation

Create a safe draft handoff preview path from the analysis summary guard.

When unresolved fields exist and the user chooses the operator draft option, Telegram Bot should:

1. avoid full final order creation;
2. create or update an `intake_draft` record in local runtime SQLite storage;
3. create a `handoff_outbox` preview record;
4. include current ORDER context snapshot in the draft payload;
5. include ProductClassifier route hints in the draft payload when available;
6. include source channel metadata:
   - Telegram chat id;
   - Telegram user id where available;
   - conversation/session id where available;
   - current dialogue state;
7. return a human-friendly message to the user:
   - “Чернетку заявки для оператора сформовано.”
   - “Оператор зможе перевірити деталі перед запуском у роботу.”
8. make clear that this is not a confirmed production order.

## Recommended naming

Avoid risky customer-facing wording such as `Фінішний бланк`.

Prefer safer wording such as:

- `Попередня заявка`
- `Чернетка заявки для оператора`
- `Попередня чернетка для перевірки оператором`

The exact phrasing may be adjusted by the module assistant through the existing PhraseBank / DialogueTextService layer.

Expected technical direction

Suggested branch:

feature/analysis-draft-handoff-preview-v01

Likely files to inspect or update:

source/education/bot_brain/app/models/order/analysis.py
source/education/bot_brain/app/models/order/order_form.py
source/education/bot_brain/app/storage/local_runtime/sqlite_store.py
source/tools/project_inspection/app_smoke_test.py
source/tools/project_inspection/local_runtime_storage_check.py
source/education/bot_brain/app/services/phrase_bank.py
source/education/bot_brain/app/services/dialogue_texts.py

The assistant may add a small focused module if needed, for example:

source/education/bot_brain/app/models/order/handoff.py

Only add new files when they keep the code clearer.

Required behavior

When analysis has unresolved fields:

summary guard remains visible;
operator draft option does not enter full final form flow;
local intake_draft is created or updated;
local handoff_outbox preview is created;
user receives a safe confirmation message;
the flow remains local and channel-runtime only.

When analysis is complete:

existing safe final form behavior may remain unchanged;
do not expand final form into canonical order creation.
Required tests / checks

The module assistant must update or confirm:

python -m py_compile ...
source/tools/project_inspection/app_smoke_test.py
source/tools/project_inspection/local_runtime_storage_check.py
source/tools/project_inspection/phrase_bank_check.py
make telegram-bot-check

If the module has Make targets for broader validation, use them.

The smoke test should cover:

unresolved analysis summary guard;
user chooses operator draft option;
full final order flow is not triggered;
intake draft payload is created;
handoff outbox preview is created;
user sees safe confirmation text.

The local runtime storage check should cover:

intake draft save/load still works;
handoff preview creation still works;
audit event insertion still works.
Required report

At completion, Telegram Bot must report only inside its own repository.

Required module-side coordination outputs:

coordination/reports/completion/<report>.md
coordination/reports/index.yaml
coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/status/next_questions_for_blueprint.md

Use completion packet automation if available.

If completion packet automation is deferred in this module, the report must explicitly say so and must not fake successful packet application.

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
stock reservation.
Definition of done

The prompt is complete when:

unresolved summary guard can create a safe local draft handoff preview;
local intake_draft contains a useful ORDER context snapshot;
local handoff_outbox contains a preview payload for operator review;
ProductClassifier route hint is included in draft payload when available;
customer-facing text no longer suggests confirmed production order;
no canonical order is created;
no forbidden integration is added;
smoke/local runtime checks are green;
Telegram Bot completion report is created in the Telegram Bot repository;
Telegram Bot current status is updated in the Telegram Bot repository.
Questions for module assistant

If implementation reveals uncertainty, report back through next_questions_for_blueprint.md:

Should the handoff payload later become an Integration Gateway envelope?
Should ProductClassifier route hints become required fields in every intake draft?
Should Telegram Bot keep MemoryState as primary state for one more step, or move SQLite state earlier?
