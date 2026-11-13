# ForPrint Human Intent Ledger + Expanded Portfolio Projection v0.1

**Date:** 2026-08-30

## Why this exists

Цей документ зберігає не лише технічну інтерпретацію, а **людський намір**: короткі тези 1-2 реченнями, які можна прив'язати до roadmap-кроків. Записи не повинні зникати; при зміні рішення старий запис supersede-иться, але лишається в історії.

### New mandatory evening-dialog output

1. Technical integration package.
2. Human Intent Delta — список нових/змінених тез по модулях.
3. Append-only module intent ledgers.
4. Expanded human portfolio projection, generated from the ledgers.
5. GAP list — що згадувалося, але не відновлено точно (наприклад точні Calculator design-reference URLs).

**Statuses:** AGREED = погоджено/повторно підтверджено; RECOVERED = відновлено з наявних project/portfolio artifacts; PROPOSED = робоча синтетика, ще не затверджена; GAP = відомо, що інформація була/потрібна, але точна деталь не відновлена.

## ForPrint System Blueprint (`forprint_system_blueprint`)

- **AGREED · HI-FP-SYSTEM-BLUEPRINT-001** — Після кожного великого вечірнього діалогу має з’являтися не лише технічний пакет інтеграції, а й окремий людський список домовленостей по кожному модулю.
  - Контекст: Це нове правило сформульоване сьогодні, щоб не втрачати сенс розмови під час технічної нормалізації.
- **AGREED · HI-FP-SYSTEM-BLUEPRINT-002** — Людські тези мають накопичуватися append-only: нові записи додаються, старі не зникають; якщо думка змінилася, стара теза позначається superseded, але лишається видимою.
  - Контекст: Портфоліо повинно показувати історію наміру, а не лише поточну машинну формулу.
- **AGREED · HI-FP-SYSTEM-BLUEPRINT-003** — Для кожного roadmap step потрібне посилання на human-intent записи, які пояснюють, навіщо цей крок існує і що саме люди мали на увазі.
  - Контекст: Це дає можливість повернутися до контексту при двозначності реалізації.
- **AGREED · HI-FP-SYSTEM-BLUEPRINT-004** — Потрібно підтримувати три представлення портфоліо: вузьке машинне, збалансоване технічне та велике людське українською мовою.
  - Контекст: Велике портфоліо не повинно стискати десятки домовленостей до однієї загальної фрази.
- **AGREED · HI-FP-SYSTEM-BLUEPRINT-005** — Один front door для нового помічника має вести до current authority, roadmap, standards, knowledge indexes, active work і потрібного context bundle.
  - Контекст: Без задачі даємо широкий bootstrap; з конкретною задачею — вузький task bundle.
- **AGREED · HI-FP-SYSTEM-BLUEPRINT-006** — make check залишається детермінованим і read-only: він може сказати INDEX_DRIFT, але не повинен тихо переписувати індекси чи завершувати роботу за людину.
  - Контекст: Автоматичні виправлення не повинні ховатися всередині перевірки.
- **AGREED · HI-FP-SYSTEM-BLUEPRINT-007** — Кожна робота стартує на pinned governance/process revision і здається проти цієї ревізії, якщо вона не була явно BLOCKED/REVOKED.
  - Контекст: Нова ревізія не повинна ретроспективно ламати вже розпочату роботу без явної причини.
- **AGREED · HI-FP-SYSTEM-BLUEPRINT-008** — Completion attestation має містити pinned snapshot, standards versions, context bundle, checks, evidence paths, deviations і стан roadmap/contracts.
  - Контекст: Мета — довести відповідність, а не просто написати 'помічник прочитав стандарти'.
- **AGREED · HI-FP-SYSTEM-BLUEPRINT-009** — Inspector повинен незалежно перевіряти completion reports і drift, а Blueprint — показувати портфельну картину та баланс між модулями.
  - Контекст: Inspector не стає semantic owner модулів.
- **RECOVERED · HI-FP-SYSTEM-BLUEPRINT-010** — Blueprint має бачити critical path, blockers, WIP, progress weight, cost/quality/executor evidence і балансувати рух модулів.
  - Контекст: Це вже було в попередньому розширеному портфоліо.
- **AGREED · HI-FP-SYSTEM-BLUEPRINT-011** — PDF-портфоліо є projection для людського review, а не authority. Authority — структуровані записи, roadmap і governance surfaces.
  - Контекст: Щоб дизайн документа не ставав єдиним місцем, де живе домовленість.
- **AGREED · HI-FP-SYSTEM-BLUEPRINT-012** — Canonical UI design system має бути reusable across Website/Mobile/internal surfaces; page-local visual systems не повинні множитися.
  - Контекст: Library owner, consumers adopt.
- **AGREED · HI-FP-SYSTEM-BLUEPRINT-013** — Human portfolio має показувати dependency of each step, а не лише функціональність: хто має закінчити що, щоб цей модуль міг рухатися далі.
  - Контекст: Це основа балансування модулів.

## Calculator Engine (`calculator_engine`)

- **AGREED · HI-CALCULATOR-ENGINE-001** — Calculator Engine має бути головним власником canonical product/job calculation specification: продукт, параметри, матеріали, відходи, технологічні операції, ціна і розрахунковий час.
  - Контекст: Він не повинен перетворюватися на CRM, Warehouse чи Accounting.
- **AGREED · HI-CALCULATOR-ENGINE-002** — Ручне замовлення з filename, hot-folder, CSV, операторської форми або legacy-джерела повинно нормалізуватися в той самий canonical request, що й онлайн-калькулятор.
  - Контекст: Не створюємо другу модель замовлення для ручного потоку.
- **AGREED · HI-CALCULATOR-ENGINE-003** — Парсер filename/ручного вводу не має вгадувати неоднозначні параметри: при ambiguity він повинен вимагати clarification.
  - Контекст: Безпечніше запитати, ніж тихо підставити неправильний матеріал чи тираж.
- **AGREED · HI-CALCULATOR-ENGINE-004** — Після стабілізації canonical schema потрібно зробити versioned filename grammar/parser і hot-folder workflow.
  - Контекст: Спочатку схема, потім адаптери.
- **AGREED · HI-CALCULATOR-ENGINE-005** — Calculator формує canonical Job/Order Specification, який далі використовують Operations Control Registry, Prepress, Warehouse і production.
  - Контекст: Паперові/екранні представлення не повинні дублювати business truth.
- **AGREED · HI-CALCULATOR-ENGINE-006** — Нормативні setup/waste/time rules повинні бути доступні Calculator для оцінки ціни, матеріалу та дедлайну.
  - Контекст: Фактичні production дані можуть пропонувати зміну норми, але не переписувати її автоматично.
- **RECOVERED · HI-CALCULATOR-ENGINE-007** — Website і Mobile повинні вбудовувати Calculator/configurator без дублювання формул та цін у frontend.
  - Контекст: Це вже фіксувалося в попередньому портфоліо.
- **RECOVERED · HI-CALCULATOR-ENGINE-008** — Calculator споживає canonical product/material/machine/print-mode definitions з Library через стабільний контракт.
  - Контекст: Попередні технічні матеріали явно відокремлювали Library reference input від pricing logic.
- **AGREED · HI-CALCULATOR-ENGINE-009** — Для товарів на кшталт футболок, кепок та інших персоналізованих виробів потрібні зручні графічні інструменти/конструктори, які мають бути прив'язані до product configuration.
  - Контекст: Це людська вимога до майбутнього UX калькулятора, а не лише технічний configurator.
- **GAP · HI-CALCULATOR-ENGINE-010** — Ми раніше називали конкретні зовнішні ресурси/сервіси як референси для конструкторів футболок/кепок і навіть визначали пріоритетний. У доступному корпусі файлів точні назви/URL зараз не відновилися.
  - Контекст: Це реальний documentation gap. Його не можна замінювати вигаданими назвами; перед реалізацією треба відновити точний список.
- **AGREED · HI-CALCULATOR-ENGINE-011** — Референсні зовнішні сервіси потрібні не для сліпого копіювання, а як орієнтир по UX, поведінці configurator-а, прев'ю і роботі з зонами друку.
  - Контекст: У roadmap треба зберігати і самі URL/назви, і що саме з них беремо як орієнтир.
- **AGREED · HI-CALCULATOR-ENGINE-012** — Кожен затверджений UX-reference повинен мати priority: primary reference / secondary reference / inspiration only.
  - Контекст: Щоб виконавець не змішував рівнозначно різні джерела.
- **AGREED · HI-CALCULATOR-ENGINE-013** — Якщо в розмові названо конкретний зовнішній сайт/інструмент як референс, його назва й URL повинні потрапити в human-intent entry без узагальнення.
  - Контекст: Саме цього зараз не вистачило для calculator design references.

## ForPrint Operations Assistant (`forprint_operations_assistant`)

- **AGREED · HI-FP-OPERATIONS-ASSISTANT-001** — Operations Assistant має бути максимально простим shop-floor interface: телефон/планшет, QR, великі кнопки, мінімум тексту, poka-yoke.
  - Контекст: Працівник не повинен вчитися працювати зі складною ERP.
- **AGREED · HI-FP-OPERATIONS-ASSISTANT-002** — Працівник є сенсором: швидко повідомляє факт/аномалію, а система валідовує і маршрутизує його до canonical owner.
  - Контекст: Assistant не стає Accounting/Warehouse/production truth.
- **RECOVERED · HI-FP-OPERATIONS-ASSISTANT-003** — Потрібні guided forms і contextual knowledge для receiving, stock check, production checkpoints, QC та видачі.
  - Контекст: Це вже було в старому портфоліо.
- **AGREED · HI-FP-OPERATIONS-ASSISTANT-004** — Для оцінки кількості аркушів або дрібних однотипних предметів має бути практичний режим: поміряти лінійкою висоту стопки і оцінити кількість по calibration profile.
  - Контекст: Саме цей 'лінійка + висота стопки' контекст треба зберігати як людську тезу, а не стискати до абстрактного quantity estimation.
- **AGREED · HI-FP-OPERATIONS-ASSISTANT-005** — Calibration profile для матеріалу/товщини зберігається канонічно в Library; Assistant використовує його як довідкове правило.
  - Контекст: Для кожної оцінки потрібні tolerance/confidence і можливість ручної корекції.
- **AGREED · HI-FP-OPERATIONS-ASSISTANT-006** — Якщо вимірювання виходить за нормальний діапазон, Assistant має запропонувати next safe action: переміряти, розбити стопку, запросити керівника, перейти на вагу/поштучний контроль.
  - Контекст: Не давати впевнене число при поганій якості вимірювання.
- **AGREED · HI-FP-OPERATIONS-ASSISTANT-007** — Worker feedback по production variance має бути дуже коротким: normal / трохи вище / x2 / x5 / severe / machine problem або короткий voice note.
  - Контекст: Детальне виробниче обліковування не можна перекладати на виконавця.
- **AGREED · HI-FP-OPERATIONS-ASSISTANT-008** — На поточному кроці працівник може запитати 'що мені робити?', а Assistant має показати інструкцію з урахуванням order/product/machine/material/role context.
  - Контекст: Перевага: текст -> картинки/схеми -> анімація -> реальне відео.
- **AGREED · HI-FP-OPERATIONS-ASSISTANT-009** — Assistant повинен показувати STOP/hold події вище звичайної черги і вимагати acknowledgement, якщо працівник є адресатом критичної події.
  - Контекст: Скасоване замовлення не повинно тихо залишатися в списку робіт.
- **AGREED · HI-FP-OPERATIONS-ASSISTANT-010** — Усі physical observations повинні мати evidence там, де це практично: фото, timestamp, device/operator, quantity/measurement context.
  - Контекст: Щоб пізніше можна було відновити, звідки взялася цифра.
- **AGREED · HI-FP-OPERATIONS-ASSISTANT-011** — Лінійка/вага/камера/QR — це різні sensing methods; система повинна обирати найпростіший достатньо точний метод під конкретний матеріал.
  - Контекст: Не кожну інвентаризацію треба робити однаково.

## ForPrint Operations Control Registry (`forprint_operations_control_registry`)

- **AGREED · HI-FP-OPERATIONS-CONTROL-REGISTRY-001** — Operations Control Registry володіє operational order lifecycle після canonical specification від Calculator.
  - Контекст: Він координує виконання, а не рахує ціни й не веде бухгалтерію.
- **AGREED · HI-FP-OPERATIONS-CONTROL-REGISTRY-002** — Він резервує матеріал через Warehouse, веде execution gates і production queue.
  - Контекст: Гейти: READY_FOR_PRODUCTION, HOLD_PAYMENT, HOLD_MATERIAL, HOLD_APPROVAL, HOLD_CLARIFICATION, HOLD_PREPRESS.
- **AGREED · HI-FP-OPERATIONS-CONTROL-REGISTRY-003** — Job ticket містить order/revision/time/customer/product/qty/deadline/priority/material/operations/instructions/state/QR.
  - Контекст: Паперовий ticket — лише фізична projection.
- **AGREED · HI-FP-OPERATIONS-CONTROL-REGISTRY-004** — Скан старої ревізії job ticket повинен попередити про застарілий документ і запропонувати актуальну версію.
  - Контекст: Стара роздруківка не може дозволяти виконання старого плану.
- **AGREED · HI-FP-OPERATIONS-CONTROL-REGISTRY-005** — Критичні стани STOP_WORK_REQUIRED, CANCELLED_BY_CUSTOMER та EMERGENCY_HOLD йдуть окремим high-priority channel.
  - Контекст: Сповіщення мають мати audio + visual + acknowledgement + escalation.
- **AGREED · HI-FP-OPERATIONS-CONTROL-REGISTRY-006** — Кожна production action перевіряє current order state: перед START, перед auto machine command, на FINISH і перед handoff.
  - Контекст: QR ідентифікує замовлення, але ніколи не є permission token.
- **AGREED · HI-FP-OPERATIONS-CONTROL-REGISTRY-007** — Якщо cancellation приходить посеред операції, система фіксує фактично виконану частину, блокує handoff і записує physical WIP location/state.
  - Контекст: Не можна вдавати, що операція не починалась або повністю завершена.
- **AGREED · HI-FP-OPERATIONS-CONTROL-REGISTRY-008** — Для зупиненого WIP потрібен окремий event: order_id, operation_id, location_id, quantity_state, stopped_at, stopped_by, reason.
  - Контекст: Далі менеджер вирішує disposition: scrap/retain/rework/repurpose/give/transfer/other.
- **AGREED · HI-FP-OPERATIONS-CONTROL-REGISTRY-009** — Система може автоматично зупинити лише майбутні операції; доля вже виготовленого WIP — авторизоване управлінське рішення.
  - Контекст: Accounting окремо веде фінансові наслідки.
- **AGREED · HI-FP-OPERATIONS-CONTROL-REGISTRY-010** — Operations Control Registry тримає planned-vs-actual operational state по routing/operations, але physical material writeoff лишається у Warehouse.
  - Контекст: Чітко розвести production execution і складський truth.

## ForPrint CRM (`forprint_crm`)

- **AGREED · HI-FP-CRM-001** — CRM має використовувати immutable person_id і organization_id; номер телефону — сильний практичний lookup, але не primary key БД.
  - Контекст: Людина може змінювати телефон, email чи месенджер.
- **AGREED · HI-FP-CRM-002** — Одна людина може представляти різні організації в різний час; це temporal relationship з role, valid_from/to, status, source, confidence.
  - Контекст: При звільненні relation закривається, історія не стирається.
- **AGREED · HI-FP-CRM-003** — Замовлення зберігає snapshot representation: person_id, organization_id, representation_id, confirmed_at.
  - Контекст: Щоб через рік було зрозуміло, від чийого імені робилося замовлення.
- **AGREED · HI-FP-CRM-004** — Telegram або інший канал може один раз на замовлення уточнити, яку організацію людина зараз представляє.
  - Контекст: Це не повинно перетворюватися на нав'язливе підтвердження в кожному повідомленні.
- **AGREED · HI-FP-CRM-005** — Потрібна generic anonymous one-off customer модель для випадків, де повний профіль не має сенсу.
  - Контекст: Не змушувати менеджера створювати фіктивні організації.
- **AGREED · HI-FP-CRM-006** — CRM повинна вміти merge/split/dedup identity і зберігати cross-channel identifiers.
  - Контекст: Телефон, email, Telegram/Viber IDs — це identifiers, а не сама сутність людини.
- **RECOVERED · HI-FP-CRM-007** — CRM — людський cockpit: open work, orders, blockers, communication context, next actions, dashboards і follow-ups.
  - Контекст: Вона не повинна ставати другою базою клієнтів/замовлень/платежів.
- **AGREED · HI-FP-CRM-008** — CRM бере контактний контекст для AR collection, але сам фінансовий стан боргу належить Accounting.
  - Контекст: Менеджер бачить борг і діалог, але ledger truth не дублюється.

## ForPrint Accounting Registry Service (`forprint_accounting_registry_service`)

- **AGREED · HI-FP-ACCOUNTING-REGISTRY-SERVICE-001** — Accounting Registry Service є owner accounts receivable workflow: invoice/order, amount due/paid, due date, payment status, overdue days, promise-to-pay date.
  - Контекст: CRM і Telegram лише допомагають комунікувати.
- **AGREED · HI-FP-ACCOUNTING-REGISTRY-SERVICE-002** — Базовий state machine: DUE -> OVERDUE_SOFT -> OVERDUE_REMINDER -> PROMISE_TO_PAY -> WAITING_PROMISED_DATE -> OVERDUE_ESCALATED -> HUMAN_ATTENTION.
  - Контекст: Клієнтська відповідь змінює стан workflow, а не просто додається коментарем.
- **AGREED · HI-FP-ACCOUNTING-REGISTRY-SERVICE-003** — Side states: DISPUTED, PARTIAL_PAYMENT, PAYMENT_PENDING_RECONCILIATION, CONTACT_UNAVAILABLE, PAUSED, PAID.
  - Контекст: Щоб не штовхати кожен кейс в одну лінійну схему.
- **AGREED · HI-FP-ACCOUNTING-REGISTRY-SERVICE-004** — AI може адаптувати тон нагадування, але не може самостійно блокувати клієнта, зупиняти production/shipping, скасовувати кредит чи списувати борг.
  - Контекст: Це рішення людини/політики.
- **AGREED · HI-FP-ACCOUNTING-REGISTRY-SERVICE-005** — Cadence нагадувань має бути конфігурованим: quiet hours, max per day, importance/history і поточний контекст клієнта.
  - Контекст: Не перетворювати автоматизацію на спам.
- **RECOVERED · HI-FP-ACCOUNTING-REGISTRY-SERVICE-006** — Для procurement/goods receipt потрібен intake з Excel/CSV/PDF, OCR для фото/сканів і focused operator review.
  - Контекст: Попередній портфель уже містив цей напрям.
- **RECOVERED · HI-FP-ACCOUNTING-REGISTRY-SERVICE-007** — Supplier alias learning і fuzzy candidate mapping корисні, але OCR/matching не повинні ставати silent truth.
  - Контекст: Підтверджені mappings можна перевикористовувати.
- **AGREED · HI-FP-ACCOUNTING-REGISTRY-SERVICE-008** — Фактична production variance впливає на actual cost analytics через Accounting, але первинні physical facts приходять від production/Warehouse.
  - Контекст: Не переносити production measurement у бухгалтерський модуль.

## ForPrint Semantic Retrieval Service (PROPOSED) (`forprint_semantic_retrieval_service`)

- **AGREED · HI-FP-SEMANTIC-RETRIEVAL-SERVICE-001** — Ключовий принцип Semantic Retrieval: search finds candidates, domain owner decides truth.
  - Контекст: Пошук не може сам створити canonical клієнта, матеріал чи замовлення.
- **AGREED · HI-FP-SEMANTIC-RETRIEVAL-SERVICE-002** — Сервіс має бути cross-cutting: exact IDs + structured filters + lexical/BM25/trigram + text embeddings + image embeddings + domain/ACL filters + reranking.
  - Контекст: Гібридний пошук, а не лише vector DB.
- **AGREED · HI-FP-SEMANTIC-RETRIEVAL-SERVICE-003** — Search projection містить entity_id, entity_type, source_module, searchable_text, structured attrs, embedding/media refs, source_revision, indexed_at.
  - Контекст: Truth лишається у CRM/Warehouse/Library/OCR.
- **AGREED · HI-FP-SEMANTIC-RETRIEVAL-SERVICE-004** — Result state має бути явним: MATCHES / UNCERTAIN / NO_MATCH / POSSIBLE_NEW_ENTITY.
  - Контекст: Краще UNCERTAIN, ніж неправильний confident match.
- **AGREED · HI-FP-SEMANTIC-RETRIEVAL-SERVICE-005** — Warehouse use case: якщо QR зіпсований або відсутній, працівник описує предмет або фотографує його, а система показує кандидатів.
  - Контекст: Вибір остаточно підтверджує доменний owner/оператор.
- **AGREED · HI-FP-SEMANTIC-RETRIEVAL-SERVICE-006** — Telegram use case: клієнт надсилає фото і пише 'мені треба така штука'; Semantic Retrieval повертає candidates, Telegram уточнює і передає підтверджений контекст у Calculator.
  - Контекст: Це один із головних multimodal сценаріїв.
- **AGREED · HI-FP-SEMANTIC-RETRIEVAL-SERVICE-007** — Потрібен evaluation corpus: recall@5, precision, MRR, no-match accuracy, false-confident-match rate.
  - Контекст: Без вимірювання semantic search легко здається кращим, ніж є.
- **AGREED · HI-FP-SEMANTIC-RETRIEVAL-SERVICE-008** — ACL filtering має відбуватися до disclosure результатів.
  - Контекст: Навіть релевантний кандидат не можна показати користувачу без права доступу.
- **AGREED · HI-FP-SEMANTIC-RETRIEVAL-SERVICE-009** — Сервіс поки лишається PROPOSED_FOR_FORMAL_ADOPTION, не активний canonical module.
  - Контекст: Спочатку formal adoption у Blueprint окремим кроком.

## Telegram Bot (`telegram_bot`)

- **RECOVERED · HI-TELEGRAM-BOT-001** — Telegram має бути conversational operating interface: identity + memory + natural-language intent + multimodal + order/admin orchestration.
  - Контекст: Факти бере з canonical модулів.
- **AGREED · HI-TELEGRAM-BOT-002** — Фото/опис товару йде в Semantic Retrieval, після чого Telegram показує кілька candidates і задає clarification.
  - Контекст: Не відповідати впевнено на основі одного fuzzy match.
- **AGREED · HI-TELEGRAM-BOT-003** — Після підтвердження товару/варіанта Telegram передає structured request у Calculator.
  - Контекст: Chat history не є canonical order.
- **RECOVERED · HI-TELEGRAM-BOT-004** — Speech-to-text повинен проходити через той самий intent pipeline, що й текст.
  - Контекст: Не створювати окрему бізнес-логіку для голосу.
- **RECOVERED · HI-TELEGRAM-BOT-005** — Admin commands і money/destructive actions вимагають strong auth/confirmation.
  - Контекст: Наприклад taxi/procurement/status через owning modules.
- **RECOVERED · HI-TELEGRAM-BOT-006** — Proactive events можуть повідомляти readiness/delay/courier/clarification, але лише з актуальних canonical states.
  - Контекст: Telegram не вигадує статус.
- **AGREED · HI-TELEGRAM-BOT-007** — Для CRM identity Telegram може один раз у контексті замовлення підтвердити organization representation.
  - Контекст: Це допомагає зв'язати канал з CRM без ручного дублювання.

## Website (`website`)

- **RECOVERED · HI-WEBSITE-001** — Website є customer web channel і повинен використовувати ті самі canonical backend capabilities, не створювати власні ціни/матеріали/order truth.
  - Контекст: Це було в попередньому портфоліо.
- **RECOVERED · HI-WEBSITE-002** — Website має вбудовувати Calculator configurator/quote flow без дублювання formulas.
  - Контекст: Frontend лише представляє конфігурацію і результати.
- **RECOVERED · HI-WEBSITE-003** — Потрібні catalog, file upload/design editor integration/preview, checkout, account/status/repeat order.
  - Контекст: Старий портфель вже містив цей flow.
- **AGREED · HI-WEBSITE-004** — Visual product designer для персоналізованих виробів має спиратися на затверджені референсні сервіси й canonical design-system правила.
  - Контекст: Точний список calculator design references зараз позначений GAP до відновлення.
- **RECOVERED · HI-WEBSITE-005** — Website повинен використовувати canonical ForPrint Design System tokens/components/themes/density/accessibility.
  - Контекст: Є окремий Blueprint addendum про owner design system.
- **AGREED · HI-WEBSITE-006** — Website не повинен зберігати business truth у frontend state; assets/order refs мають вести до owning modules.
  - Контекст: Особливо при refresh/retry.
- **RECOVERED · HI-WEBSITE-007** — Потрібні explicit review/confirmation перед final submission і mobile/performance/accessibility considerations.
  - Контекст: Не жертвувати зрозумілістю заради складного конструктора.

## Mobile App (`mobile_app`)

- **RECOVERED · HI-MOBILE-APP-001** — Спочатку треба підтвердити реальну цінність native app проти PWA/responsive web.
  - Контекст: Не будувати native лише тому, що 'має бути додаток'.
- **RECOVERED · HI-MOBILE-APP-002** — Унікальна mobile value: push, camera, file share, device integration, low-friction operational/customer flows.
  - Контекст: Business logic не дублюється на device.
- **RECOVERED · HI-MOBILE-APP-003** — MVP може включати catalog/configuration/calculation/order creation/status через shared APIs.
  - Контекст: Calculator/identity/API readiness — dependency.
- **AGREED · HI-MOBILE-APP-004** — Для працівників shop-floor частина mobile UX може бути Operations Assistant surface, а не окремий паралельний бізнес-додаток.
  - Контекст: Треба не дублювати функції між customer app та internal assistant.
- **AGREED · HI-MOBILE-APP-005** — Єдиний design language з Website/Library UI system є обов'язковим.
  - Контекст: Щоб не з'явилися три різні ForPrint UI.

## ForPrint Library (`forprint_library`)

- **RECOVERED · HI-FP-LIBRARY-001** — Library володіє stable canonical IDs і versioned schemas для products/materials/services/operations.
  - Контекст: Price/accounting/operational state від цього відділений.
- **RECOVERED · HI-FP-LIBRARY-002** — Aliases, supplier part numbers, alternate names, normalization rules і provenance/confidence мають бути частиною semantic layer.
  - Контекст: Це дозволяє безпечно мапити зовнішні джерела.
- **RECOVERED · HI-FP-LIBRARY-003** — External catalog ingestion повинен зберігати source/provider/fetched-at/key/hash/raw snapshot refs і давати human review для ambiguous merge.
  - Контекст: Не переписувати canonical truth без підтвердження.
- **AGREED · HI-FP-LIBRARY-004** — Library є canonical owner calibration profiles для фізичних вимірювань Operations Assistant, включно з параметрами товщини/ваги/толерансів.
  - Контекст: Сам Assistant лише використовує профіль.
- **RECOVERED · HI-FP-LIBRARY-005** — Library -> Calculator reference input має бути deterministic, typed, versioned і read-only.
  - Контекст: Pricing formulas залишаються в Calculator.
- **AGREED · HI-FP-LIBRARY-006** — Library повинна зберігати SOP/instruction/media knowledge для contextual work guidance.
  - Контекст: Operations Assistant показує потрібну інструкцію з контексту.
- **RECOVERED · HI-FP-LIBRARY-007** — Canonical ForPrint Design System owner закріплений за Library; Website та інші UI мають мігрувати до нього без page-local систем.
  - Контекст: Це вже було окремо додано в Blueprint.
- **AGREED · HI-FP-LIBRARY-008** — Reference photos/product media можуть індексуватися Semantic Retrieval, але Library лишається owner canonical assets/metadata.
  - Контекст: Пошуковий індекс — projection.

## ForPrint Prepress Hub (`forprint_prepress_hub`)

- **RECOVERED · HI-FP-PREPRESS-HUB-001** — Prepress Hub має визначити file lifecycle від upload до production-ready, readiness statuses, blockers, warnings, fixable issues і evidence.
  - Контекст: Master file і derived previews потрібно розділяти.
- **RECOVERED · HI-FP-PREPRESS-HUB-002** — Core preflight: format/pages/dimensions/orientation/resolution/bleed/color-space/fonts де це можливо.
  - Контекст: Порівнювати з Calculator job spec і Library requirements.
- **RECOVERED · HI-FP-PREPRESS-HUB-003** — Safe previews/thumbnails і bounded normalization/conversion можуть бути автоматичними, але master не модифікується тихо.
  - Контекст: Потрібен before/after evidence.
- **RECOVERED · HI-FP-PREPRESS-HUB-004** — Operator-assisted fix workflow потрібен для неоднозначних випадків.
  - Контекст: Автоматизація не замінює judgment там, де немає детермінованої відповіді.
- **AGREED · HI-FP-PREPRESS-HUB-005** — Prepress blockers стають HOLD_PREPRESS у Operations Control Registry і блокують production start.
  - Контекст: Гейт має бути видимий в job ticket.
- **AGREED · HI-FP-PREPRESS-HUB-006** — Production-ready package передає verdict + asset refs + revision, щоб стара версія файлу не пішла у виробництво.
  - Контекст: Revision consistency критична.

## Warehouse Service (`warehouse_service`)

- **AGREED · HI-WAREHOUSE-SERVICE-001** — Warehouse володіє physical stock truth, reservations і actual material writeoff.
  - Контекст: Calculator рахує потребу, але не списує склад.
- **AGREED · HI-WAREHOUSE-SERVICE-002** — Operations Control Registry резервує матеріал через Warehouse і отримує HOLD_MATERIAL, якщо ресурс не готовий.
  - Контекст: Ніяких прямих прихованих змін stock з інших модулів.
- **AGREED · HI-WAREHOUSE-SERVICE-003** — Semantic Retrieval допомагає знайти inventory item за описом/фото при відсутньому QR, але Warehouse/оператор підтверджує істину.
  - Контекст: Search лише кандидат.
- **AGREED · HI-WAREHOUSE-SERVICE-004** — Actual consumption/scrap/rework від production має завершуватися коректним physical writeoff у Warehouse.
  - Контекст: Категорії setup waste, production scrap, test samples, destroyed WIP треба розрізняти.
- **RECOVERED · HI-WAREHOUSE-SERVICE-005** — Guided stock checks і discrepancy capture можуть виконуватися через Operations Assistant.
  - Контекст: Physical observation має evidence.
- **AGREED · HI-WAREHOUSE-SERVICE-006** — Одиниці виміру повинні бути нормалізовані, щоб порівнювати expected vs actual.
  - Контекст: Інакше variance не має сенсу.

## Production Runtime Inspector (`production_runtime_inspector`)

- **AGREED · HI-PRODUCTION-RUNTIME-INSPECTOR-001** — Production Runtime Inspector збирає machine/runtime telemetry, але не визначає бізнес-статус замовлення.
  - Контекст: Він є technical evidence source.
- **AGREED · HI-PRODUCTION-RUNTIME-INSPECTOR-002** — Telemetry потрібна для actual cycle time, downtime, machine problems і виявлення аномалій.
  - Контекст: Operations Control Registry використовує її для planned-vs-actual view.
- **AGREED · HI-PRODUCTION-RUNTIME-INSPECTOR-003** — Broken machine або довгі простої не повинні автоматично 'навчити' систему, що погана швидкість є новою нормою.
  - Контекст: Norm change лише через proposal/review.
- **AGREED · HI-PRODUCTION-RUNTIME-INSPECTOR-004** — Runtime data треба корелювати з order_id/operation_id/machine_id/revision там, де це безпечно.
  - Контекст: Щоб факти не змішувалися між роботами.
- **AGREED · HI-PRODUCTION-RUNTIME-INSPECTOR-005** — При STOP_WORK critical state runtime integration не повинна запускати нові commands після gate check failure.
  - Контекст: Перед machine command перевіряється current order state.

## ForPrint Project Inspector (`forprint_project_inspector`)

- **RECOVERED · HI-FP-PROJECT-INSPECTOR-001** — Inspector — незалежний observer/auditor: знаходить repo/standards/knowledge/metadata/dependency drift.
  - Контекст: Не є semantic owner.
- **RECOVERED · HI-FP-PROJECT-INSPECTOR-002** — Цикл: Inspector detects -> local executor repairs/interprets -> Inspector rechecks -> Blueprint governs.
  - Контекст: Так зберігається separation of concerns.
- **AGREED · HI-FP-PROJECT-INSPECTOR-003** — Inspector має незалежно перевіряти completion attestation проти pinned governance snapshot.
  - Контекст: Модуль не може сам собі остаточно засвідчити compliance.
- **AGREED · HI-FP-PROJECT-INSPECTOR-004** — Findings треба ранжувати BLOCKING/HIGH/NORMAL/LOW і подавати в local maintenance queues.
  - Контекст: Не всі проблеми однаково критичні.
- **AGREED · HI-FP-PROJECT-INSPECTOR-005** — Safe deterministic repairs можуть з’явитися пізніше, але semantic/business changes не повинні виконуватись Inspector-ом самостійно.
  - Контекст: Межа автоматизації має бути явною.
- **AGREED · HI-FP-PROJECT-INSPECTOR-006** — Inspector має бачити drift між стандартом, з яким стартував крок, і current standard, але враховувати supported legacy revision policy.
  - Контекст: Не робити фальшиві FAIL лише через новішу ревізію.

## ForPrint Strategic Control Plane (`forprint_strategic_control_plane`)

- **PROPOSED · HI-FP-STRATEGIC-CONTROL-PLANE-001** — Strategic Control Plane у зрілому стані може отримати частину portfolio-level planning/optimization, яку Blueprint тимчасово тримає зараз.
  - Контекст: Точний поділ ще не погоджений.
- **AGREED · HI-FP-STRATEGIC-CONTROL-PLANE-002** — Стратегічні рішення — priority shifts, phase boundaries, destructive/security/cross-repo exceptions — залишаються human-controlled.
  - Контекст: Навіть при сильній автоматизації.
- **PROPOSED · HI-FP-STRATEGIC-CONTROL-PLANE-003** — Може аналізувати cost/quality/lead-time/executor evidence і пропонувати балансування портфеля.
  - Контекст: Але не міняти roadmap authority без governance path.
- **PROPOSED · HI-FP-STRATEGIC-CONTROL-PLANE-004** — Може підтримувати what-if planning і critical-path scenarios для кількох модулів наперед.
  - Контекст: Це кандидат на майбутній рівень, не поточний blocker.
- **GAP · HI-FP-STRATEGIC-CONTROL-PLANE-005** — Не завершено рішення, які функції назавжди лишаться у Blueprint, а які перейдуть сюди/Inspector.
  - Контекст: Це відкрите архітектурне питання.

## ForPrint Integration Gateway (`forprint_integration_gateway`)

- **RECOVERED · HI-FP-INTEGRATION-GATEWAY-001** — Gateway має бути тонким integration boundary: validation, normalization, routing, idempotency, correlation.
  - Контекст: Не бізнес-мозок.
- **RECOVERED · HI-FP-INTEGRATION-GATEWAY-002** — Він не повинен зберігати client/order/material/payment truth.
  - Контекст: Canonical data лишаються в owning modules.
- **AGREED · HI-FP-INTEGRATION-GATEWAY-003** — Manual intake після нормалізації в Calculator і Telegram/Website requests можуть проходити через Gateway тоді, коли з’явиться реальна runtime handoff потреба.
  - Контекст: Не реактивувати його лише заради архітектурної краси.
- **RECOVERED · HI-FP-INTEGRATION-GATEWAY-004** — Errors мають бути typed/structurally stable і не приховувати bad payload silent fixes.
  - Контекст: Краще explicit validation error.
- **AGREED · HI-FP-INTEGRATION-GATEWAY-005** — Semantic Retrieval є окремим сервісом і не повинен перетворювати Gateway на search/AI engine.
  - Контекст: Gateway транспортує запит, не вирішує semantic truth.

## Logistics Service (`logistics_service`)

- **RECOVERED · HI-LOGISTICS-SERVICE-001** — Logistics Service — provider-neutral owner delivery/tracking truth.
  - Контекст: Telegram/CRM показують його стани, але не дублюють provider logic.
- **RECOVERED · HI-LOGISTICS-SERVICE-002** — Taxi/local delivery має окремий provider contract, quote/request/assigned/in-progress/completed/cancelled states.
  - Контекст: Money-spending booking потребує human approval boundary.
- **RECOVERED · HI-LOGISTICS-SERVICE-003** — Provider substitution/fallback не повинен змінювати channel contract.
  - Контекст: Інші модулі не мають знати специфіку кожного перевізника.
- **RECOVERED · HI-LOGISTICS-SERVICE-004** — Retry/backoff/circuit breaker і reconciliation provider state vs local canonical state потрібні для надійності.
  - Контекст: Події delay/exception можуть бути proactive.
- **AGREED · HI-LOGISTICS-SERVICE-005** — Order cancellation/stop-work і delivery cancellation — пов’язані, але окремі workflows; Operations Control Registry ініціює business stop, Logistics керує delivery consequence.
  - Контекст: Не змішувати production і перевізника.

## ForPrint System Administration (`forprint_system_administration`)

- **AGREED · HI-FP-SYSTEM-ADMINISTRATION-001** — System Administration відповідає за printer routing/fallback для job tickets та інших physical outputs.
  - Контекст: Business order truth лишається в Operations Control Registry.
- **AGREED · HI-FP-SYSTEM-ADMINISTRATION-002** — Printer/machine availability та fallback мають бути технічними capability, а permission to choose/override — через Identity & Access policy.
  - Контекст: Не плутати routing з authorization.
- **AGREED · HI-FP-SYSTEM-ADMINISTRATION-003** — Critical alerts потребують надійної audio/visual delivery infrastructure і escalation timers.
  - Контекст: Але semantic state STOP належить OCR.
- **PROPOSED · HI-FP-SYSTEM-ADMINISTRATION-004** — Може підтримувати service health, local device inventory, deployment/runbook surfaces для shop-floor systems.
  - Контекст: Це інфраструктурний шар, не business orchestration.
- **AGREED · HI-FP-SYSTEM-ADMINISTRATION-005** — Temporary/report workspace policy має бути впроваджена технічно: окремі operator_exchange/reports, artifacts, work, diagnostics, backups.
  - Контекст: Щоб tmp корінь не перетворювався на смітник.

## ForPrint Contract Registry (`forprint_contract_registry`)

- **PROPOSED · HI-FP-CONTRACT-REGISTRY-001** — Contract Registry має зберігати versioned inter-module/public contracts і їх adoption/compatibility metadata.
  - Контекст: Не implementation code.
- **AGREED · HI-FP-CONTRACT-REGISTRY-002** — Roadmap steps і completion attestations повинні посилатися на конкретні contract revisions, коли вони є dependency.
  - Контекст: Щоб не було 'контракт десь оновили'.
- **PROPOSED · HI-FP-CONTRACT-REGISTRY-003** — Потрібна видимість consumer/provider compatibility і deprecation windows.
  - Контекст: Особливо для Calculator/Library/Gateway/OCR flows.
- **AGREED · HI-FP-CONTRACT-REGISTRY-004** — Human-intent ledger не замінює contract registry: людська теза пояснює навіщо, контракт описує точну machine boundary.
  - Контекст: Обидва рівні потрібні.
- **GAP · HI-FP-CONTRACT-REGISTRY-005** — Ми ще не проговорили детально кінцевий набір contract-lifecycle функцій цього модуля.
  - Контекст: Портфоліо має показувати цю невідомість, а не заповнювати її синтетикою.

## ForPrint Marketing Orchestrator (`forprint_marketing_orchestrator`)

- **RECOVERED · HI-FP-MARKETING-ORCHESTRATOR-001** — Marketing Orchestrator — майбутній AI-assisted модуль для campaigns/social/content providers.
  - Контекст: Не blocker commercial core.
- **RECOVERED · HI-FP-MARKETING-ORCHESTRATOR-002** — Може вести content calendar, briefs, multi-model generation, approval workflow, publishing і performance learning.
  - Контекст: Autopublish boundary ще треба погодити.
- **RECOVERED · HI-FP-MARKETING-ORCHESTRATOR-003** — Provider/model routing має порівнювати cost/quality/speed для text/image/video.
  - Контекст: Не прив’язувати архітектуру до одного AI provider.
- **AGREED · HI-FP-MARKETING-ORCHESTRATOR-004** — Leads і customer response context мають переходити в CRM через contract, а не жити лише в marketing tool.
  - Контекст: CRM — customer workflow owner.
- **GAP · HI-FP-MARKETING-ORCHESTRATOR-005** — Перший production-complete channel/content slice ще не визначено.
  - Контекст: Потрібно окреме продуктове рішення.

## Cloud Backup Manager (`cloud_backup_manager`)

- **RECOVERED · HI-CLOUD-BACKUP-MANAGER-001** — Cloud Backup Manager тримає backup inventory, status dashboard plan і operator runbook.
  - Контекст: Web admin не повинен тихо запускати destructive backup/restore.
- **RECOVERED · HI-CLOUD-BACKUP-MANAGER-002** — Operator flow: preview -> execute -> verify -> report; guarded actions потребують terminal confirmation.
  - Контекст: Це вже зафіксовано в project roadmap.
- **RECOVERED · HI-CLOUD-BACKUP-MANAGER-003** — Scheduler має бути disabled-by-default до окремої readiness/authorization фази.
  - Контекст: Не вмикати automation просто тому, що код готовий.
- **AGREED · HI-CLOUD-BACKUP-MANAGER-004** — Blueprint portfolio має бачити backup readiness як dependency для критичних модулів, але не управляти backup execution напряму.
  - Контекст: Модуль лишається самодостатнім.
- **PROPOSED · HI-CLOUD-BACKUP-MANAGER-005** — Human-intent ledger для Backup може зберігати операторські причини safety boundaries, щоб майбутній помічник не зняв їх як 'зайві обмеження'.
  - Контекст: Особливо корисно для restore/mirror режимів.
