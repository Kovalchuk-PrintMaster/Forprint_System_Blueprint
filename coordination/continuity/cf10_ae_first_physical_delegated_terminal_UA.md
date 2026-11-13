# CF-10 AE — фізична дочірня cgroup з root kernel proof

Ціль: виправити виявлений в AD розрив між фізичним Worker IPC/result PASS та pinned kernel FD HOLD після видалення systemd cgroup.

Один transient systemd service містить (1) anchor MainPID у батьківській cgroup, (2) окремий синтетичний Worker як дочірній процес в leaf cgroup. Root перевіряє обидва kernel peer credentials, parent PID, cgroup lineage, створює root-owned delegated leaf, переводить Worker PID у `cgroup.procs` до release, читає `cgroup.events: 1→0` з leaf FD. Anchor не завершується до отримання підтвердження kernel transition. Потім root перевіряє exit=0, retained systemd і stop/readback.

Результат лабораторії не стає production claim або Worker Result. Не змінюємо канонічного Dispatcher / launcher / worker credential handling. G1–G5 залишаються відкритими. Будь-яка відмова в root-only операціях повертає HOLD без повтору.
