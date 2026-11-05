# CF10 R078 — повторно використовуваний disposable Copilot CLI bootstrap smoke

- Джерело: R077, HEAD `354f3a9ca4fee49821373a3d261dd95973d2c8ed`.
- Історична a054 незворотна: claim CONSUMED_NO_RETRY, ledger STARTED/PENDING,
  R035 PRE є, TERMINAL відсутній; systemd failed exit-code 1 після release marker.
- R077 відновив доступ до HOME/.cache у disposable systemd, але НЕ довів запуск CLI.
- R078 створює лише ізольований, одноразовий transient unit для запуску **`copilot --version`**.
  Виконуваний файл читається з двох канонічних source-controlled registry/config,
  а не зі старого prompt/manifest a054.
- Застосовано `StateDirectory=forprint-runner`, mode `0700`, `ProtectSystem=strict`,
  `ProtectHome=yes`; інтернет заблокований `IPAddressDeny=any`.
- Немає Worker prompt, MCP, provider AI request, ledger/claim, Git-write чи авторизації.
- Після source commit/push виконай `make cf10-pilot-provider-cli-inspect`, потім
  `make cf10-pilot-provider-cli-smoke` рівно один раз. Якщо smoke FAIL — не
  запускати новий Worker і не повторювати smoke без розбору причини.
- **PASS означає лише запуск бінарника й `--version`.** Не перевірено авторизацію,
  credentials, сеть, credits, модель, MCP чи повний цикл Worker.
- Ніколи не друкувати секрети, історичні prompt або всі змінні середовища.
- Історичну a054 не перепризначати, не перезапускати, не підробляти SUCCESS terminal.
