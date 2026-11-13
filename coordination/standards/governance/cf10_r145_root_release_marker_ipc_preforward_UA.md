# CF-10 / R145 — канонічний root-release readback перед IPC

**Статус:** джерельний, неавторизуючий контроль; Git checkpoint після перевірок. Після R144 (`151b17afa5ca5c391a035a085a8690da25b7238b`).

## Навіщо

R030 має один коректний порядок: root-owned manifest → HELD systemd → pinned KernelWitness → R035 pre-boundary + ledger STARTED → root-owned release marker → Worker exec. R141/R143/R144 уже перевіряють live IPC/stdio/backend source, але R144 не мав **незалежного прочитання фактичного R030 release marker** перед forwarding.

R145 не дублює launcher. Він додає до чинного публічного `R140.serve_one()` обов'язковий read-only бар'єр `R145.review_pre_forward()` **після** R141/R143 live proof і **до** першого IPC. Старий `_serve_lab_one()` лишається приватним disposable-транспортом. За будь-якої помилки public API намагається одноразово відкликати R126 lease, видає `KERNEL_QUARANTINE_REQUIRED` та **не** підтверджує kernel zero.

## Контракт доказів

- Лише зафіксований `launcher.GATES`; root-owned каталог `0711`, regular manifest/release `0644`, `O_NOFOLLOW`, `nlink=1`, стабільні inode, максимум 512 entries. Жодного довіреного input від Worker.
- Один manifest exact-match: `attempt_id`, `source_head`, systemd unit, frozen `argv/sha`, workspace, runner UID/GID та nonce. Повторний/неоднозначний manifest — HOLD.
- `release-<nonce>.json`: точна схема `cf10_root_release_v0_1`, exact SHA-256 сирих canonical manifest bytes, root inode. Відсутній, змінений, підмінений або неправильно оформлений маркер — HOLD.
- R141 held_review + in-memory R030 `KernelWitness`, незалежні `systemctl` InvocationID/ControlGroup/UID/Group/KillMode і pinned `cgroup.events populated=1` — exact same invocation. Це доказ **наявності root release marker для цього held systemd unit**, але **не доказ** того, що Copilot exec успішно відбувся.
- На виході — лише SHA/identity/read-only факти. Ніякі `worker_result_accepted`, `terminal_ledger_written`, `live_worker_authorized`, `automatic_retry` не можуть стати `True`.

## Непорушні межі

- Немає другого launcher, `Popen`, production root IPC listener, нового Worker claim, привілеїв, credential access, змін R030/R115/gate-entry або live dispatch.
- R125 lease у R140 лишається **disposable lab only**. Production зв'язування listener та MCP child і їх запуск у той самий held/released systemd unit не реалізовані R145.
- Наявний marker не атестує виконання gate-entry, всього дерева Copilot, sandbox, egress або credentials. G1–G5 **OPEN_NO_LIVE_ADMISSION**, R115 old live shape не приймає R127 candidate.
- `/tmp`/repo `tmp/` — тільки disposable fixture та доставка пакета, жодна канонічна runtime-залежність.
- Ніякого ledger append/terminal або release-authority з цього readback.

## Acceptance

Офлайн негативні перевірки manifest/release inodes, malformed JSON, links, SHA drift, duplicated matches, kernel/systemd invocation drift, root/held identity. Суміжні R030/R133/R135/R138–R144 регресії на s01; source-check двох модулів; exact file set commit/push normal fast-forward лише після PASS. Файли worktree за межами target set не змінювати.
