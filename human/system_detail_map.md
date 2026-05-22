# ForPrint System Detail Map

## Призначення

Цей документ описує ForPrint-екосистему не як хаотичний набір модулів, а як систему шарів.

Головна мета:

```text
зробити зрозумілою відповідь на питання:
хто за що відповідає,
хто чим не має займатись,
через які шари має проходити взаємодія.
1. Architecture Governance Layer

Модуль:

forprint_system_blueprint

Роль:

джерело архітектурної правди.

Відповідає за:

список модулів;
ownership;
data objects;
contracts;
data flows;
impact rules;
module guides;
ADR;
coordination-директорії;
development standards.

Не відповідає за:

виконання замовлень;
розрахунок цін;
обробку файлів;
маршрутизацію runtime-запитів;
бухгалтерію;
склад.
2. Architecture Compliance Layer

Модулі:

forprint_project_inspector
production_runtime_inspector

Роль:

перевірка відповідності.

Project Inspector має перевіряти:

чи є manifest;
чи manifest відповідає Blueprint;
чи модуль не заявляє заборонену ownership-зону;
чи контракти існують;
чи status report є актуальним;
чи є architecture drift.

Production Runtime Inspector — пізніший шар, для живої production-системи.

3. Integration Transport Layer

Модуль:

forprint_integration_gateway

Роль:

контрактно-транспортний шар.

Відповідає за:

validation;
normalization;
routing;
correlation id;
idempotency;
security filtering;
audit events.

Не відповідає за:

бізнес-рішення;
ціни;
довідники;
клієнтів;
бухгалтерію;
production planning.
4. Business Orchestration Layer

Модуль:

forprint_crm

Роль:

бізнес-диригент і людський інтерфейс.

CRM має:

показувати dashboard;
запускати бізнес-сценарії;
координувати workflow;
показувати клієнтів, замовлення, задачі;
давати управлінську аналітику;
допомагати людині бачити стан системи.

CRM не має ставати:

фізичним власником усіх даних;
складом;
бухгалтерією;
library;
integration gateway.
5. Canonical Registry Layer

Модулі:

forprint_operational_registry
accounting_registry_service

Роль:

канонічні реєстри операційної і бухгалтерської правди.

Operational Registry:

client;
order;
task;
production status;
activity event;
operational history.

Accounting Registry:

invoice;
payment;
accounting document;
1C raw snapshot;
1C staging;
reconciliation.
6. Canonical Knowledge and Catalog Layer

Модуль:

forprint_library

Роль:

канонічна бібліотека довідників, шаблонів, техкарт і контрактів.

Library відповідає за:

material catalog;
product catalog;
machine capabilities;
print modes;
templates;
technical cards;
contract definitions;
semantic registry;
aliases;
migration graph.

Library не відповідає за:

реальні замовлення;
оплату;
client history;
production execution.
7. Domain Execution Layer

Модулі:

calculator_engine
forprint_prepress_hub
warehouse_service
logistics_service
cloud_backup_manager

Роль:

виконання предметної роботи.

Calculator Engine:

quote draft;
price breakdown;
material consumption estimate.

Prepress Hub:

file analysis;
prepress report;
preview;
prepared print file.

Warehouse Service:

stock;
reservation;
write-off;
material movement.

Logistics Service:

delivery providers;
shipping request;
delivery status.

Cloud Backup Manager:

backup jobs;
restore reports;
inventory;
checksum.
8. Customer and Operator Channel Layer

Модулі:

telegram_bot
website

Роль:

канали взаємодії.

Вони можуть:

приймати запити;
уточнювати поля;
показувати статус;
передавати payload у Gateway/CRM;
ескалювати до людини або AI.

Вони не мають:

володіти цінами;
володіти матеріалами;
володіти оплатами;
напряму змінювати канонічні довідники;
напряму керувати всіма модулями.
Головна логіка взаємодії
Blueprint описує, як має бути.
Inspector перевіряє, чи так є.
CRM визначає бізнес-дію.
Gateway перевіряє і маршрутизує payload.
Registry зберігає канонічну операційну/бухгалтерську правду.
Library зберігає канонічні довідники і технічні правила.
Domain modules виконують предметну роботу.
Bot/Website є каналами входу.
Поточний висновок

ForPrint треба розвивати не як один великий моноліт, а як керовану модульну екосистему з чіткими шарами.

Найближчий практичний фокус:

1. Закріпити module manifests.
2. Вирівняти CRM / Library / Calculator / Telegram Bot.
3. Підготувати Project Inspector.
4. Поступово деталізувати Integration Gateway.