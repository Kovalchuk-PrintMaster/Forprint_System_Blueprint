# ForPrint Module Alignment Audit

## Призначення

Цей документ фіксує поточну оцінку модулів ForPrint-екосистеми.

Його задача — не критикувати старі рішення, а вирівняти всі модулі в єдину архітектурну карту.

## Загальний стан

Проєкт розвивався стихійно через декілька паралельних гілок:

- Library;
- Calculator Engine;
- Telegram Bot;
- Accounting / 1C;
- Prepress Hub;
- Cloud Backup Manager;
- CRM;
- System Blueprint.

Це нормальний етап для раннього проєкту. Але далі потрібна централізація термінів, ролей і контурів відповідальності.

## Найбільші ризики

### 1. CRM може стати “власником усього”

Ризик:

CRM почне фізично зберігати клієнтів, замовлення, оплату, статуси, довідники, аналітику і стане монолітом.

Правильне рішення:

CRM = бізнес-диригент + dashboard + human UI.
Operations Control Registry = canonical operational data.
Accounting Registry = бухгалтерські дані.
Library = довідники.
2. Telegram Bot може стати “бог-модулем”

Ризик:

Bot має доступ до клієнта, AI, файлів і сценаріїв, тому може почати робити все напряму.

Правильне рішення:

Bot = channel + workflow client.
Всі системні дії через Gateway / CRM / Registry / Library / Calculator.
3. Calculator може почати володіти каталогами

Ризик:

Calculator для зручності заводить власні materials/products і поступово стає паралельним catalog owner.

Правильне рішення:

Calculator може мати cache/snapshot, але canonical catalog owner = Library.
4. Library може стати “складом усього”

Ризик:

Library почне зберігати все: клієнтів, замовлення, оплату, файли, status.

Правильне рішення:

Library = довідники, шаблони, contracts, semantic registry, versioning.
Не operational data.
5. Accounting може перетягнути operational registry

Ризик:

Через 1С і рахунки Accounting Registry почне ставати головною базою замовлень.

Правильне рішення:

Accounting = invoices, payments, 1C mapping, reconciliation.
Operations Control Registry = orders, clients, statuses.
6. Старий термін Orchestrator може плутати систему

Ризик:

Різні помічники вкладали різний зміст у слово Orchestrator.

Правильне рішення:

Не використовувати Orchestrator як назву нового модуля без уточнення.
Функції розкладені між:
- CRM;
- Integration Gateway;
- Blueprint;
- Project Inspector.
Пріоритети
Найближчий пріоритет
1. Завершити Project Alignment Layer.
2. Дати всім модулям module manifest standard.
3. Створити перші manifests у реальних активних модулях.
4. Вирівняти CRM, Calculator, Library, Telegram Bot.
Другий пріоритет
1. Почати мінімальний Project Inspector.
2. Навчити його читати Blueprint + manifests.
3. Показувати architecture drift.
Третій пріоритет
1. Деталізувати Integration Gateway.
2. Описати route contracts.
3. Підготувати перші payload examples.
Пізніше
1. Production Runtime Inspector.
2. Doctor / Auto-repair.
3. Visual editor.
4. Runtime dashboards.
Поточне рішення по Doctor

Doctor поки не розробляється.

Статус:

planned_optional_future_tool

Причина:

Проєкт ще сирий. Автоматичне форматування, перенесення, пошук і виправлення шляхів може створити більше ризиків, ніж користі.

Допускається:

збирати ідеї;
документувати потенційні перевірки;
зберігати як майбутній support tool.
Висновок

Поточний напрямок System Blueprint правильний.

Найважливіша робота зараз:

Не писати багато нового коду,
а вирівняти карту системи, ролі модулів, контракти і наступні пріоритети.