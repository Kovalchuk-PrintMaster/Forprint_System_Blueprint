# CF10 r052 — джерельно прив'язаний guard на чинному PAM-маршруті

## Призначення

Це **не** новий launcher або authority store. r052 додає дві обов'язкові
перевірки до вже існуючого `cf10_owner_pam_launch_v0_1.launch_once`:

1. **PRE_PASSWORD** — після перевірки канонічного source та frozen inputs,
   але **до PAM**: source-bound r051 root-owned PRECLAIM, незалежний
   r046/r047 raw proof lineage, Task70 / Work Front, writer, ledger,
   root-owned one-shot claim, systemd-quiescence та source-bound pilot wiring.
2. **POST_PASSWORD_PRE_CLAIM** — під наявним `owner_launch.lock` після успішної
   PAM-автентифікації, але **до** `owner_attempt_*.json` O_EXCL: ті самі
   перевірки, нове читання sealed PRECLAIM та r050 LAUNCH_WINDOW.

Модуль не має операцій запуску, видачі proof, PAM-аутентифікації, створення
claim, зміни ledger, systemd чи публікації. `launch_allowed=false` у його
machine requirements — інваріант навіть після успіху unit-тестів.

## Важлива двофазна архітектура

PRECLAIM r045/r051 виконується тільки при незмінному **legacy** карантині:
`cf10-s01-runtime-launch-preflight` з literal `QUARANTINED...; exit 2` та
`LIVE_CUTOVER_ENABLED=False`. Тому пізніше його **не можна** просто
замінити `True` або переписати legacy Make target: це змінить HEAD і
обнулить source freeze sealed PRECLAIM.

Майбутня source-контрольована реалізація окремого pilot cutover має:

* залишити literal legacy Make quarantine і `LIVE_CUTOVER_ENABLED=False`;
* додати **окрему** захищену Make pilot-перевірку (не новий dispatcher);
* додати спеціалізовану source-bound pilot-умову до існуючого systemd backend;
* зафіксувати весь source **до** створення нового Task70 attempt;
* використати root-owned create-once proof/receipt та той самий PAM, claim,
  writer lock і canonical Worker Result finalizer;
* не відновлювати спожитий attempt, не дозволяти automatic retry / ACCEPT /
  publication; не торкатися Hestia та сторонніх services.

У r052 такого Make/backend cutover **немає**. Методи guard відмовляють, якщо
два майбутні source-bound pilot entrypoints не присутні. Жодного worker
не запускаємо, PRECLAIM не видаємо, HEAD не заморожуємо.

## Тести та спосіб завершення

`make cf10-r052-owner-launch-check` — безпечні локальні негативні перевірки.
`make cf10-r052-pilot-launch-requirements` — машинні вимоги, не дозвіл.
Разом із пакетом перевіряються r051/r050/r047/r045/r044/r043/r037 та
`blueprint-tmp-independence-check` до scoped commit/push.

Сторонні незакомічені файли проєкту повинні залишатися без змін.
