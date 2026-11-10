# CF-10 R142 — коренева перевірка походження MCP child за PIDFD та stdio pipes

**Статус: source-only / review-only.** Основа Git: `90c908589c346def337c6c9cf65bf06faca1978c` (R141 recovery). R030 і R115 не змінюються; claims/systemd/Copilot/credentials/production/network/ledger не запускаються.

## Межа

R141 вже перевіряє bridge process через kernel `SO_PEERCRED`, cgroup, pidfd, exact argv, root-owned SHA. R142 використовує саме **R141 `BridgePin`**, а не новий launcher. Із kernel procfs визначається один безпосередній child під тим bridge (через `task/<tid>/children`; якщо інтерфейс відсутній — обмежений огляд `/proc/*/stat`), відкривається дитячий pidfd, перевіряються start ticks/parent PID, UID/GID, точна systemd cgroup, `/proc/PID/exe`, `-I -B` frozen argv, root-owned SHA файла `source_capsule/.../worker_validation_mcp.py` та **два незалежні анонімні stdio pipes**, які збігаються з fd bridge-процесу.

`verify_mcp_child()` повторює живий readback безпосередньо перед майбутнім forwarding. `review_post_release_child()` з'єднує цей доказ із уже наявним R141 POST-review, не змінюючи його та не оголошуючи release/terminal success. Закривати PIDFD треба через `MCPChildPin.close()`.

## Що доведено, а що ні

- Позитивний `mcp_process_transport_lineage_proven=True` означає лише **ідентичність та прямий stdio transport конкретного child** на момент перевірки.
- `git_object_source_verified_by_independent_caller=False`: сам переданий root-caller SHA ще треба окремо зв'язати з незалежно перевіреним Git HEAD і canonical source capsule. R142 не доводить цього за власним результатом.
- `root_release_readback_proven=False`, `canonical_mcp_child_independently_proven=False`, `g1_g5_closed=False`, `live_worker_authorized=False`, `worker_result_accepted=False`, `terminal_ledger_written=False` залишаються вимкненими. Немає атестації всього provider process tree, мережі, credentials, CLI tools або G1–G5.
- Виробничий R140 і надалі приймає лише R125 disposable lease. R115 відхиляє перспективний IPC argv. Немає другого release/launcher.

## Тести

`make cf10-r142-mcp-child-tests` і `make cf10-r142-mcp-child-source-check`.

Локальні source-only тести створюють root-owned fixture `/run/forprint-cf10-r125-*`, **реальні** parent+child Python, `pidfd` та Unix socket / stdio-pipes. Єдиний **mock** — точна systemd cgroup (тестовий процес не запускається в canonical unit). Тому це не live systemd acceptance. На сервері R142 package встановлює тільки source, тест, документацію та Makefile із точним Git HEAD checkpoint.

`tmp/` — одноразова доставка, staging/evidence, без production посилань. Hestia й зовнішні systemd-сервіси не змінювати. За HOLD не виконувати reset/clean/retry до звірки.

## Наступна межа

Root-controlled R137-style capsule must be pinned to a Git object before R142 can confirm independently canonical MCP source provenance. Тільки потім — controlled held-to-released R030 integration, no Copilot live until G1–G5.
