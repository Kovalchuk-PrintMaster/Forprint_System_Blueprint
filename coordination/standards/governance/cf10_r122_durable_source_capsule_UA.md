# CF-10 R122 — постійний Source Capsule (неавторизуючий)

## Рішення

R121 r008 на s01 підтвердив: immutable Git HEAD 12c668e… (427 Python/registry файлів), повний імпорт `ForPrintValidation` від імені `forprint-runner` та реальний MCP `initialize → tools/list` під R119 kernel-профілем — PASS. Водночас робочий `SUITE` відрізняється від HEAD і **не повинен входити у випущену збірку**.

R122 створює **постійну**, перевірювану, root-owned копію цих exact Git blobs у `/var/lib/forprint-cf10/runtime-capsules/git-<head>-sha256-<manifest-digest>/source/`. Ні `tmp/`, ні disposable `/run` не стають залежністю runtime. Root-касу публікацій відділено від `forprint-runner` (читання лише групі `forprint-runner` (каталоги 0750, файли 0640), запис заборонений).

Випуск атомарний: staging → SHA-256 + Git blob SHA-1 → canonical MANIFEST.json → `rename` → повний readback. Повторний виклик дозволений лише при точній повторній перевірці усіх байтів; mismatch зупиняє операцію без overwrite. Незбережений worktree не копіюється. Створення капсули не змінює systemd і не видає release/claim/worker permissions.

## Межі

- Git source pin: `12c668e0cc309bd1162154ae12f7281603cf7bfa`, branch `audit/blueprint-inventory-refresh-2026-07-29`.
- Canonical entry: `source/scripts/coordination/control_plane/worker_runtime/worker_validation_mcp.py`.
- Зберігання: лише `/var/lib/forprint-cf10/runtime-capsules`, root-owned, ніколи в `tmp/`.
- Жодна інформація про credentials не копіюється; копіюються лише `.py` і `coordination/registry/*.yaml|*.yml|*.json`.
- `R118 preclaim`, `invocation_adapter`, canonical `systemd launcher/gate-entry`, systemd units, Hestia, зовнішні таймери — без змін.
- Runtime capsule **не підключено** до live Worker. G1–G5 відкриті. Наступний етап має перевірити source identity binding на pinned capsule path у канонічному invocation/authorization контурі, IPC та epoch revocation. До завершення заборонено live admission.
- Запуск `make cf10-r122-capsule-publish` не означає дозволу на Worker; зміна source HEAD потребує окремого reviewed release рішення.
