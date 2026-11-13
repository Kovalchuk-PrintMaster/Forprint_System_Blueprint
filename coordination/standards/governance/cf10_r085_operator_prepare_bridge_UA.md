# CF-10 R085 · Явний операторський план до canonical prepare

- Джерело: HEAD `3fd5b86e3d34ef5e7fd89fba70c13a7d01719a03`.
- Тип: **керована підготовка нової спроби**, без ACK, dispatch, claim або Worker launch. На відміну від R084 read-only plan, команда `prepare` створює runtime/workspace і тому вимагає explicit root TTY та дослівне підтвердження.
- R084 перевіряє точний Worker Task/Work Front, новий attempt ID, source HEAD, fingerprint, готовність провайдера і SHA каталогу. R085 повторно перевіряє цей preview **всередині** `prepare_cycle` до будь-якого `provision_workspace`.
- R082 Frozen Assignment повинен точно співпасти з провайдером, моделлю, source та R084 catalog candidate. `preview_sha256` додається до prepared artifact для audit trail; сам digest не дає авторизації.
- На цьому етапі дозволено підготувати **лише Copilot / auto** для поточного точного CF-10 пілотного завдання, worker-01. Не використовуйте a054 чи будь-який існуючий attempt. Codex/Claude можна розглядати у R084 read-only plan, але R085 їх не готує.
- Існуючий `governed-worker-cycle-prepare` і внутрішній owner console залишаються сумісними. R083 anti-downgrade, PAM, R037, single-use claim та systemd не послаблюються.

## Команди Make

- `make -s cf10-provider-assignment-prepare-inspect` — тільки перегляд.
- `make -s cf10-provider-assignment-prepare-tests` — тести.
- `make -s cf10-provider-assignment-prepare CF10_TASK=cf10-validation-check-pipeline-profile-and-optimization-v0-1 CF10_ATTEMPT=cf10-u180j-aNNN CF10_PROVIDER=github_copilot_cli CF10_MODEL=auto CF10_CONFIRM_PREPARE=PREPARE_EXPLICIT_COPILOT_NO_LAUNCH` — **реальна підготовка нової спроби**, окремо після рішення оператора. Не виконується автоматично при встановленні R085.

Операторські аргументи передаються Make через експорт environment, **без** інтерполяції в shell-рецепт. Усі production залежності живуть поза `tmp/`.

Якщо після початку `prepare` виникла будь-яка помилка, перевірте runtime/attempt перед повтором. Невдала підготовка **не** дає права повторно використати attempt без огляду.
