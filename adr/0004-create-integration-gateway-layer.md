# ADR 0004: Create ForPrint Integration Gateway layer

## Status

Accepted for Blueprint, implementation planned.

## Context

ForPrint складається з багатьох модулів: CRM, Library, Calculator, Prepress, Operational Registry, Accounting, Warehouse, Logistics, Telegram Bot, Website та інших майбутніх сервісів.

Якщо кожен модуль буде напряму викликати всі інші модулі, система швидко отримає щільну павутину залежностей:

- складно змінювати контракти;
- складно ловити помилки payload;
- складно підключати нові модулі;
- складно зрозуміти, де саме зламався бізнес-сценарій;
- складно захищатися від некоректних або підозрілих зовнішніх запитів.

## Decision

Ввести окремий модуль `forprint_integration_gateway`.

Його роль:

- validation gateway;
- message router;
- contract boundary;
- correlation/idempotency context manager;
- integration audit event producer.

Він не є бізнес-оркестратором і не є джерелом предметних даних.

## Consequences

Позитивні наслідки:

- менше прямих залежностей між модулями;
- легше підключати нові модулі;
- легше перевіряти контракти;
- легше повертати зрозумілі помилки користувачу або оператору;
- Inspector зможе аналізувати інтеграційні події.

Ризики:

- Gateway може стати надто великим, якщо в нього почати переносити бізнес-логіку;
- потрібна дисципліна: бізнес-рішення залишаються в CRM/предметних модулях, а Gateway лише перевіряє і маршрутизує;
- потрібні contract tests, щоб Gateway не став “чорною дірою”.

## Rule

Якщо логіка відповідає на питання “що треба зробити в бізнес-процесі?” — це не Gateway.

Якщо логіка відповідає на питання “чи коректний запит, чи безпечний payload і куди його передати?” — це Gateway.
