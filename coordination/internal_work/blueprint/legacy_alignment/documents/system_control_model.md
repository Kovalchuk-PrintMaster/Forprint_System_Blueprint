# ForPrint System Control Model

## Призначення

Цей документ фіксує, як співвідносяться ключові керуючі шари ForPrint-системи.

Головна мета — прибрати плутанину між старими термінами на кшталт `orchestrator`, `sync manager`, `doctor`, `crm core`, `architecture graph`.

## Базова модель

```text
ForPrint System Blueprint
= архітектурна правда.

ForPrint Project Inspector
= ревізор відповідності модулів Blueprint.

ForPrint Integration Gateway
= контрактно-транспортний шар між модулями.

ForPrint CRM
= бізнес-диригент, dashboard, human UI, аналітика.

ForPrint Library
= канонічні довідники, шаблони, техкарти, contracts, semantic registry.

ForPrint Operations Control Registry
= канонічні операційні сутності: client, order, task, production status.

Accounting Registry Service
= бухгалтерський контур, invoice, payment, 1C mapping.

Telegram Bot / Website
= канали взаємодії з клієнтом.

Предметні модулі
= виконують свою вузьку роботу.
```
## Blueprint

Blueprint відповідає на питання:

Як система має бути побудована?

Він містить:

список модулів;
ownership;
data objects;
contracts;
data flows;
impact rules;
module guides;
ADR;
coordination-директорії.

Blueprint не виконує бізнес-процеси.

## Project Inspector

Inspector відповідає на питання:

Чи реальні модулі відповідають Blueprint?

Він читає:

machine/*.yaml;
forprint_module_manifest.yaml;
reports/forprint_module_status.json;
результати тестів/healthchecks.

Inspector не малює архітектуру самостійно. Він перевіряє відповідність.

## Integration Gateway

Integration Gateway відповідає на питання:

Чи коректний запит, чи безпечний payload і куди його технічно передати?

Він робить:

validation;
normalization;
routing;
security filtering;
correlation id;
idempotency;
audit event.

Gateway не приймає бізнес-рішень.

## CRM

CRM відповідає на питання:

Що треба зробити в бізнес-процесі і як це показати людині?

CRM:

показує dashboard;
координує workflow;
запускає сценарії;
показує клієнтів/замовлення/статуси;
формує управлінську аналітику.

CRM не має ставати фізичним власником усіх даних.

## Library

Library відповідає на питання:

Які довідники, шаблони, техкарти, контракти і канонічні назви використовує система?

Library:

material catalog;
product catalog;
templates;
semantic IDs;
alias map;
versioning;
migration graph;
contract definitions.

Library не має ставати операційною базою замовлень.

## Operations Control Registry

Operations Control Registry відповідає на питання:

Яка канонічна операційна правда по клієнтах, замовленнях і задачах?

Він може володіти:

client;
order;
task;
order status;
activity event;
production request.
## Accounting Registry

Accounting Registry відповідає на питання:

Яка бухгалтерська правда і як вона синхронізується з 1С?

Він може володіти:

invoice;
payment status;
accounting document;
1C raw snapshot;
1C staging;
reconciliation report.
## Telegram Bot

Telegram Bot відповідає на питання:

Як клієнт або оператор взаємодіє з системою через Telegram?

Bot:

збирає дані;
уточнює intent;
веде сценарії;
передає запити;
показує статус;
ескалує до AI/людини.

Bot не є source of truth для цін, матеріалів, рахунків або замовлень.

## Website

Website відповідає на питання:

Як клієнт взаємодіє з системою через web?

Website має бути thin client / web channel, а не окрема ізольована CRM.

## Doctor

Doctor зараз не є активним модулем.

Поточний статус:

future_optional_support_tool

Його ідеї можна зберігати для майбутнього, але зараз основний контроль робиться через:

Blueprint + Manifest + Tests + Project Inspector.
## Головний принцип
Жоден прикладний модуль не має самовільно ставати центром усієї системи.

Кожен модуль має:

чітку роль;
чітку межу відповідальності;
manifest;
status report;
контракти;
зв’язок з Blueprint.
