# System Overview

ForPrint — це модульна система керування рекламно-інформаційним виробництвом / невеликою друкарнею.

Мета системи — максимально зменшити ручну працю, зробити процеси контрольованими, прозорими, розширюваними і придатними до автоматизації через CRM, Telegram Bot, AI-assisted workflows та окремі предметні сервіси.

## Верхні ролі

| Рівень | Роль |
|---|---|
| ForPrint System Blueprint | Описує, як система має бути побудована |
| ForPrint Project Inspector | Перевіряє, чи реальні модулі відповідають Blueprint |
| ForPrint CRM | Диригує бізнес-процесом і показує людям робочий інтерфейс |
| Прикладні модулі | Виконують предметну роботу |

## Принцип

Ми не хочемо ситуації, коли кожен модуль окремо працює добре, але разом вони не стикуються.

Тому Blueprint фіксує:

1. Межі модулів.
2. Власників даних.
3. Контракти між модулями.
4. Потоки даних.
5. Правила впливу змін.
6. Планові і майбутні модулі.
7. Відкриті питання архітектури.


## Integration Gateway

`forprint_integration_gateway` is planned as the technical traffic layer between modules. It validates requests by contracts, routes payloads, provides standardized errors, correlation and idempotency context, and sends audit events to Inspector. It does not replace CRM and does not own business data.
