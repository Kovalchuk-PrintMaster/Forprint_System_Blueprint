# CF-10 / R081: source-bound Copilot adapter seam

## Мета

Перший **виконуваний** крок від монолітного Copilot-рендера до мультипровайдерного Control Plane. У чинному `invocation_adapter.build_launch_invocation` залишаються нормалізація задачі, перевірка dispatch, frozen context, MCP configuration і source gates. Лише побудова vendor-specific `argv` та структура `provider_policy` проходять через `cf10_r081_provider_adapter_v0_1.route_invocation`.

## Властивості

- Тільки `github_copilot_cli` дозволений як реалізований source-bound backend. Інші назви провайдерів **fail closed** без `fallback`.
- `READY` у Registry, `Model`, `Candidate` або запуск тесту не дають дозволу виконувати Worker.
- Незмінний контракт `argv`, SHA-256, MCP permissions, `provider_policy` — parity тести зі старим джерелом для readback ON/OFF, timeout None/960000 та двох моделей.
- Формати `Worker Result`, frozen claim, operator PAM, systemd, ledger, root receipts, finalizer і task dispatch не змінено.
- ProviderAdapter не валідує авторизацію Copilot і не приймає ніяких результатів самостійно. Авторизація провайдера ще потребує окремого безпечного позитивного доказу.
- R079/R080 catalog candidates ще **не підключені** до живого dispatch: наступний зріз — точна frozen selection + parity pipeline.
- `a054` залишається історичною спробою `CONSUMED_NO_RETRY`, `STARTED/PENDING`, без canonical terminal. Запуск/повтор/очищення заборонено.

## Межі перевірки

Локальні тести перевіряють формат і арифметичну еквівалентність SHA команд. Серверні оригінальні тести `invocation_adapter`, registry, dispatch, owner corridor, finalizer проходять перед commit. Вони не замінюють виробничого виконання Copilot і не свідчать про його auth readiness.

## Наступні кроки

1. R082: явний вибір `provider_id/runtime_id/model_id` і його source/hash freeze **до ACK/dispatch**; не знімати Copilot-only коридор без іншої перевірки.
2. R083: незалежні bootstrap/auth/stream тестування Codex, потім source-reviewed Codex adapter без нового Control Plane.
3. Для REMOTE_JOB — окремий durable remote job id, idempotency, receipts і replay-safe lifecycle; systemd свідчення локального процесу не застосовувати як доказ remote termination.
