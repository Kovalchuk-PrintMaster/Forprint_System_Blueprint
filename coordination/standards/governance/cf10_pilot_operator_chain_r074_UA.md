# CF-10 операторський ланцюг R074 → включений до R075

R074 був source-кандидатом до першої спроби a053 і вимагав успішного terminal ledger, тому **окремий R074 не встановлюємо**. Після споживання одноразового claim a053 без `STARTED` цей критерій не застосовний. Незмінний R074 як інсталятор залишаємо історичним артефактом, а його корисний код read-only doctor, документацію маршрутизації та виправлення абсолютного root перенесено до R075.

Встановлення R075 дозволяє тільки перевірений постмортем a053: root owner claim consumed, backend `LAUNCH_REQUESTED`, порожній canonical STARTED ledger, порожні root-owned stdout/stderr, unit currently not-found/inactive. Це **не** доказ повної історичної quiescence, але достатня умова для source remediation після безповоротного quarantine a053. Жодного claim reset або retry.

## Постійнa операторськa карта

- `make cf10-pilot-plan` — читання стану.
- `make cf10-pilot-operator-doctor` — read-only маршрутизатор, застосовує штатні R045/R051/R046/R047/R052 та source guard; ніколи не видає launch authority.
- `make cf10-pilot-resume` — лише допустимі nonlaunch-переходи за поточним ledger.
- `make cf10-pilot-launch-once` — тільки окреме операторське PAM після повної перевірки exact нового attempt, без retry.
- `make cf10-pilot-operator-check` — перевірка логіки та gate parity.

`CF10_PILOT_ARGS` використовує абсолютний `--root "$(CURDIR)"`. Розширений source-native R075 також перевіряє реальний serialized manifest до owner-PAM/claim.

## Інваріанти

`tmp/` — виключно доставка; durable runtime поза ним. Hestia, sudoers і legacy signed-release не змінюються. R073 доказовий кандидат **лише a053** і не переноситься на інший HEAD/attempt. Після source commit/push потрібно підготувати новий attempt і окремий доказовий огляд.

Докладний machine-readable паспорт: `coordination/continuity/cf10_pilot_operator_chain_v0_1.json`.
