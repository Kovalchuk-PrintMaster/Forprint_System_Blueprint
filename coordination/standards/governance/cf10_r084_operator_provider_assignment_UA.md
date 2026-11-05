# CF-10 R084 · операторський план вибору провайдера

**Базова ревізія:** `573b617c7b8eda218e17ec04405a4e0448c1afdc`. **Тип:** read-only, неавторизуючий.

Перший source-native маршрут поєднує реальний `Worker Task` / `Work Front`, поточний стан джерел та каталог R080 у явний операторський **план-кандидат**. Застосовуються лише `Make/CLI`; `tmp/` використовується для доставки ZIP і одноразових тестів, але жоден production-модуль від нього не залежить.

## Інваріанти

- Явні task_id, attempt_id, provider_id, model_id; вибір провайдера за замовчуванням у маршруті plan **заборонений**.
- Read-only перевірка `Worker Task` + зв'язку з Work Front і поточного `source_head` + fingerprint.
- R080 підтверджує READY, capabilities, SHA реєстру/конфігурації і обраного дескриптора. SHA preview не є цифровим підписом і не надає авторизації.
- Спроби, що вже існують у canonical ledger чи runtime, відхиляються до plan. Для поточного пілота worker-01 обов'язковий.
- Не змінює prepare/ACK/dispatch, R082 freeze, R083 gate, PAM, root claim, systemd, R037 finalizer, результат Worker.
- Не допускається automatic fallback чи auto retry; Codex/Claude залишаються NOT_CONFIGURED, доки окремо не перевірені.

## Make/CLI

`make -s cf10-provider-assignment-inspect`

Для read-only плану передавати всі параметри як аргументи Make, **без** інтерполяції в shell-рецепті:

`make -s cf10-provider-assignment-plan CF10_TASK=cf10-validation-check-pipeline-profile-and-optimization-v0-1 CF10_ATTEMPT=cf10-u180j-aNNN CF10_PROVIDER=github_copilot_cli CF10_MODEL=auto`

У реальному середовищі використовувати тільки новий, ще не підготовлений і не спожитий `attempt_id`. Цей план не створює спробу. Не використовувати історичну a054.

## Наступний рубіж

Операторський plan із SHA має перейти в довірений `prepare_cycle` до створення attempt runtime, з окремим рішенням щодо провайдера. Він не повинен дозволяти non-Copilot dispatch до повної інтеграції credentials, sandbox, MCP/result нормалізації та технічної атестації.
