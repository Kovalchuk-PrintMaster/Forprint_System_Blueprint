# CF-10 R088 · Ізольована діагностика Codex CLI

**Початкова ревізія:** `d943de27b7ebfea88a8a916e0babd961105f78cd`. **Статус:** неавторизуючий інвентар і opt-in offline-version probe.

R087 надав source-only Codex Adapter. R088 **не** переводить його у READY і **не** встановлює Codex CLI. Базовий `inspect` перевіряє метадані у двох фіксованих системних шляхах. Неперевірені symlink, ненадійний власник, режим чи неоднозначний executable призводять до REVIEW. Відсутність CLI також є коректним результатом inventory — не помилка інсталяції Blueprint.

## Канонічні Make/CLI

- `make -s cf10-codex-offline-inspect` — тільки файлові метадані, **без** Codex subprocess.
- `make -s cf10-codex-offline-tests` — чисті unit/regression фікстури, без системного запуску.
- **Окремий opt-in операторський probe**: `make -s cf10-codex-offline-version-probe CF10_CONFIRM_CODEX_VERSION_PROBE=PROBE_CODEX_VERSION_OFFLINE_DISPOSABLE_NO_WORKER`. Не виконується інсталятором і потребує root + interactive TTY, source guard, приватного runner HOME та одного перевіреного root-owned executable.

Probe викликає лише `/usr/bin/systemd-run ... -- <allowlisted-codex> --version` у тимчасовому юніті `forprint-cf10-codexprobe-*`, з `IPAddressDeny=any`, `ProtectSystem=strict`, `ProtectHome=yes`, `NoNewPrivileges=yes`, `User=forprint-runner`, `StateDirectoryMode=0700`, `RuntimeDirectoryMode=0700`, окремим `CODEX_HOME`, порожнім stdin і обмеженням часу. Використовує наявний R077/R078 sandbox-контракт. Тільки SHA/розмір stdout повертається оператору; текст CLI не потрапляє у звіти.

R088 не модифікує `/etc/sudoers.d/hestiaweb`, Hestia, зовнішні systemd-сервіси, Registry, default provider, `tmp`-залежності, durable ledger, ACK/PAM, claim, release чи finalizer R037. Немає запуску Worker, автентифікації або network access. Немає автоматичного retry.

**Важливо:** версія CLI і root-ownership **не доводять** наявність auth, коректність sandbox виконання task, сумісність JSONL або readiness. Потребує окремої атестації CLI lineage, Codex HOME, auth boundary, task invocation, result normalization та R037.
