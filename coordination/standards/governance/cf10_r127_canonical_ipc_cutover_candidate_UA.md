# CF-10 R127 — реальний STDIO→UDS транспортний кандидат без live-допуску

## Передумови та підтверджені докази

- `R125` на s01: справжній MCP з durable R122 capsule під R119/kernel, Unix socket, `initialize → tools/list → tools/call(run_repo_head)`, перевірений read-only результат і одноразове revoke — PASS.
- `R126` на s01: окремий root PID відкликає root-owned lease під час відкритої Unix-сесії, наступний запит блокується до forwarding — PASS. Commit `4fb9a6eda8336811156f4d2e8f285cbabbe01659`.
- `R123` зберігає точний crosswalk canonical invocation ↔ R122 source. Цей crosswalk наразі описує *workspace MCP*, не IPC.

## Новий корисний результат R127

1. Один source-only STDIO→Unix-socket proxy для майбутнього Copilot MCP transport: суворі JSON-RPC size/sequence/identity правила; лише `run_repo_head` і не більш ніж один `tools/call` за сесію; фільтрація `tools/list`; перевірка root-side `SO_PEERCRED`; відхилення зайвих методів, чужих інструментів, некоректних аргументів і розширення authority.
2. Read-only canonical cutover candidate: перед побудовою запису виконує існуючі R123 crosswalk/readback і R126 root lease inspection, звіряє attempt, decision, task, workfront, epoch, frozen source SHA і точний socket. Не змінює реальний `invocation_adapter` чи його argv.
3. Реальний disposable process smoke на s01: непривілейований `forprint-runner` виконує proxy і спілкується через Unix socket із синтетичним root-only MCP-відповідачем; root lease читається перед кожним frame, після завершення відкликається. Він **не** повторює дорогу R125 kernel/MCP операцію; фактичну MCP read-only операцію вже доведено окремо.
4. Canonical source tests, SHA-readback, суворий Git checkpoint на 6 файлів, normal fast-forward push, без переписування 71 стороннього dirty шляху.

## Обмеження та ризики, які НЕ закриті

- `cf10_systemd_launcher_v0_1.py`: `LIVE_CUTOVER_ENABLED=False` — зберігається. Жодна нова authority не видається.
- `R115/R118` жорстко вимагають workspace MCP. R127 config-кандидат **не може** потрапити у live invocation до source-reviewed зміни всього preclaim→gate→launch шляху. Не можна замінити один прапорець CLI й назвати це релізом.
- R125/R126 root lease поки disposable із префіксом `/run/forprint-cf10-r125-...`; production attempt/epoch, cgroup/peer PID pin, broker-to-ledger terminal fence, in-flight cancellation, credentials/inference egress separation не атестовані. G1–G5 OPEN.
- R127 process smoke використовує *синтетичні* MCP відповіді; не підтверджує інтегрований Copilot, справжній `tools/call`, kernel sandbox у цьому новому проксі чи terminalization.
- Не відкривається Copilot CLI, worker, claim, credentials, production unit, Hestia, зовнішні сервіси; `tmp/` лише staging/одноразова перевірка; постійні source файли інсталюються в canonical repo.
- Проксі не повинен використовуватися в live Worker до перевіреного root-broker із точним PID/cgroup/epoch, root release та terminal revocation/cancel fence. Поточний `SO_PEERCRED` root-сервера недостатній як самостійна authorization.

## Наступний інженерний результат

Узгоджений source-reviewed canonical preclaim + held systemd gate + root broker launch + direct Worker IPC, із реальним PID/cgroup fence та ledger-bound terminalization. Проводити тільки новою attempt після повного G1–G5 review. До цього жодних launch/claim на s01.
