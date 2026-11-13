# CF-10 / R129 — канонічна конвергенція lifecycle (source-only)

Дата: 2026-11-09. Вихідна межа: R128 на s01 = `PASS_REAL_STDIO_PROXY_TO_ROOT_UDS_ISOLATED_MCP_TOOLCALL_REVOKED`; R127 commit `8e09ef3d7bb92b3908bd3efe3fb6f1f254718b38`.

## Мета

Один детермінований, **неавторизуючий** автоматичний контракт для стикування існуючих `invocation_adapter`, R115 preclaim, єдиного `cf10_systemd_launcher`, root lease R125/R126, STDIO proxy R127 та `cf10_systemd_terminal_bridge`. Без другого launcher, без зміни live-коду.

Замість серії лабораторій R119–R128 — одна перевірювана послідовність на **синтетичній**, цілком ізольованій від production спробі. Готовність моделі переходів ≠ підтверджена готовність live Worker.

## Порядок

`PREPARED → EXPLICIT_ACK → OWNER_ADMISSION → LAUNCH_REQUESTED → CANONICAL_STARTED → ROOT_RELEASE → READONLY_TOOLCALL → EXTERNAL_ROOT_REVOKE → KERNEL_CGROUP_QUIESCENT → TERMINAL_LEDGER_JOIN → OPERATOR_REVIEW`.

Для кожної події всі `attempt_id`, `task_id`, `work_front_id`, `decision_id`, `source_head`, `epoch`, `systemd unit` збігаються. Тільки одне точне `run_repo_head` через R127 source-only candidate; друга довільна операція не дозволена. Root release лише після канонічного STARTED, як у чинному launcher. Зовнішнє відкликання перед terminal ledger. `KERNEL_CGROUP_QUIESCENT` потребує модельного `1_TO_0` і `populated=0`; порожній або відсутній systemd unit сам по собі не є доказом. `TERMINAL_LEDGER_JOIN` веде лише до `REVIEW_REQUIRED`, а **не acceptance/release**.

**Зверни увагу:** source-only синтетична перевірка приймає позначені `synthetic=true` повідомлення, а не підписані receipt/kernel-FD. Підтвердити реальний PID/cgroup/ledger може тільки канонічний runtime. З цієї причини результати R129 ніколи не змінюють жоден прапорець live authority.

## Поточні відкриті межі

1. R115/R118 продовжують забороняти новий proxy у live argv — не послаблювати їх до узгодженого source+release review.
2. Root-owned signed release, one-time claim і lease epoch ще не зв'язані в **одну перевірену** живу спробу.
3. R126 revoke блокує **нові** виклики, але ще не скасовує in-flight `tools/call`. Потрібне доведене cgroup-stop/fence.
4. G1/G2: tool egress та credential cache / HOME isolation для всього Copilot (не лише MCP) — не доведено.
5. G3: effective Copilot process/native tools sandbox — не доведено.
6. G5: pinned kernel witness → durable ledger terminal/result/review у live Worker — не доведено.

## Обов'язкове збереження меж

- `cf10_systemd_launcher_v0_1.py`: `LIVE_CUTOVER_ENABLED=False`.
- Не змінюємо R115, provider argv, `cf10_systemd_gate_entry_v0_1.py`, root receipt, Copilot binary, R122 capsule, systemd units, Hestia, cloud backup, website preview.
- `tmp/` тільки staging/disposable evidence; installed source/tests/docs — канонічні поза `tmp/`.
- Результат тестів — тільки `SYNTHETIC_ONLY_NON_AUTHORIZING`, `G1_G5_OPEN`.
- Один Make/CLI target `cf10-r129-lifecycle-source-check` для read-only звірки після встановлення; інсталятор — окремий операторський ZIP із commit тільки власних 4 файлів.

## Наступний один workfront

Узгоджена, єдина зміна *канонічних* seams: специфічний proxy MCP `argv` + R115 preclaim + root broker/epoch + вже існуючий systemd launcher + pinned cgroup terminal ledger join. Спочатку source-only і негативні fixture/transaction тести, тоді окремий explicit release decision. Жодного live Copilot E2E, доки G1–G5 не підтверджені для **усього** Worker, а не лише для дочірнього MCP.
