# Module Alignment Execution Plan

## Призначення

Цей документ фіксує порядок, у якому ми переносимо alignment prompts у модульні чати, отримуємо alignment reports і оновлюємо Blueprint.

Головна ціль:

перестати рухати модулі стихійно
і перейти до керованої хвилі вирівнювання.
Поточний статус

Ми вже підготували alignment prompts для 8 ключових модулів:

calculator_engine
forprint_crm
forprint_library
telegram_bot
accounting_registry_service
forprint_prepress_hub
forprint_integration_gateway
forprint_operational_registry

Тепер треба не просто мати prompts у файлах, а послідовно передати їх у модульні чати й отримати alignment reports.

Правило

Не робити великий рефакторинг дочірніх модулів, доки не отримано alignment report.

Спочатку:

1. Зрозуміти поточний стан.
2. Знайти architecture drift.
3. Знайти contract gaps.
4. Визначити safe next corrections.
5. Тільки потім змінювати модуль.
Wave 1 — Core direction alignment

Це найважливіша хвиля.

1. Calculator Engine

Чому перший:

він є ядром quote flow;
від нього залежить запуск нормального order flow;
від нього залежить майбутній mobile_app;
він має високий ризик почати володіти каталогами.

Очікуваний результат:

чітко розділити:
Calculator = calculation logic
Library = catalogs
Gateway = routing
Operational Registry = order truth
Accounting = invoice/payment truth
2. ForPrint CRM

Чому другий:

CRM має бути бізнес-диригентом;
є ризик, що CRM стане монолітом;
треба відділити dashboard/workflow від canonical storage.

Очікуваний результат:

CRM = business orchestration + UI
Operational Registry = client/order/task truth
Accounting Registry = invoice/payment truth
Library = catalog truth
3. ForPrint Library

Чому третя:

Library є канонічним джерелом довідників;
від неї залежать Calculator, Prepress, Warehouse, CRM;
є ризик, що Library стане сховищем усього.

Очікуваний результат:

Library = catalogs + templates + contracts + semantic registry
не operational runtime storage.
4. Integration Gateway

Чому четвертий:

Gateway потрібен, щоб модулі не зшивалися напряму;
Gateway має забезпечити channel-agnostic майбутнє для Telegram, Website і Mobile App;
треба не допустити, щоб Gateway став бізнес-мозком.

Очікуваний результат:

мінімальний request/response envelope
validation error model
correlation_id
idempotency_key
перші routing rules
5. Operational Registry

Чому п’ятий:

без нього CRM може стати фізичним власником усіх операційних даних;
треба визначити canonical client/order/task/status.

Очікуваний результат:

мінімальні canonical operational entities v1.
Wave 2 — Active support modules
6. Telegram Bot

Ризик:

Bot може стати god module.

Очікуваний результат:

Bot = channel + workflow client + AI-assisted interface.
7. Accounting Registry Service

Ризик:

Accounting може перетягнути operational registry через 1C.

Очікуваний результат:

Accounting = invoice/payment/1C mapping/reconciliation.
8. ForPrint Prepress Hub

Ризик:

Prepress може почати керувати order workflow або hardcode-ити технічні правила.

Очікуваний результат:

стабільна prepress job model + file states + output report.
Wave 3 — Deferred / later modules

Не запускаємо зараз активно:

warehouse_service
logistics_service
cloud_backup_manager
mobile_app

Вони лишаються в архітектурі, але не мають відволікати від core alignment.

Mobile App rule

mobile_app не розробляється зараз, але враховується як майбутній customer channel.

Усі клієнтські контракти мають бути channel-agnostic:

не telegram_only
не website_only
а customer_channel_*
Найближча дія

Першим переносимо prompt:

coordination/outgoing_prompts/calculator_engine/drafts/2026-05-22-align-calculator-engine-with-blueprint.md

Очікувана відповідь має бути збережена у:

coordination/incoming_requests/calculator_engine/new/
Після отримання відповіді

Blueprint має:

1. Переглянути alignment report.
2. Оновити module_alignment_matrix.yaml, якщо треба.
3. Оновити contracts.yaml/data_objects.yaml, якщо треба.
4. Оновити module guide.
5. Створити новий уточнюючий prompt, якщо треба.
6. Позначити prompt як sent/reviewed у prompt_dispatch_index.yaml.