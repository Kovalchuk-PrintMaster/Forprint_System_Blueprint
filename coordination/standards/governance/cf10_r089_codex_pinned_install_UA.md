# CF-10 R089 — контрольоване встановлення зафіксованого Codex CLI

База: `32dc679162f8b4de04c1ff60880c46a530abde49` (R088).

## Два відокремлені рішення

1. Встановлення R089 **source ZIP**: тільки перевірки та selective Git commit/push. Воно **не встановлює Codex**, не робить мережевих запитів, не викликає `curl`, systemd, Codex або Worker.
2. Окрема операторська дія `make -s cf10-codex-pinned-install CF10_CONFIRM_CODEX_INSTALL=INSTALL_PINNED_CODEX_0_166_0_NO_WORKER`: потребує root, TTY, published source guard, відсутності обох можливих Codex CLI, достатнього диска та exact canonical project. Лише цей opt-in завантажує зафіксований GitHub Release через HTTPS.

Реліз OpenAI Codex CLI `rust-v0.166.0`, опублікований 2026-10-29. Pinned GitHub Release metadata (`assets[].digest`), не *latest*:

- x86_64: `codex-x86_64-unknown-linux-musl.tar.gz` — `a0bf572d2f93f056c6712a6da348e96078dc84f3885fd7be67807ef389cb3978`.
- aarch64: `codex-aarch64-unknown-linux-musl.tar.gz` — `94eb707605ec2646b2e05b7edf7c4e7b3ccf02b16237c34ae9beb8cfb7f810a9`.

Завантаження використовує лише фіксовану URL, без `curl|sh` чи npm postinstall. Перед публікацією бінарника перевіряються архітектура, SHA-256, точний розмір TAR, рівно один regular member, ELF header і обсяг розпакування. Системна публікація `/usr/local/bin/codex` — атомарний `link`, який не перезаписує наявний target або symlink; інший `/usr/bin/codex` також має бути відсутнім. Якщо install після мережі не вдався, **не повторювати автоматично**: перевірити причину та поточний inventory.

Root-only durable receipt живе в `/var/lib/forprint-provider-provenance/codex_r089_v0_166_0_install.json` (каталог `0700`, файл `0600`) і містить SHA зафіксованого архіву, SHA встановленого бінарника та source HEAD. Тимчасові файли download/extraction — в одноразових приватних каталогах, не runtime-залежностях.

## Після опціонального встановлення

- Read-only: `make -s cf10-codex-offline-inspect`.
- Окрема дія для **offline** `--version` у вже наявному sandbox R088:
  `make -s cf10-codex-offline-version-probe CF10_CONFIRM_CODEX_VERSION_PROBE=PROBE_CODEX_VERSION_OFFLINE_DISPOSABLE_NO_WORKER`.

Ця версія Codex не проходить авторизацію, не переводиться в Registry READY, не отримує model invocation, ACK, claim або systemd Worker. Далі окремо потрібні attestations CLI HOME/auth, version option parity, sandbox, result transport/Handoff/R037.

Не торкатися Hestia, sudoers, зовнішніх сервісів, a054, R037, root-owned claim, чужих Git-змін. Make/CLI — єдиний операторський surface. `tmp/` — лише доставка ZIP, staging, disposable QA. Реальна поточна артефактна установка ніколи не залежить від `tmp/`.
