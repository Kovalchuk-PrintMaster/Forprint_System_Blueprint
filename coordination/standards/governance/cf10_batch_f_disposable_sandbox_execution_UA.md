# CF-10 Large Batch F — executable disposable whole-process sandbox

## Дозволений результат

Один root-owned disposable unit `forprint-cf10-batchf-<16hex>.service`
від системного `forprint-runner` перевіряє **ефективні** обмеження:
`PrivateNetwork=yes`, `RestrictAddressFamilies=AF_UNIX`, `IPAddressDeny=any`,
`InaccessiblePaths=<тільки фіктивний файл>`. Справжній `AF_UNIX` міст
підтверджується root-side `SO_PEERCRED`, `/proc/<pid>/cgroup` і незалежним
readback systemd. IPv4/IPv6 тільки створення socket; жодної зовнішньої
мережі й жодних справжніх credentials. Фіктивний файл лежить у `/run` і
до sandbox доступний DAC-читанню. Worker повертає лише код доступу, не вміст.

Source entrypoint `cf10-batch-f-sandbox-source-check` не виконує systemd.
Одноразова root-лабораторія з пакета **не є production launcher** і не
викликає R030.run_once, PAM чи root claim. Немає залежностей production від
`tmp/` або `/run/forprint-cf10-batchf-*`.

## Навмисні межі

У цій конфігурації inference неможливий: навіть GitHub Copilot не зможе
звернутися до мережі. Отже, успіх disposable перевірки не закриває G1–G5,
не є атестацією реальних provider credentials/cache, повного дерева Copilot,
виконання завдання, root IPC production чи pinned kernel 1→0.
`systemctl stop` + systemd readback не замінюють kernel witness.

Якщо preflight, systemd run, SO_PEERCRED або будь-яка негативна проба
провалюється, статус **HOLD**. Заборонено повторно запускати стару unit,
підвищувати права, розширювати мережу або вважати G1–G5 закритими.
Виконання на s01 можливе лише через єдиний guarded пакет, тести, evidence,
і лише після PASS — exact-file commit і normal fast-forward push.
