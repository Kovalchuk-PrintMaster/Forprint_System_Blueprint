# CF-10 AG — канонічний Dispatcher preview → одноразовий nonce → AE Worker

База: `f0f3990579984985738c8e29a92246bdc2a41b95`. Передумова: AE вже довів фізичний Worker IPC + delegated kernel leaf 1→0 на s01; AF успішно виконаний на s01, evidence AF підтверджує фізичний E2E, Git HEAD f0f3990579984985738c8e29a92246bdc2a41b95. AG r001 зупинився на HOLD_GIT_BASELINE до інсталяції.

## Критична зміна

Під час аналізу AF виявлено причинний розрив: `join()` перевіряв task_id й окремі позитивні звіти, але не міг довести, що фізичний Worker отримав маркер **конкретного** preview Dispatcher. AG створює новий одноразовий synthetic nonce на основі hash-bound decision preview та salt, передає його в незмінений протокол AE→anchor→AD child і незалежно звіряє child result hash з тим самим nonce. `AE.run_once()` підтримує legacy-режим без параметрів; при переданому nonce перевіряє форму до systemd/`/run` і додає hash-only binding readback.

Root перевіряє exact ACK, canonically computed decision_id, Task/Context/Attempt fingerprint, різницю PID Worker vs anchor, unit, InvocationID, незалежний kernel leaf 1→0, `retained_systemd`, stop/readback. Неможливо підмінити одним історичним AE-result рішення Dispatcher з іншим preview identity: результат child digest та nonce binding не збіжаться.

## Межі

Це lab-only pilot. Canonical Dispatcher `authorize_training_explicit_dispatch()` викликається для **попереднього перегляду рішення** із `ledger_store_override` у disposable /run scratch, а не як фактичний production dispatch. ACK — точний auto-echo лише для локального тесту. AE запускає окремий disposable systemd unit; production `cf10_systemd_launcher_v0_1.LIVE_CUTOVER_ENABLED` залишається False. Жодного live Copilot, credentials, inference, external egress, canonical claim або durable terminal ledger. G1–G5 OPEN; synthetic join не дає права змінювати ці стани.

**Наступне критичне завдання після server AG PASS:** незалежний provider authorization без витоку credentials, реальний provider egress, source-bound worker claim і canonical production terminal acceptance. Не створювати альтернативні Dispatcher/launcher/MCP broker. Не перетворювати lab nonce на auth token.

AG r002: перебазовано на фактичний AF checkpoint, додано AF source/test SHA pins і його регресію. Пакет як і раніше не є production authority.
