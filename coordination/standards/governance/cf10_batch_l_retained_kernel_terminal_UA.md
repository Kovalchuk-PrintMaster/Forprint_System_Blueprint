# CF-10 Large Batch L — retained systemd cgroup terminal kernel proof

## Рішення

Batch A–C намагалися читати pinned `cgroup.events` **після `systemctl stop`**, коли systemd міг уже вилучити cgroup, і отримували `ENODEV`. Цей пакет перевіряє іншу, близьку до R030 послідовність: **held процес → озброєння pinned FD (`populated=1`) → release → завершення дочірнього процесу → спостереження `1→0` → systemd retained readback → тільки тоді `systemctl stop` → inactive readback**.

Для цієї disposable-перевірки встановлюються `RemainAfterExit=yes`, `ExitType=cgroup` та `KillMode=control-group`. Використовується канонічна реалізація `KernelWitness.wait_zero`, але жоден реальний `forprint-cf10-worker-*` unit не запускається. Root перевіряє `SO_PEERCRED=996:992`, `MainPID`, InvocationID, systemd properties та cgroup inode. Child запускає тільки pinned Copilot CLI `--version` у чистому HOME без секретів. Всі об'єкти разові, розміщені у `/run/forprint-cf10-batchl-*`; жодних залежностей production від `tmp/`.

## Правила

- Запуск з точного Git HEAD та лише після регресій. При PASS тільки 5 source файлів у commit/push.
- Одна disposable unit на запуск. При HOLD ніякого автоматичного retry, root claim або Worker-запуску.
- Після невдачі контролер зупиняє лише власний unit. Якщо `ENODEV` або cgroup зникла до `populated=0`, результат **HOLD**. `inactive` не підміняє kernel proof.
- Лабораторний PASS не закриває G1–G5 для Copilot inference, production root broker, durable ledger чи реального Worker. 
- Hestia, sudoers, інших сервісів, файлів production runtime та реальних credentials не торкаємося.
