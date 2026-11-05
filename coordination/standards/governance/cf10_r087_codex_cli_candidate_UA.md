# CF-10 R087 — Codex CLI Source Adapter Candidate

**Базовий HEAD:** `08ab912fe3e73c65841d773cea9c0fc7bdba7fdc`.

Це **source-only, non-authorizing** лабораторний контракт другого CLI-провайдера `openai_codex_cli`. Чинний запис Codex у `coordination/registry/worker_runtime_adapters_v0_1.yaml` лишається `NOT_CONFIGURED`, а `cf10_r081_provider_adapter_v0_1.py` і dispatch залишаються **Copilot-only**.

## Що можна тестувати

- Детермінований ARGV_NO_SHELL для `codex exec --json` з explicit model та exact attempt workspace; жодних `subprocess`/PAM/systemd/claim/ledger.
- Майбутній prompt передаватиметься stdin; зараз жоден pipe не відкривається, сам prompt не з'являється в плані, фіксується лише SHA256.
- Майбутній read-only sandbox **не дозволяє редагувати** файли: це перевірка ABI, не готовність повноцінного Worker. Не додавати `--dangerously-bypass-approvals-and-sandbox` або `--add-dir`.
- JSONL можна оцінити лише як **недовірені технічні події**; навіть `turn.completed` не є Handoff v2 Result і не може обійти WorkerResultReturn чи R037.
- `normalize_result_candidate()` завжди відмовляє до окремого reviewed milestone.

## Межі

Не змінювати `tmp/` на постійне сховище чи runtime dependency. Не конфігурувати Codex credentials/`CODEX_HOME`, не встановлювати бінарник, не робити network/auth probe, не робити Codex `READY` та не додавати Codex до `_SOURCE_BOUND_ADAPTERS` на цьому кроці. Зберегти всі зовнішні та незакомічені зміни поза scope.

## Make/CLI

- `make -s cf10-codex-adapter-candidate-check` — тільки status.
- `make -s cf10-codex-adapter-candidate-tests` — чисті тести, без CLI.

## Наступна межа

Потрібна окрема Codex **disposable sandbox/version check** з реальним бінарником і контрольованим HOME, потім source-bound provider descriptor + operator capability approval. Фактичний Worker launch і результат з R037 залишаються окремими межами.

Підстава щодо опцій CLI: [Codex exec CLI](https://github.com/openai/codex/blob/main/codex-rs/exec/src/cli.rs), [Codex SDK exec](https://github.com/openai/codex/blob/main/sdk/typescript/src/exec.ts). CLI опції необхідно перевірити проти конкретної встановленої версії перед підключенням.
