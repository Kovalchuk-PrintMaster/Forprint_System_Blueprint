# CF-10 Large Batch H — Disposable Loopback HTTPS CONNECT / Unix Broker

**Статус:** лабораторний транспорт, не live-допуск. Залежить від PASS Batch G r002; Git HEAD на вході `52acfa7ad1c91c1239cafda928e625726a0f7dd8`.

## Функціональна межа

Один тимчасовий unit у systemd з `PrivateNetwork=yes`, `IPAddressDeny=any`, `IPAddressAllow=localhost`, `RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6`. Під `forprint-runner` (996:992) відбувається локальне TCP-з'єднання, HTTP CONNECT для **вигаданого** `fixture.forprint.invalid:443`, opaque Unix-socket forwarding у root-side лабораторний broker та справжня TLS-відповідь з перевіркою тестового сертифіката й SAN. Другий CONNECT — на `unauthorized.invalid:443` — відхиляється. Прямий IPv4-вихід до TEST-NET адреси повинен бути недоступним. Фіктивний root-controlled credential-файл має повертати EACCES/EPERM, не ENOENT.

Root-side TLS fixture **не** відкриває мережу, не перенаправляє трафік до провайдера й не виконує довільних URL. Відповідь — лише `CF10_BATCH_H_PUBLIC_TLS_CONNECT_FIXTURE_V1`. Лабораторний тестовий ключ сертифіката в ZIP є публічним прикладом, не використовується в production, не є секретом і не надає Worker жодних прав. Systemd-сервіс одноразовий: новий unit створюється тільки коли назва не зайнята; при HOLD зберігаються докази, немає auto-retry.

## Як інтерпретувати результат

PASS означає: на s01 працює реальний локальний HTTP CONNECT → Unix socket → TLS, root-side `SO_PEERCRED`/cgroup, loopback-only allowlist, відхилення стороннього CONNECT, захист фіктивного файла, readback зупинки systemd. Це **не** доказ реального Copilot API, HTTP proxy-compatibility Copilot CLI, доступу inference-провайдера, захисту реального provider token, root IPC production, canonical R030 Worker handoff чи kernel witness `1→0`. G1–G5 залишаються відкритими й Worker claim заборонений.

## Захисні правила

- Жодних production/systemd-unit-файлів, жодного додавання sudoers або Hestia-правил.
- Старий `forprint-cf10-batchg-d91637008dda0f74.service` читається лише для підтвердження термінального стану; не очищується.
- Дозволений хост — лише штучне fixture-доменне ім'я. Ніяких external GET, DNS, HTTP requests чи реальних credentials. Public SAN-сертифікат перевіряється клієнтом; кореневий тестовий ключ використовується лише host-side і не копіюється в sandbox.
- `tmp/` — виключно доставлення й disposable evidence. Канонічний код/тести — у визначених директоріях Git.
- Source-only Make target — не launcher; запуск systemd дозволений лише guard-інсталятору один раз після регресій.
- Відсутність pinned kernel `1→0` ніколи не конвертується в PASS terminal; laboratory systemd readback — окремий менш сильний доказ.

## Exit / acceptance

При будь-якій невідповідності — HOLD з `error_code` і етапом; жодного commit/push до загального PASS. Після PASS Git commit/push рівно 5 target-файлів. Один ZIP зі стислим sanitized evidence формується при PASS або HOLD, якщо доступний файл/диск.

**Наступний неохоплений фронт:** контрольований реальний inference transport із provider-specific HTTPS destinations/auth і перевіркою поведінки pinned Copilot CLI; не створювати альтернативний launcher/owner claim.
