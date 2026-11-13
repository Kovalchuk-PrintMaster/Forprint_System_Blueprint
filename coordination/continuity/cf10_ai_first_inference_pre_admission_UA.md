# CF-10 Batch AI — перший model inference: передумови

## Факти, на які спирається пакет

- AH r006: фізичний Copilot 1.0.107 `--version`, коректне cgroup 1→0, без провайдера, мережі й токенів.
- Git checkpoint `2058d1a5846ae406c2e591b698627166268d8fa4`; 18 локальних правок не міняти.
- R115 — єдина канонічна перевірка executable; AA — єдина root-only metadata перевірка credentials.
- R140 — MCP IPC, не inference egress proxy; W/X — виключно локальний TLS fixture. Їх не перевизначати.

## One-shot boundary

`make cf10-first-inference-root-readiness-survey-once` виконує дві *безтокенові* прямі root HTTPS-проби `/_ping` на точних хостах `copilot-proxy.githubusercontent.com` і `api.githubcopilot.com`, не обходить TLS, не слідує redirects, не використовує proxy fallback. Паралельно перевіряє CLI `--help` у безтокеновому offline-режимі та тільки метадані optional root-owned handle `/var/lib/forprint-cf10/credentials/copilot.pat` (не читаючи файл).

Це **не** production root-only egress policy, не API access test, не доказ Copilot CLI authentication і не дозвіл на inference. Ні Worker, ні systemd, ні network policy, ні Hestia/sudoers, ні durable ledger не змінюються. Наявні credential файли не створюються/зчитуються, не копіюються й не включаються до evidence.

## Що автоматично повертаємо

- Root TLS probe: PASS_TLS_200 або зрозумілий HOLD per endpoint.
- R115 pin і підтримка ключових обмежувальних CLI flags на локальному 1.0.107.
- Канонічний AA metadata-only стан external credential handle.
- Один SHA-bound JSON admission-рішення з усіма G1–G5 відкритими.
- Scoped Git commit/push з повною регресією; 18 локальних змін збережено.

## Наступний gated робочий фронт

Незалежно від результату, перший live model request має проходити через реально root-owned керований еgress/auth broker, без credential у Worker/MCP дочірніх інструментах, з першою owner-authorized canonical claim, результатом і незалежним kernel terminal. Це *не* можна вивести з успіху `/ _ping`, допомоги CLI або метаданих handle.
