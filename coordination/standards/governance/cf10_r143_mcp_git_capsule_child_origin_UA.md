# CF-10 R143 — Git commit → MCP source capsule → PIDFD child (review-only)

## Призначення

R137 r003 довів disposable запуск справжнього канонічного MCP з 14 Git-об’єктів; R141 підтвердив PIDFD-bridge, R142 — прямий MCP child та stdio-pipes. R143 додає відсутній **незалежний source-origin join** без другого launcher.

Root-side caller постачає `frozen_source_commit` із вже перевіреної канонічної спроби (це **не** authority від Worker/MCP). R143 перевіряє:

- точний повний commit SHA та `HEAD` у Blueprint; без dirty-worktree як джерела коду;
- Git tree modes: тільки `100644/100755`, не symlink; Git blob SHA-1 у канонічному Git object форматі, далі побайтовий SHA-256;
- усі 14 файлів source capsule з Git-об’єктів; порожні `__init__.py` допустимі;
- власність root, незмінність inode під час читання, відсутність symlink, групового/стороннього write та додаткових файлів (`.pyc` включно);
- `R142.MCPChildPin` у тій самій lab source capsule та Git SHA його `worker_validation_mcp.py`;
- повторну R142 kernel PIDFD/parent/UID/cgroup/stdio перевірку до й після Git readback.

`review_post_release_git_child` поєднує R141 post-review, R142 child-review і R143 source-origin. Результат **тільки review-only**: без `launch`, `claim`, IPC forwarding, `release`, terminal ledger append, Worker acceptance, G1–G5 closure або auto-retry.

## Межі гарантії

R143 засвідчує source capsule й транспорт MCP, **але не** гарантує незмінність усіх завантажених site-packages або Python runtime, повний список process descendants, відсутність мережевого доступу чи секретів у Copilot CLI. Доказ worker release/terminalization належить окремому канонічному R030/R035/R139.

R143 ще **не встановлює live hook у R030** — перед production інтеграцією потрібні closed G1–G5 та окремо перевірений frozen invocation/lease. Не запускати Worker із цього source-only модуля.

## Операційні правила

`tmp/` — виключно disposable delivery; capsule під `/run/forprint-cf10-r125-<nonce>` — disposable і ніколи не durable authority. Не змінювати Hestia / зовнішні сервіси. На інсталяції — один Make/CLI test gate і 4-file Git checkpoint, без змін стороннього dirty-worktree.
