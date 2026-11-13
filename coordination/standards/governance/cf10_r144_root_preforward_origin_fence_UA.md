# CF-10 R144 — root IPC pre-forward origin fence (source-only)

**Мета.** Закрити розрив між R140 disposable root broker і read-only lineage R141/R142/R143: публічний `R140.serve_one()` не може викликати R135 без незалежної повторної перевірки походження MCP. Немає нового launcher чи ledger writer.

## Порядок у майбутньому канонічному циклі

1. **HELD, до release.** R030 із root-owned frozen BoundedInput/plan, R035 PRE/KERNEL witness і одноразовим root lease. R141 `review_held_handoff` доводить frozen systemd invocation. R144 цього не створює.
2. **Після release, до першого IPC-кадру.** `R140.serve_one()` перевіряє дійсну R125 disposable lease та `spec/plan/witness`; викликає R141 `review_post_release_bridge()` для повторного kernel systemd/bridge PIDFD; викликає R143 `review_post_release_git_child()` для R142 child PIDFD+stdio і 14 точних Git-об'єктів capsule. Frozen `source_head` має збігатися з commit, attempt і unit.
3. **Лише після PASS** викликає той самий приватний `_serve_lab_one`, тобто існуючий R140 → R135 один read-only `run_repo_head` з незалежним R126 revoke. Немає другого MCP proxy/launcher.
4. **Будь-який HOLD:** спроба irreversible R126 root lease revoke, `KERNEL_QUARANTINE_REQUIRED`. Успішне revoke **не доводить** припинення in-flight процесів: тільки R133+KernelWitness і durable R035 можуть далі доводити завершення. Не дозволено auto-retry.

## Безпекова межа

`_serve_lab_one` збережений лише як приватний disposable testing backend. Його аргументи, як і публічного wrapper, допускають тільки R125 lease `/run/forprint-cf10-r125-*/lease.json` із root ownership. Production R030 release, R115 preclaim, Worker Result acceptance, terminal append, Copilot auth/egress не змінюються. G1–G5 **відкриті**: `root_release_readback_proven`, `kernel_terminal_proven`, `copilot_process_tree_proven`, `copilot_egress_attested`, `credential_isolation_attested`, `worker_result_accepted`, `live_worker_authorized` залишаються `False`.

Важливо: R144 перевіряє origin на вході сеансу. Він **не** доводить ефективну sandbox-ізоляцію і не є production listener. Наступна інтеграція має використовувати цей guarded API в канонічному R030 post-release коридорі лише після незалежних доказів G1–G3 і захищеного production lease, без обходу R115. Будь-яка зміна authority потребує окремого governance-рішення.
