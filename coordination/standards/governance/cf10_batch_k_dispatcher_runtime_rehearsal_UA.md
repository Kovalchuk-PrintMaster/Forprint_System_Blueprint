# CF-10 / Large Batch K — Canonical Dispatcher-to-Sandbox rehearsal

## Зміст

Один неавторизуючий лабораторний сценарій: **реальний R030/R134/R115 source-only preclaim review** для синтетичної frozen спроби → SHA прив'язки → одноразовий `forprint-cf10-batchk-*` systemd sandbox з **реальним pinned Copilot 1.0.107 `--version`** і синтетичним HTTPS CONNECT/TLS → повернення SHA через root-controlled Unix control socket → незалежне порівняння та Git checkpoint.

Окремий **fixture** не є реальним Worker/attempt: `forprint-cf10-batchk-*` **не є** канонічним unit `forprint-cf10-worker-*`. Реальний `R030.run_once` та авторизований Dispatcher не запускалися.

## Безпека

- Мережа процесу залишається ізольованою, дозволений тільки localhost та root-owned Unix.
- Немає реальних credentials, model prompt, inference або provider outbound.
- Не використовуються claim, production root listener, ledger writer, systemd-конфіги, Hestia або `/etc/sudoers.d`.
- G1–G5 і pinned kernel `1→0` **не атестовані**; PASS лише для демонстрації frozen digest propagation.
- No retry на HOLD; один evidence ZIP, Git commit/push тільки після повної регресії та реального disposable PASS.

## Функціональний наступний крок

Після цього перестати нарощувати fixture-етапи; спроєктувати production root broker / inference transport та довести provider auth+egress без передачі tokens у Worker; незалежно закрити kernel terminal proof.
