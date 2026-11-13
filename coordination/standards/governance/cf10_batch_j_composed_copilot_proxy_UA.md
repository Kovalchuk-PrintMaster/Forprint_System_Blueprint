# CF10 / Large Batch J — One-unit Copilot + HTTPS transport composition

## Ціль

Один disposable systemd unit (`forprint-runner`, private network namespace)
виконує **справжній** pinned Copilot 1.0.107 (`--version`, без auth) і
передає **синтетичний** TLS/HTTPS запит через loopback CONNECT → root AF_UNIX
fixture. Незалежний контролер перевіряє SO_PEERCRED, cgroup, systemd effective
allow/deny, заборону зовнішніх мереж і захист фіктивного файла.

## Межі доказу

- Copilot --version і HTTPS fixture працюють в одному unit / namespace.
- **Не доведено**, що Copilot CLI реально використовує проксі для inference.
- Не доведено live provider authentication, production egress, MCP tools,
  root broker під R030, terminal kernel 1→0, G1–G5 та Worker E2E.
- Пакет не запускає prompt, не читає credentials, не змінює production runtime,
  не створює Worker claim, не змінює системні service unit, не допускає replay.
- Тільки Git HEAD exact; при HOLD commit/push заборонено. Один evidence ZIP.

## Подальший milestone

Спільний R030 root-held release + root-bound inference broker, після незалежного
доведення production G1–G5. Жоден локальний fixture не є підставою для live.
