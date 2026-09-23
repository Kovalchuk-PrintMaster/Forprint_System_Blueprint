# Evidence Portfolio — Accounting Registry / 1C boundary history

- Source SHA-256: `af8b9e8ee14965e8347011011211b77b562f69a960ac61ab481d7348326bc346`
- Evidence records: **30**
- Attachment-only gaps: **14**
- Authority class: **Accounting Registry module history / non-Blueprint authority**

> Historical evidence only; current Accounting/Operational Registry/Blueprint repositories are not audited.

## EV-ACC1705-0001 — turn 1
**Speaker:** user  
**Evidence role:** owner_intent, 1c_boundary

> ься облік всіх наявних матеріалів я би хотів щоб ми зробили таким чином я б хотів би максимально відв'язатися від 1С в внутрішні технічній роботі нехай там бухгалтерія там возиться з нею далі поки що але щоб наша робота була таким чином що у нас є власна база даних матеріалів ну тобто ми витягуємо всю специфікацію всіх матеріалів всі залишки з 1С формуємо собі там ну 1С певно що формує там якісь документи або щось там подібне ну то не проблема ми його розпарсимо легко і ми собі формуємо надалі свою власну базу даних базуючись на тому що вже є а після цього ми уже перетягуємо одіяло керування на себе тобто всі

**Cue:** Owner wants production/technical work to become autonomous from 1C while accounting can remain there for now.

---

## EV-ACC1705-0002 — turn 1
**Speaker:** user  
**Evidence role:** owner_intent, operational_truth

> Дивись ми зараз накидуємо логіку роботи нашого проекту друкарні і таке питання що треба розібратися з тим як можна скоригувати і синхронізувати роботу нашого проекту з 1С скажімо так вся поточна бухгалтерія і всі фінансові проводки проводяться зараз в 1С там же поки що і ведеться облік всіх наявних матеріалів я би хотів щоб ми зробили таким чином я б хотів би максимально відв'язатися від 1С в внутрішні технічній роботі нехай там бухгалтерія там возиться з нею далі поки що але щоб наша робота була таким чином що у нас є власна база даних матеріалів ну тобто ми витягуємо всю специфікацію всіх матеріалів всі залишки з 1С формуємо собі там ну 1С певно що формує там якісь документи або щось там подібне ну то не проблема ми його розпарсимо легко і ми собі 

**Cue:** Owner proposes importing initial material specification/balances then managing production movement internally.

---

## EV-ACC1705-0003 — turn 1
**Speaker:** user  
**Evidence role:** owner_intent, operational_truth

> ись на тому що вже є а після цього ми уже перетягуємо одіяло керування на себе тобто всі списання всі залишки даних які йдуть по робочим процесам ми переадресовуємо на себе на свій модуль і просто вже потім точково в 1С ми передаємо актуальну інформацію тобто наприклад за поточний день то ну там ми вибираємо там наприклад три або чотири точки передачі даних да там кожні 4 години там наприклад там ну умовно там о 8:00 ранку 12 там четверта і 20 там година там або кожну годину ну то не є принциповим це ми можемо налаштовувати але принциповим є те що ми беремо на себе автономне керування залишками автоном

**Cue:** Owner wants internal control over receipts/write-offs/balances and periodic fact transfer back into 1C.

---

## EV-ACC1705-0004 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_design, authority_split

> ажливим уточненням: нам не треба “ламати” 1С і воювати з нею. Треба зробити так, щоб виробнича система стала головною для реального руху матеріалів , а 1С залишилась бухгалтерською/обліковою системою , куди ми передаємо вже підготовлені, перевірені документи. Тобто модель така: Наш проєкт = фактичний виробничий облік, залишки, списання, резерви, норми, калькуляції, виробничі події. 1С = бухгалтерія, фінансові проводки, офіційні документи, податковий/складський облік, поки що без втручання у виробничу логіку. 1С технічно дозволяє інтеграцію з зовнішніми системами: через REST/OData можна читати й змінювати дані,

**Cue:** Assistant separates production operational truth from accounting/1C truth.

---

## EV-ACC1705-0005 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_design, ledger

> у Я б не робила прямий хаотичний обмін “з 1С туди-сюди”. Я б зробила окремий модуль: inventory_core / materials_ledger Його задача — вести власну книгу руху матеріалів . Не просто таблицю “залишок банеру 800 м²”, а саме журнал подій: material_movement - id - material_id - movement_type: receipt / write_off / reserve / release_reserve / correction / inventory_adjustment - quantity - unit - warehouse_id - production_order_id - source_module - operator_id - created_at - synced_to_1c - sync_batch_id Тоді залишок — це не ручне число, а результат рухів: початковий залишок + прихід - списання - резерв + повернення ± к

**Cue:** Assistant proposes a movement-ledger model rather than one mutable stock number.

---

## EV-ACC1705-0006 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_design, ledger

> гу руху матеріалів . Не просто таблицю “залишок банеру 800 м²”, а саме журнал подій: material_movement - id - material_id - movement_type: receipt / write_off / reserve / release_reserve / correction / inventory_adjustment - quantity - unit - warehouse_id - production_order_id - source_module - operator_id - created_at - synced_to_1c - sync_batch_id Тоді залишок — це не ручне число, а результат рухів: початковий залишок + прихід - списання - резерв + повернення ± коригування = актуальний залишок Це набагато надійніше, ніж просто тримати одну колонку current_stock . Головна ідея: 1С не джерело іс

**Cue:** Movement events include receipt/write-off/reserve/release/correction/inventory-adjustment with provenance.

---

## EV-ACC1705-0007 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_design, authority_split

> Це набагато надійніше, ніж просто тримати одну колонку current_stock . Головна ідея: 1С не джерело істини для виробництва Перший етап — 1С ще джерело стартових даних: 1С → експорт матеріалів, одиниць, залишків, складів, можливо партій Ми імпортуємо це у свою базу: our_materials our_warehouses our_stock_snapshot our_material_movements А далі поступово змінюємо роль: до запуску: 1С = головна по залишках після запуску нашого модуля: наша система = головна по фактичному виробничому руху 1С = отримує результат І це дуже правильний підхід для друкарні, бо 1С часто добре підходить для бухгалтерії, але незручна для живого

**Cue:** 1C is framed as initial/import/accounting system, not long-term production movement authority.

---

## EV-ACC1705-0008 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_design, integration

> пряму синхронізацію, а через чергу Правильна схема: Наш виробничий модуль ↓ таблиця outbox / sync_queue ↓ 1C adapter ↓ 1С ↓ sync_log / результат Тобто коли у нас відбулося списання, ми не одразу ліземо в 1С. Ми створюємо подію: event: material_write_off_created status: pending_sync Потім окремий адаптер бере ці події й передає в 1С. Це дає дуже важливі плюси: 1С впала — виробництво не зупинилось помилка синхронізації — подія не загубилась можна повторити передачу можна бачити, що саме не передалося можна робити передачу раз на годину, 4 рази на день або в кінці дня Частота передачі даних Твоя іде

**Cue:** Integration should be asynchronous through outbox/queue and a 1C adapter.

---

## EV-ACC1705-0009 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_design, sync_modes

> f_day_close: true Але архітектурно краще, щоб система підтримувала обидва режими: 1. scheduled sync — пакетна передача кілька разів на день 2. manual sync — кнопка “передати зараз” 3. end-of-day sync — закриття виробничого дня 4. emergency resync — повторна передача проблемного пакета Що саме треба синхронізувати з 1С Я б поділила обмін на два напрямки. 1. Імпорт з 1С до нашої системи На старті або періодично: довідник матеріалів одиниці виміру склади групи матеріалів залишки на дату можливо постачальники можливо партії/серії, якщо вони ведуться Це режим: 1С → наша система 2. Експорт з нашої

**Cue:** Sync should support scheduled/manual/end-of-day/emergency resync modes.

---

## EV-ACC1705-0010 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_design, auditability

> т. Я б не передавала в 1С тільки голу цифру: Списано банеру: 800 м² Краще передавати документ або пакет документів із розшифровкою: Дата: 2026-05-17 Матеріал: Банер 440 г Склад: Основний Кількість: 800 м² Підстава: виробничі замовлення №... Тип операції: виробниче списання Джерело: ForPrint Inventory Core ID пакета синхронізації: sync_2026_05_17_2000 Бо якщо бухгалтерія потім спитає: “Звідки взялося 800 м²?”, у нас має бути відповідь не словами, а структурованими даними. Я б зробила не пряму синхронізацію, а через чергу Правильна схема: Наш виробничий модуль ↓ таблиця outbox / sync_queue ↓ 1C adapter ↓ 1С ↓

**Cue:** Transfers to 1C should carry structured provenance, not just a naked aggregate number.

---

## EV-ACC1705-0011 — turn 25
**Speaker:** user  
**Evidence role:** owner_workflow, blueprint_coordination

> Pasted text.txt Document так ще раз тут все вірно я віддаю yf blueprint чи треба ще щось дописати сюди якщо так до додай щоб я передав наш звіт про поточний стан і наміри

**Cue:** Owner prepares a current-state/intent report for Blueprint review.

---

## EV-ACC1705-0012 — turn 33
**Speaker:** user  
**Evidence role:** owner_observation, testing

> пусті дай наповнення test_counterparty_model test_health test_library_change_request test_one_c_snapshot test_product_model

**Cue:** Owner reports several tests are empty and asks for actual test contents.

---

## EV-ACC1705-0013 — turn 53
**Speaker:** user  
**Evidence role:** owner_workflow, prompt_governance

> Pasted text.txt Document так все ок ще лишилось що доробити з останнго промт blueprint чи реба вже новий?

**Cue:** Owner checks whether the current Blueprint prompt is complete before requesting a new one.

---

## EV-ACC1705-0014 — turn 78
**Speaker:** assistant  
**Evidence role:** assistant_report, validation

> к, v0.5 перевірки зелені , можна комітити й пушити. Стан приймаємо: Ruff: OK Pytest: 117 passed, 1 warning Check-report: OK v0.5 implementation files: OK v0.5 test fixture validation: OK Gitignore sandbox validation: OK StarletteDeprecationWarning поки не чіпаємо — це warning із залежностей fastapi/starlette , він не блокує проєкт. Перед комітом зроби: Bash git status --short Перевір, щоб не було: .venv_accounting_registry/ __pycache__/ .pytest_cache/ .ruff_cache/ local_sandbox/ *.1CD *.dt *.sqlite *.db Якщо все ок, коміт: Bash git add .gitignore README.md app scripts tests reports git ad

**Cue:** Historical v0.5 gate reports Ruff OK, pytest 117 passed, check-report OK and fixture/gitignore safety checks green.

---

## EV-ACC1705-0015 — turn 78
**Speaker:** assistant  
**Evidence role:** assistant_rule, repository_hygiene

> ір, щоб не було: .venv_accounting_registry/ __pycache__/ .pytest_cache/ .ruff_cache/ local_sandbox/ *.1CD *.dt *.sqlite *.db Якщо все ок, коміт: Bash git add .gitignore README.md app scripts tests reports git add tests/fixtures/one_c git commit -m "Add Accounting Registry sanitized OneC import pipeline" git push Після пушу: Bash git status Очікувано: nothing to commit, working tree clean Після цього v0.5 можна буде закрити completion report для Blueprint.

**Cue:** Before commit, assistant explicitly excludes local sandbox/1C database/cache artifacts.

---

## EV-ACC1705-0016 — turn 80
**Speaker:** assistant  
**Evidence role:** assistant_report, git

> Супер, v0.5 закрито успішно . Фактичний результат: Commit: 95d4a55 — Add Accounting Registry sanitized OneC import pipeline Push: ab48ef1..95d4a55 main -> main git status: clean У коміті додано v0.5-пакет: sanitized source intake, export detection/parsers, import pipeline, mapping issue persistence, developer smoke scripts, fixtures і тести; після пушу робоче дерево чисте. Pasted text Тепер правильно зробити completion report для Blueprint і не стартувати v0.6 без нового дозволу. Можеш передати Blueprint так: Accounting Registry v0.5 Completion Report Accounti

**Cue:** Historical v0.5 implementation commit is pushed cleanly to main.

---

## EV-ACC1705-0017 — turn 80
**Speaker:** assistant  
**Evidence role:** assistant_report, v0.5

> ne Push: ab48ef1..95d4a55 main -> main git status: clean У коміті додано v0.5-пакет: sanitized source intake, export detection/parsers, import pipeline, mapping issue persistence, developer smoke scripts, fixtures і тести; після пушу робоче дерево чисте. Pasted text Тепер правильно зробити completion report для Blueprint і не стартувати v0.6 без нового дозволу. Можеш передати Blueprint так: Accounting Registry v0.5 Completion Report Accounting Registry v0.5 Completion Report Target module forprint_accounting_registry_service Completed step Accounting Registry v0.5 — Real Sanitized OneC Test DB and Exp

**Cue:** v0.5 package adds sanitized source intake, format detection/parsers, schema probe, offline import pipeline and mapping-issue persistence.

---

## EV-ACC1705-0018 — turn 80
**Speaker:** assistant  
**Evidence role:** assistant_report, safety

> behavior: sanitized test DB source can be registered unsanitized source is rejected production source is rejected checksum can be calculated for local sample file working copy manifest references original source but remains separate original source is not mutated by tests Direct DB/file discovery against sanitized test sources status Implemented graceful schema probing: probe_sanitized_source_schema OneCSchemaProbeResult Current behavior: synthetic fixture discovery works unsupported file/database-like source returns unsupported_source production source is rejected schema discovery output remains non-canon

**Cue:** Historical behavior rejects unsanitized/production sources and keeps original source unmodified.

---

## EV-ACC1705-0019 — turn 80
**Speaker:** assistant  
**Evidence role:** assistant_report, parsers

> Супер, v0.5 закрито успішно . Фактичний результат: Commit: 95d4a55 — Add Accounting Registry sanitized OneC import pipeline Push: ab48ef1..95d4a55 main -> main git status: clean У коміті додано v0.5-пакет: sanitized source intake, export detection/parsers, import pipeline, mapping issue persistence, developer smoke scripts, fixtures і тести; після пушу робоче дерево чисте. Pasted text Тепер правильно зробити completion report для Blueprint і не стартувати v0.6 без нового дозволу. Можеш передати Blueprint так: Accounting Registry v0.5 Completion Report Accounting Registry v0.5 Completion Report Target module forprint_accounting_registry_service Completed step Accounting Registry v0.5 — Real Sanitized OneC Test DB and Export Parser Pack Commit 95d4a55 

**Cue:** v0.5 supports sanitized manual/file export parsing across common structured/tabular formats.

---

## EV-ACC1705-0020 — turn 80
**Speaker:** assistant  
**Evidence role:** assistant_report, staging

> rns unsupported_source production source is rejected schema discovery output remains non-canonical no write API exists in read-only discovery path Manual/file export parser status Implemented parser boundary for: JSON CSV XML YAML TXT tabular dump unknown raw text / unsupported Current behavior: json export fixture parses csv export fixture parses xml export fixture parses unknown format returns unsupported_source-style result raw row values are preserved unknown columns are preserved parsed export maps into OneCStagingRecord candidates Mapping issue persistence status Implemented storage mo

**Cue:** Schema discovery/import outputs remain noncanonical staging evidence rather than authoritative business state.

---

## EV-ACC1705-0021 — turn 81
**Speaker:** user  
**Evidence role:** owner_input, blueprint_acceptance

> Accounting Registry v0.5 is accepted. Status: sandbox_1c_import_export_ready Do not proceed to live 1C integration. Do not implement production write. Do not implement automatic posting. Next allowed v0.6 direction is conditional: prepare stronger parser profiles only when real sanitized 1C export samples are provided. Until then: - maintain v0.5; - update coordination/status files; - keep check-report green; - wait for sanitized counterparties/nomenclature/invoices/payments/balances samples. Show more Show less

**Cue:** Owner supplies Blueprint acceptance/status for Accounting Registry v0.5.

---

## EV-ACC1705-0022 — turn 81
**Speaker:** user  
**Evidence role:** owner_input, safety_boundary

> Accounting Registry v0.5 is accepted. Status: sandbox_1c_import_export_ready Do not proceed to live 1C integration. Do not implement production write. Do not implement automatic posting. Next allowed v0.6 direction is conditional: prepare stronger parser profiles only when real sanitized 1C export samples are provided. Until then: - maintain v0.5; - update coordination/status files; - keep check-report green; - wait for sanitized counterparties/nomenclature/invoices/payments/balances samples. Show more Show less

**Cue:** Accepted v0.5 explicitly blocks live 1C integration.

---

## EV-ACC1705-0023 — turn 81
**Speaker:** user  
**Evidence role:** owner_input, safety_boundary

> epted. Status: sandbox_1c_import_export_ready Do not proceed to live 1C integration. Do not implement production write. Do not implement automatic posting. Next allowed v0.6 direction is conditional: prepare stronger parser profiles only when real sanitized 1C export samples are provided. Until then: - maintain v0.5; - update coordination/status files; - keep check-report green; - wait for sanitized counterparties/nomenclature/invoices/payments/balances samples. Show more Show less

**Cue:** Accepted v0.5 explicitly blocks production writes.

---

## EV-ACC1705-0024 — turn 81
**Speaker:** user  
**Evidence role:** owner_input, safety_boundary

> port_ready Do not proceed to live 1C integration. Do not implement production write. Do not implement automatic posting. Next allowed v0.6 direction is conditional: prepare stronger parser profiles only when real sanitized 1C export samples are provided. Until then: - maintain v0.5; - update coordination/status files; - keep check-report green; - wait for sanitized counterparties/nomenclature/invoices/payments/balances samples. Show more Show less

**Cue:** Accepted v0.5 explicitly blocks automatic accounting posting.

---

## EV-ACC1705-0025 — turn 81
**Speaker:** user  
**Evidence role:** owner_input, next_gate

> xt allowed v0.6 direction is conditional: prepare stronger parser profiles only when real sanitized 1C export samples are provided. Until then: - maintain v0.5; - update coordination/status files; - keep check-report green; - wait for sanitized counterparties/nomenclature/invoices/payments/balances samples. Show more Show less

**Cue:** v0.6 is conditional on actual sanitized 1C export samples.

---

## EV-ACC1705-0026 — turn 82
**Speaker:** assistant  
**Evidence role:** assistant_summary, module_boundary

> ibrary runtime integration; real Calculator integration; real Warehouse integration; canonical client registry; canonical order registry; canonical product/material catalog; full 1C mirror. v0.6 condition v0.6 is conditional. Do not start stronger parser profiles until real sanitized 1C export samples are provided. Required future sample categories: counterparties; nomenclature; invoices; payments; balances. Current maintenance rule Until sanitized samples are provided: maintain v0.5; keep check-report green; update coordination/status files; do not add production 1C behavior; do not add live write beha

**Cue:** Maintenance instructions explicitly forbid Accounting Registry from becoming canonical client/order/product/material owner.

---

## EV-ACC1705-0027 — turn 82
**Speaker:** assistant  
**Evidence role:** assistant_summary, integration_boundary

> ; automatic posting; real Gateway runtime integration; real CRM runtime integration; real Operational Registry runtime integration; real Library runtime integration; real Calculator integration; real Warehouse integration; canonical client registry; canonical order registry; canonical product/material catalog; full 1C mirror. v0.6 condition v0.6 is conditional. Do not start stronger parser profiles until real sanitized 1C export samples are provided. Required future sample categories: counterparties; nomenclature; invoices; payments; balances. Current maintenance rule Until sanitized samples are provided: maintain v0.5; ke

**Cue:** Maintenance status forbids live Operational Registry/Library/Calculator/Warehouse/Gateway/CRM integrations at this stage.

---

## EV-ACC1705-0028 — turn 82
**Speaker:** assistant  
**Evidence role:** assistant_summary, v0.6_inputs

> il real sanitized 1C export samples are provided. Required future sample categories: counterparties; nomenclature; invoices; payments; balances. Current maintenance rule Until sanitized samples are provided: maintain v0.5; keep check-report green; update coordination/status files; do not add production 1C behavior; do not add live write behavior; do not add automatic posting. --- # 2. Файл: `docs/development/sanitized_one_c_samples_required.md` ```markdown # Sanitized OneC Export Samples Required for v0.6 ## Purpose Accounting Registry v0.6 may start only after real sanitized 1C export sample

**Cue:** Future sanitized sample categories include counterparties, nomenclature, invoices, payments and balances.

---

## EV-ACC1705-0029 — turn 82
**Speaker:** assistant  
**Evidence role:** assistant_summary, maintenance

> ; payments; balances. Current maintenance rule Until sanitized samples are provided: maintain v0.5; keep check-report green; update coordination/status files; do not add production 1C behavior; do not add live write behavior; do not add automatic posting. --- # 2. Файл: `docs/development/sanitized_one_c_samples_required.md` ```markdown # Sanitized OneC Export Samples Required for v0.6 ## Purpose Accounting Registry v0.6 may start only after real sanitized 1C export samples are provided. The samples are needed to build stronger parser profiles without guessing real 1C export structure. ## Req

**Cue:** Until samples exist, only maintenance/status work is authorized; no new production functionality.

---

## EV-ACC1705-0030 — turn 82
**Speaker:** assistant  
**Evidence role:** assistant_summary, data_safety

> ery provided sample must be sanitized. Required: ```text real_1c_data: true or false sanitized: true production_allowed: false Forbidden in committed samples: real personal phone numbers; real private emails; real personal names unless anonymized; real bank accounts; real client confidential data; real production DB files; unsanitized payment data; live 1C database files. Storage location Small sanitized samples may be placed under: tests/fixtures/one_c/exports/ examples/one_c/ Large or real test DB files must stay only under ignored paths: local_sandbox/one_c_databases/ local_sandbox/one_c_ex

**Cue:** Future sample handling requires sanitized data and forbids real personal/bank data in committed fixtures.

---
