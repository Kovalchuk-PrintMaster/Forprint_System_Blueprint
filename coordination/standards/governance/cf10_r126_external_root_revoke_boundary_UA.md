# CF-10 R126 — зовнішнє root-only відкликання одноразової IPC lease

**Статус:** non-authorizing source + disposable UDS proof. Не активує Worker.

R125 на s01 довів один read-only `tools/call(run_repo_head)` та автоматичне
закриття *всередині* broker. R126 додає незалежну root-only команду, яка
може перевести чинну disposable R125 lease у `revoked=true` через окремий
процес. Доведення з окремим UID Unix socket показує, що наступний запит
вже не має проходити gate.

Не створює другу модель Worker, нового launcher, новий authority registry,
нові credentials або production systemd unit. Існуючі R125/R122/R123
джерела не змінюються. Git checkout/Makefile на s01 — в одному пакеті.

**Важлива межа:** атомарне відкликання не перериває *вже допущений*
MCP tool call. Для production потрібні передвиконавчий fence з атомарним
перевірянням epoch, cgroup cancellation, root-controlled service lifetime та
повне зв'язування root receipt/STARTED/terminal ledger. G1–G5 OPEN.

Точний шлях: `/run/forprint-cf10-r125-[0-9a-f]{16}/lease.json`; тільки
root-owned каталоги 0710, root-owned file 0600, O_NOFOLLOW, full identity
match і one-way revoke. Ніяких write/update поза одноразовою lease.
