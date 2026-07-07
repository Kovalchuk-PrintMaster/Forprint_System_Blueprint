# Prompt: Align Telegram Bot with ForPrint governance protocol

## Target module

`telegram_bot`

## Purpose

Bring Telegram Bot into compliance with the ForPrint module governance protocol without changing runtime bot behavior prematurely.

Telegram Bot must remain a client-channel adapter. It must not become the owner of clients, orders, accounting, warehouse stock, pricing truth, production runtime, or canonical catalogs.

## Current status from Blueprint governance audit

Telegram Bot is currently not aligned with the governance protocol.

Missing governance files:

- `forprint_module_manifest.yaml`
- `coordination/status/current_status.yaml`
- `coordination/prompts/index.yaml`
- `coordination/reports/index.yaml`
- `coordination/status/next_questions_for_blueprint.md`

Missing Makefile targets:

- `check`
- `check-report`
- `status-report`
- `blueprint-pull`
- `blueprint-check`
- `blueprint-sync-directives`
- `coordination-check`
- `coordination-fix`
- `module-policy-check`
- `governance-check`

## Important observed problem

During an attempted governance alignment, the module Makefile appeared to contain duplicate/overridden targets and then failed with:

```text
Makefile:1036: *** missing separator. Stop.

Observed duplicate/overridden target warnings included:

classify-dialogs
deberta-train
style-train
deberta-eval
lint
format
security-check
clean

Before adding governance targets, the Telegram Bot assistant must first inspect and normalize the existing Makefile structure.

Required first step

Do not blindly append governance targets to the bottom of the Makefile.

First:

inspect the existing Makefile;
identify duplicate targets;
decide which old targets are canonical;
preserve existing working runtime commands;
only then add governance-compatible targets.
Required test strategy

Telegram Bot currently does not have the expected ForPrint governance test layout.

Add or restore module-local tests in the correct Telegram Bot test directory.

Required minimum tests:

Makefile parse/smoke test if appropriate;
manifest boundary validation;
coordination files existence validation;
no direct ownership of clients/orders/accounting/warehouse/pricing;
Integration Gateway boundary requirement;
basic bot scenario smoke tests using safe fixtures only;
no live Telegram sending during tests;
no real token usage during tests.
Required governance alignment

Add these governance files:

forprint_module_manifest.yaml
coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/prompts/index.yaml
coordination/reports/index.yaml
coordination/status/next_questions_for_blueprint.md

Add or normalize these Makefile targets:

check
check-report
status-report
blueprint-pull
blueprint-check
blueprint-sync-directives
coordination-check
coordination-fix
module-policy-check
governance-check
Boundary rules

Telegram Bot must not:

write directly to 1C;
perform accounting posting;
mutate warehouse stock;
own operational orders;
own client account truth;
own pricing truth;
bypass Integration Gateway for business workflows;
use live Telegram token in tests.

Telegram Bot may:

receive Telegram-side input;
guide channel-specific intake;
prepare normalized channel events;
call Integration Gateway contracts once those contracts are approved;
render safe human-facing responses.
Validation required before commit

Before committing, run:

make coordination-check
make governance-check
make check
make check-report
git status --short

All checks must pass.

If some implementation remains intentionally deferred, the target may print DEFERRED, but it must not hide broken runtime behavior.

Commit expectation

After successful alignment:

git add Makefile forprint_module_manifest.yaml coordination
git commit -m "Add Telegram Bot governance and test alignment"
git push
Blueprint note

This task is intentionally deferred until Telegram Bot work resumes. Do not force alignment from Blueprint while the module Makefile/test layout is unstable.
