# Visible Transcript

> Exact recoverable MHTML text. Attachment bodies may be absent. Historical provenance only.

## conversation-turn-1 — user
Turn ID: `bbb213c8-75cf-4814-aad3-551e6f204697`

Дивись ми зараз накидуємо логіку роботи нашого проекту друкарні і таке питання що треба розібратися з тим як можна скоригувати і синхронізувати роботу нашого проекту з 1С скажімо так вся поточна бухгалтерія і всі фінансові проводки проводяться зараз в 1С там же поки що і ведеться облік всіх наявних матеріалів я би хотів щоб ми зробили таким чином я б хотів би максимально відв'язатися від 1С в внутрішні технічній роботі нехай там бухгалтерія там возиться з нею далі поки що але щоб наша робота була таким чином що у нас є власна база даних матеріалів ну тобто ми витягуємо всю специфікацію всіх матеріалів всі залишки з 1С формуємо собі там ну 1С певно що формує там якісь документи або щось там подібне ну то не проблема ми його розпарсимо легко і ми собі формуємо надалі свою власну базу даних базуючись на тому що вже є а після цього ми уже перетягуємо одіяло керування на себе тобто всі списання всі залишки даних які йдуть по робочим процесам ми переадресовуємо на себе на свій модуль і просто вже потім точково в 1С ми передаємо актуальну інформацію тобто наприклад за поточний день то ну там ми вибираємо там наприклад три або чотири точки передачі даних да там кожні 4 години там наприклад там ну умовно там о 8:00 ранку 12 там четверта і 20 там година там або кожну годину ну то не є принциповим це ми можемо налаштовувати але принциповим є те що ми беремо на себе автономне керування залишками автономне керування приходом і розходом матеріалу як такового причому в будь-яких матеріалів які використовуються на виробництві плодоофісних і просто вже по факту ми підгружаємо в 1С наші власні дані тобто за сьогодні там якщо було списано там там 800 м² банеру то ми і в 1С підгружаємо що сьогодні було списано 800 м², а не так як вона собі списала там 300 наприклад або 1300 тому що 1С ну поки що я не бачу зручних інструментів і коригуванням і налаштуванням мені здається що легший шлях будувати якусь свою власну систему а в 1С тільки передавати чіткі параметри що відбулось за день а вже бухгалтерію там хай вони крутять як хочуть поки що ми до цього питання не звертаємось якщо треба буде то можливо ми просто напишемо свій власний модуль на майбутнє ну поки що до цього не доходить що ти думаєш з цього приводу і скажи мені
Show more
Show less

## conversation-turn-2 — assistant
Turn ID: `df3d5614-0b9f-4737-bc1c-ef6dd60814d4`

Я бачу тут не просто “синхронізацію”, а принципове рішення: хто є головною системою для виробничих залишків. Розкладу це як архітектурну схему: що правильно забрати у свій модуль, що лишити в 1С, і де найнебезпечніші місця.

Так, я вважаю цей напрям
правильним
, але з одним важливим уточненням:
нам не треба “ламати” 1С і воювати з нею. Треба зробити так, щоб
виробнича система стала головною для реального руху матеріалів
, а 1С залишилась
бухгалтерською/обліковою системою
, куди ми передаємо вже підготовлені, перевірені документи.
Тобто модель така:
Наш проєкт = фактичний виробничий облік, залишки, списання, резерви, норми, калькуляції, виробничі події.
1С = бухгалтерія, фінансові проводки, офіційні документи, податковий/складський облік, поки що без втручання у виробничу логіку.
1С технічно дозволяє інтеграцію з зовнішніми системами: через REST/OData можна читати й змінювати дані, створювати об’єкти й документи, а також працювати з регістрами, довідниками та документами; також у платформі є web/HTTP-сервіси, XML/JSON, файловий обмін, зовнішні з’єднання та інші механізми інтеграції.
1c-dn.com
+1
Як я бачу правильну архітектуру
Я б не робила прямий хаотичний обмін “з 1С туди-сюди”. Я б зробила окремий модуль:
inventory_core
/
materials_ledger
Його задача — вести
власну книгу руху матеріалів
.
Не просто таблицю “залишок банеру 800 м²”, а саме журнал подій:
material_movement
- id
- material_id
- movement_type: receipt / write_off / reserve / release_reserve / correction / inventory_adjustment
- quantity
- unit
- warehouse_id
- production_order_id
- source_module
- operator_id
- created_at
- synced_to_1c
- sync_batch_id
Тоді залишок — це не ручне число, а результат рухів:
початковий залишок
+ прихід
- списання
- резерв
+ повернення
± коригування
= актуальний залишок
Це набагато надійніше, ніж просто тримати одну колонку
current_stock
.
Головна ідея: 1С не джерело істини для виробництва
Перший етап — 1С ще джерело стартових даних:
1С → експорт матеріалів, одиниць, залишків, складів, можливо партій
Ми імпортуємо це у свою базу:
our_materials
our_warehouses
our_stock_snapshot
our_material_movements
А далі поступово змінюємо роль:
до запуску:
1С = головна по залишках

після запуску нашого модуля:
наша система = головна по фактичному виробничому руху
1С = отримує результат
І це дуже правильний підхід для друкарні, бо 1С часто добре підходить для бухгалтерії, але незручна для живого виробничого процесу: банер, плівка, папір, фарба, люверси, ламінат, порізка, брак, переробка, часткове списання, залишки рулонів, нестандартні формати — це все краще вести у власній логіці.
Але не треба передавати в 1С просто “800 м² списано”
Ось тут важливий момент. Я б не передавала в 1С тільки голу цифру:
Списано банеру: 800 м²
Краще передавати документ або пакет документів із розшифровкою:
Дата: 2026-05-17
Матеріал: Банер 440 г
Склад: Основний
Кількість: 800 м²
Підстава: виробничі замовлення №...
Тип операції: виробниче списання
Джерело: ForPrint Inventory Core
ID пакета синхронізації: sync_2026_05_17_2000
Бо якщо бухгалтерія потім спитає: “Звідки взялося 800 м²?”, у нас має бути відповідь не словами, а структурованими даними.
Я б зробила не пряму синхронізацію, а через чергу
Правильна схема:
Наш виробничий модуль
        ↓
таблиця outbox / sync_queue
        ↓
1C adapter
        ↓
1С
        ↓
sync_log / результат
Тобто коли у нас відбулося списання, ми не одразу ліземо в 1С. Ми створюємо подію:
event: material_write_off_created
status: pending_sync
Потім окремий адаптер бере ці події й передає в 1С.
Це дає дуже важливі плюси:
1С впала — виробництво не зупинилось
помилка синхронізації — подія не загубилась
можна повторити передачу
можна бачити, що саме не передалося
можна робити передачу раз на годину, 4 рази на день або в кінці дня
Частота передачі даних
Твоя ідея з точками синхронізації правильна. Я б заклав це як налаштування:
YAML
sync_to_1c:
  mode: scheduled
  schedule:
    -
"08:00"
-
"12:00"
-
"16:00"
-
"20:00"
allow_manual_sync: true
  allow_end_of_day_close: true
Але архітектурно краще, щоб система підтримувала обидва режими:
1. scheduled sync — пакетна передача кілька разів на день
2. manual sync — кнопка “передати зараз”
3. end-of-day sync — закриття виробничого дня
4. emergency resync — повторна передача проблемного пакета
Що саме треба синхронізувати з 1С
Я б поділила обмін на два напрямки.
1. Імпорт з 1С до нашої системи
На старті або періодично:
довідник матеріалів
одиниці виміру
склади
групи матеріалів
залишки на дату
можливо постачальники
можливо партії/серії, якщо вони ведуться
Це режим:
1С → наша система
2. Експорт з нашої системи в 1С
Після того як наш модуль почав керувати виробництвом:
списання матеріалів
прихід матеріалів, якщо ми його фіксуємо у себе
переміщення між складами
резервування/зняття резерву — можливо не в 1С, а тільки у нас
інвентаризаційні коригування
повернення матеріалу
брак
Це режим:
наша система → 1С
Який принцип я б зафіксувала
Ось це прямо варто записати як архітектурне правило:
1С не має самостійно розраховувати виробниче списання матеріалів.
1С отримує готові документи/пакети рухів від нашої виробничої системи.
Тобто не так:
1С сама вирішила, що списалось 300 м²
А так:
наша система по факту виробництва визначила: списано 800 м²
1С отримала документ на 800 м²
Найбільші ризики
Найнебезпечніше місце —
подвійне керування залишками
.
Тобто якщо частина людей списує в 1С, а частина — у нашій системі, буде хаос.
Тому треба зробити чітке правило:
Після запуску нашого inventory-модуля всі виробничі списання робляться тільки в нашій системі.
В 1С руками виробничі списання не створюються, крім аварійних випадків.
І для аварійних випадків треба мати окремий механізм:
manual_1c_adjustment_detected
reconciliation_required
Тобто якщо бухгалтер щось руками поправила в 1С, наша система має або отримати це назад, або показати конфлікт.
Обов’язково потрібна звірка
Навіть якщо наша система стане головною, треба мати модуль звірки:
Наш залишок по матеріалу
vs
Залишок у 1С
Наприклад щодня о 21:00:
material_id | our_stock | 1c_stock | difference | status
Банер 440   | 1250 м²   | 1250 м²  | 0          | OK
Плівка      | 320 м²    | 300 м²   | -20        | CONFLICT
Це не означає, що 1С права. Це означає, що треба бачити розбіжність.
Як я б розбила реалізацію по етапах
Етап 1. Read-only інтеграція з 1С
Ми нічого не змінюємо в 1С. Тільки витягуємо:
матеріали
склади
залишки
одиниці виміру
Формуємо свою базу.
Етап 2. Власний облік руху матеріалів у тестовому режимі
Наша система рахує списання, але ще не впливає на 1С.
1С живе як раніше
наша система веде паралельний облік
ми порівнюємо результати
Це дуже важливий перехідний етап.
Етап 3. Shadow comparison
Порівнюємо:
що списала 1С
що порахувала наша система
де різниця
чому різниця
На цьому етапі ми відловимо помилки норм, одиниць, коефіцієнтів, браку, обрізків.
Етап 4. Наша система стає головною для виробництва
Після перевірки:
виробничі списання створюються в нашій системі
1С отримує пакет документів
Етап 5. Розширення
Далі можна додавати:
закупівлі
планування потреб
мінімальні залишки
автозаявки на закупівлю
прогноз витрат
аналітику собівартості
контроль браку
облік рулонів/листів/залишків форматів
Моя рекомендація по суті
Я б робила саме так, як ти кажеш:
не намагатися перетворити 1С на гнучку виробничу систему
, а побудувати власний модуль, який відповідає реальному процесу друкарні.
Але я б не формулювала це як “відв’язатися від 1С повністю”. Правильніше:
Відв’язати виробничу логіку від 1С, але залишити контрольований бухгалтерський міст.
Тобто:
1С — не керує виробництвом
1С — отримує фінально підготовлені облікові факти
Як це лягає в наш загальний проєкт
Я б заклала окремий модуль у базову архітектуру:
apps/
  materials/
    каталог матеріалів
    одиниці виміру
    склади
    партії
    залишки

  inventory/
    рухи матеріалів
    резерви
    списання
    коригування
    інвентаризація

  production/
    виробничі замовлення
    фактичні витрати
    норми
    брак

  integrations/
    one_c/
      import_materials
      import_stock
      export_writeoffs
      export_receipts
      reconciliation
      sync_logs
І я б одразу в коді заклала принцип:
1C adapter — це зовнішній адаптер.
Він не має права диктувати внутрішню логіку нашій системі.
Тобто вся внутрішня система має працювати навіть без 1С. 1С — це лише один із каналів обміну.
Висновок
Твоя ідея правильна стратегічно. Я б її підтримала.
Але реалізовувати треба не як “вивантажили залишки, потім щось перезаписали в 1С”, а як серйозну схему:
власний material ledger
власний production stock
окремий 1C adapter
черга синхронізації
журнал помилок
звірка залишків
пакетне закриття дня
заборона подвійного ручного списання
Це дасть нам незалежність від 1С у виробництві, але не створить хаос у бухгалтерії. Я б саме так і закладала фундамент.

## conversation-turn-25 — user
Turn ID: `882772b8-a25e-4805-8a94-19d68afd2448`

Pasted text.txt
Document
так ще раз тут все вірно я віддаю yf blueprint чи треба ще щось дописати сюди якщо так до додай щоб я передав наш звіт про поточний стан і наміри

## conversation-turn-27 — user
Turn ID: `05288e6e-8e8f-44f7-9c82-43d45198b250`

Pasted text.txt
Document

## conversation-turn-31 — user
Turn ID: `d32e05c9-de94-4105-92fa-6e74ce3e55e2`

Pasted text.txt
Document

## conversation-turn-33 — user
Turn ID: `53553702-f7c0-462d-a589-7812469bb9bb`

Pasted text.txt
Document
ці тести у мене чамусь пусті дай наповнення
test_counterparty_model
test_health
test_library_change_request
test_one_c_snapshot
test_product_model

## conversation-turn-35 — user
Turn ID: `ed08eeb7-b3ef-447b-b9ea-46ef0e02c048`

Pasted text.txt
Document

## conversation-turn-51 — user
Turn ID: `19d6b774-648e-487e-bfd0-d52e4e1736ab`

Pasted text.txt
Document

## conversation-turn-53 — user
Turn ID: `16715b4a-430a-4864-82d3-f207d2597c22`

Pasted text.txt
Document
так все ок 
ще лишилось що доробити з останнго промт blueprint  чи реба вже новий?

## conversation-turn-55 — user
Turn ID: `79928437-aa5a-42d0-8c3c-7220a7b8601e`

Pasted text.txt
Document

## conversation-turn-61 — user
Turn ID: `0ee3f40f-5392-4379-b233-17563bd5364e`

Pasted text.txt
Document

## conversation-turn-63 — user
Turn ID: `942cc145-654a-47f8-9330-99d493a4df62`

Pasted text.txt
Document
так все ок можемо йти далі

## conversation-turn-65 — user
Turn ID: `01ecb516-4ae7-45d8-bb62-fcfde035928b`

Pasted text.txt
Document

## conversation-turn-73 — user
Turn ID: `0a1246ec-f281-4486-924a-66f62c5aeaa3`

Pasted text.txt
Document

## conversation-turn-75 — user
Turn ID: `b700acb4-0697-4ac3-8218-13715132b625`

Pasted text.txt
Document

## conversation-turn-78 — assistant
Turn ID: `ab373c90-8d45-4bd7-8602-56fe8d08d6d9`

Так,
v0.5 перевірки зелені
, можна комітити й пушити.
Стан приймаємо:
Ruff: OK
Pytest: 117 passed, 1 warning
Check-report: OK
v0.5 implementation files: OK
v0.5 test fixture validation: OK
Gitignore sandbox validation: OK
StarletteDeprecationWarning
поки не чіпаємо — це warning із залежностей
fastapi/starlette
, він не блокує проєкт.
Перед комітом зроби:
Bash
git
status
--short
Перевір, щоб не було:
.venv_accounting_registry/
__pycache__/
.pytest_cache/
.ruff_cache/
local_sandbox/
*.1CD
*.dt
*.sqlite
*.db
Якщо все ок, коміт:
Bash
git
add .gitignore README.md app scripts tests reports
git
add tests/fixtures/one_c
git
commit
-m
"Add Accounting Registry sanitized OneC import pipeline"
git
push
Після пушу:
Bash
git
status
Очікувано:
nothing to commit, working tree clean
Після цього v0.5 можна буде закрити completion report для Blueprint.

## conversation-turn-79 — user
Turn ID: `6c1e996a-120d-4532-a5f4-706c1da91066`

Pasted text.txt
Document
так все ок

## conversation-turn-80 — assistant
Turn ID: `7ba77e48-38a5-4227-8d32-c4cef6f659c4`

Супер,
v0.5 закрито успішно
.
Фактичний результат:
Commit: 95d4a55 — Add Accounting Registry sanitized OneC import pipeline
Push: ab48ef1..95d4a55 main -> main
git status: clean
У коміті додано v0.5-пакет: sanitized source intake, export detection/parsers, import pipeline, mapping issue persistence, developer smoke scripts, fixtures і тести; після пушу робоче дерево чисте.
Pasted text
Тепер правильно зробити
completion report для Blueprint
і не стартувати v0.6 без нового дозволу.
Можеш передати Blueprint так:
Accounting Registry v0.5 Completion Report
Accounting Registry v0.5 Completion Report
Target module
forprint_accounting_registry_service
Completed step
Accounting Registry v0.5 — Real Sanitized OneC Test DB and Export Parser Pack
Commit
95d4a55 — Add Accounting Registry sanitized OneC import pipeline
Pushed to:
origin/main
Final Git state
branch: main
origin/main: up to date
working tree: clean
Check results
Ruff lint: OK
Pytest: 117 passed, 1 warning
Check-report: OK
The only warning is
StarletteDeprecationWarning
from FastAPI/Starlette testclient dependency. It does not block current project checks.
Files added / changed
Added sanitized 1C source intake and safety:
app/forprint_accounting_registry_service/one_c_io/sanitization.py
app/forprint_accounting_registry_service/one_c_io/test_database_registry.py
Added export format detection/parsing:
app/forprint_accounting_registry_service/one_c_io/file_formats.py
app/forprint_accounting_registry_service/one_c_io/export_detection.py
app/forprint_accounting_registry_service/one_c_io/export_parsers.py
Added schema probe and import pipeline:
app/forprint_accounting_registry_service/one_c_io/schema_probe.py
app/forprint_accounting_registry_service/one_c_io/import_pipeline.py
Added mapping issue persistence:
app/forprint_accounting_registry_service/storage/mapping_models.py
app/forprint_accounting_registry_service/repositories/mapping_issues.py
app/forprint_accounting_registry_service/services/mapping_issue_registry.py
Updated storage registration:
app/forprint_accounting_registry_service/storage/database.py
Added safe developer smoke scripts:
scripts/one_c_discover_source.py
scripts/one_c_parse_export.py
scripts/one_c_run_import_pipeline.py
Added sanitized parser/import fixtures:
tests/fixtures/one_c/databases/synthetic_test_db.txt
tests/fixtures/one_c/exports/counterparties.csv
tests/fixtures/one_c/exports/counterparties.json
tests/fixtures/one_c/exports/counterparties.xml
tests/fixtures/one_c/exports/payment_register.yaml
Added tests:
tests/unit/test_mapping_issue_persistence.py
tests/unit/test_mapping_issue_registry_service.py
tests/unit/test_one_c_developer_cli.py
tests/unit/test_one_c_directory_practical_import.py
tests/unit/test_one_c_export_parsers.py
tests/unit/test_one_c_import_pipeline.py
tests/unit/test_one_c_report_practical_extraction.py
tests/unit/test_one_c_sandbox_write_hardening.py
tests/unit/test_one_c_sanitization_and_test_db_registry.py
tests/unit/test_one_c_schema_probe.py
Updated:
.gitignore
README.md
reports/accounting_registry_check_report.json
reports/accounting_registry_check_report.md
scripts/run_accounting_registry_checks.py
Sanitized test database source intake status
Implemented:
OneCSanitizationStatus
OneCSanitizationMetadata
OneCTestDatabaseSource
OneCTestDatabaseManifest
OneCSourceChecksum
OneCWorkingCopyManifest
Current behavior:
sanitized test DB source can be registered
unsanitized source is rejected
production source is rejected
checksum can be calculated for local sample file
working copy manifest references original source but remains separate
original source is not mutated by tests
Direct DB/file discovery against sanitized test sources status
Implemented graceful schema probing:
probe_sanitized_source_schema
OneCSchemaProbeResult
Current behavior:
synthetic fixture discovery works
unsupported file/database-like source returns unsupported_source
production source is rejected
schema discovery output remains non-canonical
no write API exists in read-only discovery path
Manual/file export parser status
Implemented parser boundary for:
JSON
CSV
XML
YAML
TXT tabular dump
unknown raw text / unsupported
Current behavior:
json export fixture parses
csv export fixture parses
xml export fixture parses
unknown format returns unsupported_source-style result
raw row values are preserved
unknown columns are preserved
parsed export maps into OneCStagingRecord candidates
Mapping issue persistence status
Implemented storage models:
MappingIssueStorage
UnmappedFieldRecordStorage
RequiredFieldMissingIssueStorage
FieldTypeMismatchIssueStorage
DefaultValueDecisionStorage
Implemented repository/service:
save_mapping_issue
get_mapping_issue
update_mapping_issue_status
mapping_completion_is_blocked
persist_mapping_result
Current behavior:
mapping issue persists
unmapped field persists
required missing field persists
field type mismatch persists
default decision persists
issue can link to staging record
issue status can be updated
critical/manual-review issue blocks mapping completion
resolved issue no longer blocks mapping completion
Import pipeline status
Implemented:
OneCSandboxImportPipeline
OneCImportPipelineResult
OneCImportPipelineStatus
Pipeline:
source manifest / sanitized source
↓
parse export
↓
OneCRawSnapshot
↓
OneCStagingRecord
↓
mapping policy
↓
mapping issue persistence
↓
summary result
Current behavior:
pipeline runs on sanitized JSON fixture
pipeline runs on sanitized CSV fixture
pipeline creates raw snapshots
pipeline creates staging records
pipeline persists mapping issues
pipeline summarizes blocked/manual-review records
unsupported source returns unsupported_source
pipeline refuses unsanitized source
pipeline refuses production source
Directory import/export practical status
Implemented practical import through parsed exports and directory snapshots.
Current behavior:
counterparty directory CSV fixture imports
directory import creates staging records
directory data remains accounting reference only
directory dry-run export remains dry-run
directory export requires manual approval and cannot be production write
Standard report extraction practical status
Implemented report extraction from sanitized fixture exports.
Current behavior:
payment register fixture parses into report snapshot
report rows preserve raw fields
report snapshot remains accounting-only
report extraction does not create CRM / Operational / Library truth
Sandbox write safety status
Hardened sandbox write safety.
Current behavior:
write is blocked by default
write requires explicit destructive flag
write requires disposable source
non-dry-run write requires working copy manifest
write refuses original source as working copy
production source is refused
original source checksum remains unchanged
No real 1C binary mutation was implemented.
Developer CLI / smoke runner status
Implemented safe local smoke scripts:
scripts/one_c_discover_source.py
scripts/one_c_parse_export.py
scripts/one_c_run_import_pipeline.py
These scripts are read-only/sanitized-fixture based by default and do not require real 1C DB files for tests.
Check-report updates
run_accounting_registry_checks.py
now validates:
Ruff lint
Pytest
boundary/storage/OneC docs
v0.5 implementation files
module manifest boundary
placeholder contracts non-canonical
storage model boundary
OneC I/O boundary
fixture safety
v0.5 test fixtures
local sandbox gitignore rules
Boundary confirmation
No live 1C connection was added.
No live 1C write was added.
No production direct DB write was added.
No production synchronization was added.
No automatic posting was added.
No real Gateway integration was added.
No real CRM integration was added.
No real Operational Registry integration was added.
No real Library integration was added.
No real Calculator integration was added.
No real Warehouse integration was added.
No canonical client registry was added.
No canonical order registry was added.
No canonical product/material catalog was added.
No full 1C mirror was added.
No original test DB source is mutated by tests.
All committed fixtures are sanitized/non-production examples.
What the module can now do with sanitized 1C test data
The module can now:
register sanitized local/test 1C-like sources
record source checksums
declare separate working copies
probe schema discovery from fixture/test tables
gracefully reject unsupported binary/database-like sources
parse sanitized JSON/CSV/XML/YAML/TXT exports
preserve raw row/field values
map parsed data into OneCStagingRecord candidates
persist mapping issues into local storage
run offline sanitized import pipeline
produce import summaries
handle practical accounting directory import/export fixtures
handle practical accounting report extraction fixtures
run safe developer smoke scripts
block unsafe production/destructive write paths by default
Remaining open questions before v0.6
Please decide next allowed direction:
1. allow v0.6 real local sanitized 1C export samples from the current business 1C;
2. allow v0.6 stronger parser profiles for specific 1C exports: counterparties, nomenclature, invoices, payments, balances;
3. allow v0.6 mapping UI/admin-review preparation, without CRM ownership;
4. allow v0.6 persistent import history/reporting inside Accounting Registry;
5. allow v0.6 Project Inspector integration for Accounting Registry check reports;
6. pause Accounting Registry until Gateway / Operational Registry contracts are clearer.
Requested Blueprint decision
Please review v0.5 and choose the next allowed step.
Do not authorize live 1C integration unless the production safety model is explicitly approved.
Зараз я б
не рухалась далі без Blueprint
. Поточний модуль уже зробив великий стрибок: від boundary-service до offline sanitized import pipeline, але межа “не production 1C” досі принципова.

## conversation-turn-81 — user
Turn ID: `cd850f84-aa56-427a-99c4-73ac4dc78e20`

Accounting Registry v0.5 is accepted.

Status:
sandbox_1c_import_export_ready

Do not proceed to live 1C integration.
Do not implement production write.
Do not implement automatic posting.

Next allowed v0.6 direction is conditional:
prepare stronger parser profiles only when real sanitized 1C export samples are provided.

Until then:
- maintain v0.5;
- update coordination/status files;
- keep check-report green;
- wait for sanitized counterparties/nomenclature/invoices/payments/balances samples.
Show more
Show less

## conversation-turn-82 — assistant
Turn ID: `c1b7f6da-bbcc-4b15-8377-c06bce0c299d`

Приймаємо це як стоп-сигнал для активної розробки Accounting Registry: v0.5 закритий, v0.6 не стартуємо без реальних sanitized exports. Зараз доцільний тільки maintenance-пакет: статус, вимоги до майбутніх зразків, перевірка, що модуль не рушив далі.

Так, тепер у нас є чітка інструкція:
Accounting Registry v0.5 accepted.
Status: sandbox_1c_import_export_ready.
Do not proceed to live 1C integration.
Do not implement production write.
Do not implement automatic posting.
v0.6 only after real sanitized export samples.
Тобто зараз робимо
малий maintenance/status pack
, без нового функціоналу.
0. Директорії
Bash
cd
/srv/software_development/forprint-project/forprint_accounting_registry_service
mkdir
-p
docs/status
mkdir
-p
docs/development
mkdir
-p
coordination/status
1. Файл:
docs/status/v0_5_accepted.md
Markdown
# Accounting Registry v0.5 Accepted Status

## Status

```text
sandbox_1c_import_export_ready
ForPrint System Blueprint accepted Accounting Registry v0.5.
Accepted capability
The module can now safely work with:
sanitized local/test 1C-like sources;
sanitized manual/file exports;
JSON / CSV / XML / YAML / TXT tabular export fixtures;
parsed export batches;
OneCStagingRecord candidates;
mapping issue persistence;
offline sanitized import pipeline;
accounting directory import/export fixtures;
accounting report extraction fixtures;
safe developer smoke scripts.
Explicitly forbidden
Do not implement:
live 1C connection;
live 1C write;
production direct DB write;
production synchronization;
automatic posting;
real Gateway runtime integration;
real CRM runtime integration;
real Operational Registry runtime integration;
real Library runtime integration;
real Calculator integration;
real Warehouse integration;
canonical client registry;
canonical order registry;
canonical product/material catalog;
full 1C mirror.
v0.6 condition
v0.6 is conditional.
Do not start stronger parser profiles until real sanitized 1C export samples are provided.
Required future sample categories:
counterparties;
nomenclature;
invoices;
payments;
balances.
Current maintenance rule
Until sanitized samples are provided:
maintain v0.5;
keep check-report green;
update coordination/status files;
do not add production 1C behavior;
do not add live write behavior;
do not add automatic posting.
---

# 2. Файл: `docs/development/sanitized_one_c_samples_required.md`

```markdown
# Sanitized OneC Export Samples Required for v0.6

## Purpose

Accounting Registry v0.6 may start only after real sanitized 1C export samples are provided.

The samples are needed to build stronger parser profiles without guessing real 1C export structure.

## Required sample groups

### 1. Counterparties

Expected examples:

- counterparty code;
- name;
- tax ID / EDRPOU if sanitized;
- accounting group if available;
- phone/email only if anonymized;
- 1C reference ID if safe;
- status/activity marker if available.

### 2. Nomenclature

Expected examples:

- 1C nomenclature code;
- name;
- unit;
- accounting group;
- VAT/tax category if available;
- parent group/category if available;
- active/archive status if available.

### 3. Invoices / accounting documents

Expected examples:

- document number;
- document date;
- counterparty accounting reference;
- line items;
- quantities;
- units;
- amounts;
- currency;
- document status if available.

### 4. Payments

Expected examples:

- payment document number;
- payment date;
- amount;
- currency;
- counterparty accounting reference;
- linked invoice/document reference if available;
- payment status if available.

### 5. Balances / settlements

Expected examples:

- counterparty accounting reference;
- period;
- opening balance;
- debit;
- credit;
- closing balance;
- currency.

## Sanitization requirements

Every provided sample must be sanitized.

Required:

```text
real_1c_data: true or false
sanitized: true
production_allowed: false
Forbidden in committed samples:
real personal phone numbers;
real private emails;
real personal names unless anonymized;
real bank accounts;
real client confidential data;
real production DB files;
unsanitized payment data;
live 1C database files.
Storage location
Small sanitized samples may be placed under:
tests/fixtures/one_c/exports/
examples/one_c/
Large or real test DB files must stay only under ignored paths:
local_sandbox/one_c_databases/
local_sandbox/one_c_exports/
local_sandbox/one_c_tmp/
local_sandbox/one_c_working_copies/
v0.6 parser rule
Do not create strong parser profiles by guessing.
Parser profiles should be based on actual sanitized exports from the current business 1C workflow.
---

# 3. Файл: `coordination/status/forprint_accounting_registry_service.status.yaml`

```yaml
module_id: forprint_accounting_registry_service
module_name: ForPrint Accounting Registry Service

current_status: sandbox_1c_import_export_ready
current_phase: v0.5_accepted
development_mode: maintenance_until_sanitized_samples

last_completed_step:
  version: v0.5
  name: Real Sanitized OneC Test DB and Export Parser Pack
  commit: "95d4a55"
  result: accepted_by_blueprint

allowed_now:
  - maintain_v0_5
  - keep_check_report_green
  - update_coordination_status_files
  - wait_for_sanitized_one_c_export_samples

not_allowed_now:
  - live_one_c_connection
  - live_one_c_write
  - production_direct_db_write
  - production_synchronization
  - automatic_posting
  - real_gateway_runtime_integration
  - real_crm_runtime_integration
  - real_operational_registry_runtime_integration
  - real_library_runtime_integration
  - real_calculator_integration
  - real_warehouse_integration
  - canonical_client_registry
  - canonical_order_registry
  - canonical_product_material_catalog
  - full_one_c_mirror

v0_6_condition:
  status: blocked_until_samples_provided
  required_sanitized_samples:
    - counterparties
    - nomenclature
    - invoices
    - payments
    - balances

safety_defaults:
  read_only: true
  production_allowed: false
  writes_allowed: false
  destructive_write_allowed: false
  automatic_posting_allowed: false

check_policy:
  ruff_required: true
  pytest_required: true
  check_report_required: true
4. Тест:
tests/unit/test_v0_5_accepted_status.py
Python
Run
from
pathlib
import
Path
import
yaml
PROJECT_ROOT
=
Path
(
__file__
)
.
resolve()
.
parents[
2
]
def
test_v0_5_accepted_status_doc_exists_and_blocks_live_one_c
() ->
None
:
content
=
(
PROJECT_ROOT
/
"docs/status/v0_5_accepted.md"
)
.
read_text(
encoding
=
"utf-8"
)
assert
"sandbox_1c_import_export_ready"
in
content
assert
"Do not implement"
in
content
assert
"live 1C connection"
in
content
assert
"live 1C write"
in
content
assert
"automatic posting"
in
content
def
test_sanitized_samples_requirement_doc_lists_required_categories
() ->
None
:
content
=
(
PROJECT_ROOT
/
"docs/development/sanitized_one_c_samples_required.md"
)
.
read_text(
encoding
=
"utf-8"
)
required_categories
=
[
"Counterparties"
,
"Nomenclature"
,
"Invoices / accounting documents"
,
"Payments"
,
"Balances / settlements"
,
    ]
for
category
in
required_categories
:
assert
category
in
content
def
test_coordination_status_declares_maintenance_mode_and_v0_6_block
() ->
None
:
path
=
PROJECT_ROOT
/
"coordination/status/forprint_accounting_registry_service.status.yaml"
payload
=
yaml
.
safe_load(
path
.
read_text(
encoding
=
"utf-8"
))
assert
payload
[
"current_status"
]
==
"sandbox_1c_import_export_ready"
assert
payload
[
"current_phase"
]
==
"v0.5_accepted"
assert
payload
[
"development_mode"
]
==
"maintenance_until_sanitized_samples"
assert
payload
[
"v0_6_condition"
][
"status"
]
==
"blocked_until_samples_provided"
not_allowed
=
set
(
payload
[
"not_allowed_now"
])
assert
"live_one_c_connection"
in
not_allowed
assert
"live_one_c_write"
in
not_allowed
assert
"automatic_posting"
in
not_allowed
assert
"production_synchronization"
in
not_allowed
5. Оновити
scripts/run_accounting_registry_checks.py
У список
REQUIRED_BOUNDARY_FILES
додай:
Python
Run
"docs/status/v0_5_accepted.md"
,
"docs/development/sanitized_one_c_samples_required.md"
,
"coordination/status/forprint_accounting_registry_service.status.yaml"
,
Тобто в
check-report
ці статусні файли теж мають контролюватися.
6. Оновити
README.md
У кінець додай:
Markdown
## Current Blueprint status

Current accepted status:

```text
sandbox_1c_import_export_ready
Accounting Registry v0.5 is accepted.
The module is now in maintenance mode until real sanitized 1C export samples are provided.
v0.6 is conditional and must not start until sanitized samples exist for:
counterparties;
nomenclature;
invoices;
payments;
balances.
Current restrictions:
no live 1C connection;
no live 1C write;
no production synchronization;
no automatic posting;
no production direct DB write;
no real CRM/Gateway/Operational Registry/Library/Calculator/Warehouse integration.
---

# 7. Перевірка

```bash
cd /srv/software_development/forprint-project/forprint_accounting_registry_service
source .venv_accounting_registry/bin/activate

python -m ruff check app tests scripts --fix
make check
make check-report
Очікувано:
Ruff: OK
Pytest: 118+ passed
Check-report: OK
8. Коміт
Після зелених перевірок:
Bash
git
status
--short
git
add README.md docs/status docs/development coordination/status scripts tests reports
git
commit
-m
"Mark Accounting Registry v0.5 accepted"
git
push
Після пушу:
Bash
git
status
Має бути:
nothing to commit, working tree clean
Після цього Accounting Registry можна поставити в паузу до моменту, коли з’являться реальні sanitized exports із 1С.
