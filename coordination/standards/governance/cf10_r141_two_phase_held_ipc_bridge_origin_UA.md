# CF-10 R141 — двофазний HELD / post-release backend bridge provenance

**Статус:** source-only, non-authorizing. Canonical base: `cac319a59b0e6f2db5fd4587588d74873d7e0e23` (R140). Жодного production listener, зміни R030, Copilot, claim, PAM, ledger або root release.

## Призначення

Підтвердити, що клієнт root-side IPC не просто перебуває у правильній cgroup, а підключений через конкретний **backend bridge-процес**, відомий незалежному root-контролеру. Відокремити цю перевірку від доказу походження реального MCP child. Один broker — чинний R140; R141 не створює альтернативного launcher чи relay.

### Двофазний порядок

1. **HELD (до release).** `review_held_handoff()` звіряє точні `BoundedInput`/plan, R135/R134 IPC candidate і root R126 disposable lease, root trusted systemd `_verify_held` та pinned `KernelWitness` з *тим самим* `InvocationID`. Backend bridge тут **ще не запущений**, а статус `HELD_R030_R135_PRE_RELEASE_REVIEW_ONLY` не є release-authority.
2. **Після release, до forwarding.** Незалежний root-caller закріплює вже створений backend bridge через `pin_backend_bridge()`: PIDFD, стартовий kernel-tick, `/proc/PID/exe`, exact cmdline, kernel `SO_PEERCRED`, exact cgroup (R135), root-owned immutable-source bytes + SHA. `review_post_release_bridge()` повторно читає той самий systemd `InvocationID` і pinned `cgroup.events=1`. Навіть позитивний результат позначено `POST_RELEASE_BRIDGE_PINNED_PRE_IPC_REVIEW_ONLY`, **не** Worker Result.
3. **Після роботи** R140/R135/R133/R035/R138/R139 залишаються чинними; підсистема не видає terminal fact або дозвіл на retry.

**Важливо:** backend peer у R137 є *bridge-процесом*, який управляє дочірнім `worker_validation_mcp.py`. Навіть PIDFD + SHA bridge не доводять: створення самого MCP child за root-frozen manifest, замкнений process tree, відсутність мережевого egress/credentials чи захист вбудованих інструментів Copilot 1.0.107. `canonical_mcp_child_independently_proven=False`, `g1_g5_closed=False`, `live_worker_authorized=False` завжди.

## Суміжні вимоги та черговий gate

- R030 єдиний systemd launcher, root callback озброює `KernelWitness` до release. Не змінювати його до затвердженого end-to-end cutover.
- R140 розпізнає тільки `/run/forprint-cf10-r125-*/lease.json`: НЕ production lease.
- R115 навмисно відхиляє prospect IPC argv; не обходити його іншим підпроцесом.
- G1–G3 потрібна окрема атестація дочірнього MCP process tree, credentials та egress. G4–G5 — незалежний Result validation і durable terminal/review. Без цього жодного live admission.
- `tmp/` лише доставка ZIP та disposable evidence. Ніяких production залежностей від `tmp/`. Hestia та зовнішні сервіси не зачіпати.

## Make/CLI

- `make cf10-r141-held-ipc-tests`
- `make cf10-r141-held-ipc-source-check`

Тести використовують випадковий одноразовий root-owned fixture під `/run`, тільки локальний Python bridge, без systemd, Git mutation, Worker, Copilot або реальних credentials. Всі fixture процеси terminate/wait, каталог очищається. Пакет source-apply має точну SHA/HEAD перевірку, guarded commit/push лише після тестів.
