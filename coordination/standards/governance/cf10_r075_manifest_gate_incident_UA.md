# CF-10 / R075 — a053 post-claim fail-closed, source-native fix

## Факти a053, 2026-11-04

Виведено зі штатних root-owned та systemd readbacks на s01, переданих оператором:

- Owner claim: `CONSUMED_NO_RETRY`; канонічний ledger: `0` записів, `STARTED` немає.
- Backend root receipt: валідний ланцюг, одна подія `LAUNCH_REQUESTED`.
- `stdout.log`, `stderr.log`: root:0600, по 0 байтів.
- Bound launch manifest: 0; точний unit `forprint-cf10-worker-a75f63082487666a6a18f872.service` у systemd наразі `not-found/inactive`, `MainPID=0`; cgroup відсутня або не прив'язана.
- Відсутність поточного unit НЕ є доказом, що процес ніколи не існував. Але наведений порядок backend свідчить про fail до підтвердженого `systemd-run`/`STARTED`. **a053 не запускати вдруге та не скидати claim**.

## Інтеграційна причина, яку виправляє R075

- R013 приймає до 65536 байтів багаторядкового `-p` / `--prompt`, до 8192 байтів MCP та до 98304 байтів сумарного argv.
- Старий backend `_store_file` обмежував будь-який запис 16384 байтами; ізольований gate entry читав максимум 16384 байти і відхиляв `\n` у prompt та аргументи понад 2000 символів.
- Безпосередній збій a053 на `manifest` є **гіпотезою до серверного виміру фактичного serialized byte length**. Кореневі розходження source-контрактів підтверджені; інші помилки запису gate manifest можливі.

## Рішення

1. Вирівняти обмеження R013 → backend manifest → ізольований systemd gate; gate зберігає stdlib-only `-I` і заборону newline поза prompt.
2. Не змінювати історичний signed-release та глобальний `LIVE_CUTOVER_ENABLED=False`.
3. До owner-PAM/claim на справжньому frozen invocation побайтово серіалізувати in-memory manifest, перевірити межі, user/group, root stores, command shape без запису чи launcher.
4. Один project-native Make/CLI doctor, машинний паспорт і regression tests. `tmp/` лише staging/ZIP, а не runtime.
5. **Зміна HEAD після source-патча робить a053 історичною**; для Worker потрібен новий a054 або інший новий attempt, із новим frozen state і незалежним proof/release за чинним контрактом.

## Аварійний сценарій

Не видаляти root receipts/logs, не очищувати або переносити a053, не переписувати ledger, не застосовувати застарілий R074. Розслідування із read-only системних спостерігачів; будь-яке невизначене походження `STARTED`/cgroup блокує повтор.

R075 — source-change candidate, не runtime approval. Після інсталяції необхідні серверні тести, перевірка diff і явний окремий commit/push. Installer НЕ запускає Worker, НЕ робить push та НЕ створює новий attempt.
