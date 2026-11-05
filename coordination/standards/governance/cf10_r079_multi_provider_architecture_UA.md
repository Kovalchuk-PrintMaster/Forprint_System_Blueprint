# CF-10 / R079 — аудит provider-neutral Worker Architecture

Основа: **Git HEAD `7aceecec4e0653affd4511b064a74c6ece527382`**. Це документ про source-архітектуру, а не підтвердження production readiness.

## Висновок

Стратегічна концепція правильна: `coordination/standards/automation/worker_runtime_adapter_registry_contract_v0_1.yaml` уже вимагає незалежної від провайдера ідентичності Worker, вибору runtime на спробу, спільних Work Front/Handoff/Dispatcher/ledger/result. Проте пілотна реалізація зараз допускає тільки Copilot CLI. **Не перейменовувати Copilot-код в універсальний, не змінюючи фактичного контракту.**

## Реальні зв'язки

1. `worker_runtime/registry.py`: `ready_count != 1` — кілька одночасно READY провайдерів заборонені.
2. `cf10_training_dispatch.py`: точна прив'язка до `github_copilot_cli`, моделі `auto`.
3. `governed_worker_cycle.py`: передає цю прив'язку як константу при dispatch.
4. `worker_runtime/invocation_adapter.py`: `SUPPORTED_PROVIDER`, Copilot argv/MCP IDs, permissions і кредити Copilot.
5. `cf10_supervisor_binding_candidate_v0_1.py`, R077, R078: конкретний Unix runner, HOME і startup-профіль.
6. `worker_runtime/worker_result_return.py`: два власні формати framing; не є нормалізатором Codex JSONL / Claude stream-json.
7. `provider_session_proof.py`: provider-specific інтеграційний сценарій Copilot.

Це **пілотні вузькі шви**, а не необхідна частина універсальної координації.

## П'ять незалежних вимірів

- `Worker identity`: worker-01, worker-02... — роль і scope, не бренд AI.
- `Task`: Work Front, Task Envelope, Handoff, capabilities, budget, exact attempt/source.
- `Provider + model`: Copilot/Codex/Claude/інший, конкретна модель, versioned adapter.
- `Execution backend`: локальний CLI під systemd або окремий remote/cloud job executor.
- `Trust`: Owner/PAM, one-shot claim, writer protocol, immutable ledger, independent result verification.

**Схема**: Task → capability/policy routing → frozen provider/model/adapter binding → owner gates → executor → untrusted provider output → normalized completion candidate → independent validator/finalizer → owner acceptance. Кожен провайдер бачить лише дозволені capability tools, не має права приймати власний результат.

## Підключення провайдерів

Copilot — зберегти існуючий адаптер, згодом загорнути в спільний інтерфейс. Codex CLI — `codex exec`, власний auth/sandbox/MCP/JSONL adapter. Claude Code — `claude -p` із власним permission policy і JSON/stream-json adapter. Кожна з цих команд тільки ілюстративна: конкретні flags повинні проходити source-bound version tests. Remote/cloud job — інший executor із durable job ID, retry reconciliation, idempotency і власними attestations; не вважати systemd-ланчером.

## Ризики та обов'язкові gates

- Число READY у registry можна розширювати тільки одночасно з source-controlled per-attempt selector і exact frozen binding. Інакше можливий silently switched provider.
- Не довіряти capabilities як виконуваній authority. `workspace_write: launch_policy_bound` не дозволяє запис сам по собі.
- Провайдерські креденшали ізолювати по сервісному профілю/Unix user або захищеному environment/credential boundary. Не переносити загальний HOME Copilot на інших без огляду.
- Зберегти `ARGV_NO_SHELL`, worktree isolation, незалежні докази, deny-by-default, no auto-retry після claim.
- Відокремити **LLM provider** від **executor type**: Codex CLI та Codex Cloud — не один і той самий запуск.
- Протоколи stdout/stdin і JSONL різняться. Адаптер повинен перетворювати їх на *untrusted* canonical completion candidate, який перевіряється незалежно.
- Роутинг із групою Worker потребує concurrency quotas, writer lease/conflict review, cost policy і явних task capability requirements.

## Порядок міграції

1. R079 (цей пакет): безпечний чистий типізований контракт вибору провайдера, тести із двома READY **лише у fixture**, статичний аудит фактичного coupling. **Не запускає Worker і не змінює live registry.**
2. Adapter seam + selector freeze. Жодної зміни старих пілотів; нові спроби мусять верифікувати provider/model/adapter на PREPARE, ACK, DISPATCH, PRECLAIM.
3. Copilot parity tests із тим самим входом і результатом. Лише після PASS — перенесення реального маршруту на спільний інтерфейс.
4. Codex як другий adapter з auth smoke (без робочого claim), власними CLI flags та result normalization; потім Claude Code.
5. Роутинг кількох Worker і remote jobs — окремі контрольовані кроки, а не прапорці READY.

## Стан a054

`cf10-u180j-a054`: CONSUMED_NO_RETRY, canonical ledger STARTED/PENDING, systemd exit=1, R035 PRE присутній, terminal відсутній, Worker Result відсутній. Не ресетити, не перевидавати, не приписувати успіх. R079 не змінює стан.

## Експериментальний доказ

R078: `PASS_OFFLINE_DISPOSABLE_COPILOT_VERSION_ONLY_NON_AUTHORIZING`. Це bootstrap CLI, а не auth/network/model/workflow тест.
