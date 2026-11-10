# CF10 R131 — non-authorizing canonical terminal review fence

Це інтеграційна **межа читання**, а не другий Worker launcher. Результати R123–R130 не дають live-authority. R129 перевіряє лише синтетичні події, R130 — завершення тестового дерева в делегованій cgroup.

## Що зв'язує R131

- R127 review candidate + R129 синтетичний порядок переходів (не підмінюють runtime-доказ).
- Ідентичність attempt, epoch, source_head, cwd, capsule ID через поточні перевірки R129.
- Реальне `revoked=true` через існуючий **R126** root-owned lease readback.
- Реальний typed `KernelWitness` + **існуючий** `cf10_systemd_terminal_bridge.witnessed_terminal()` з pinned `cgroup.events: 1→0` і retained systemd invocation ID.
- Вивід лише `REVIEW_ONLY`; жодного `result_accepted`, ledger append, запуску, claim, retry чи release.

**Заборона:** синтетичний unit R129 НЕ є канонічним unit. Єдине джерело observed systemd unit — `KernelWitness`. На жодному етапі не допускається підміна `KernelWitness` довільним JSON або відсутність kernel-доказу.

## Відкриті критичні межі

1. R126 lease наразі є **disposable лабораторним** з path `/run/forprint-cf10-r125-*/lease.json`, а не production authority для всіх Worker.
2. Поточний R115/R118 відхиляє proxy-команду як неканонічну. Live-argv і preclaim не міняються цим пакетом.
3. Реальний root-manifest / operator decision / launch gate / ledger join не доведені одним immutable lineage.
4. Успішний kernel terminal при штатному exit не означає зупинку in-flight MCP і при timeout. Для canceled/failed service цей консервативний fence повертає HOLD.
5. G1/G2 credential/egress Copilot і G3 повне kernel-enforcement для in-process tools не підтверджено.
6. G5 root release → `STARTED` → `Result` → kernel witness → ledger terminal/recovery усе ще потребує доказу на одній canonical Worker-спробі.

### Дозволено

`make cf10-r131-terminal-source-check` та `make cf10-r131-terminal-tests`. Команди є non-authorizing. Для виклику `witnessed_review_candidate` потрібні незалежно підготовлені root lease і **справжній** канонічний kernel witness. Пакет автоматично не створює такі докази.

Не змінювати `/etc/sudoers.d/hestiaweb`, Hestia, сторонні systemd-сервіси, постійний runtime, R122 capsule або `/run` цим source-only ZIP.
