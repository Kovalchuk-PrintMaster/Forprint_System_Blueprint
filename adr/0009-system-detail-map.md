## Status

Accepted

## Context

ForPrint-екосистема складається з багатьох модулів, які почали розроблятися паралельно. Для подальшої роботи потрібно не тільки знати список модулів, а й бачити, у якому системному шарі кожен модуль працює.

Без такої карти є ризики:

- CRM стане монолітом;
- Telegram Bot стане “бог-модулем”;
- Calculator почне володіти каталогами;
- Library стане операційною базою всього;
- Accounting перетягне на себе operational registry;
- Integration Gateway почне приймати бізнес-рішення.

## Decision

Додати System Detail Map:

```text
machine/system_layers.yaml
machine/system_control_flows.yaml
human/system_detail_map.md
diagrams/system_detail_map.mmd
```

Цей шар описує:

системні layers;
роль кожного layer;
які модулі входять до кожного layer;
що кожному layer заборонено робити;
основні control flows між шарами.
Consequences

Позитивні наслідки:

простіше пояснювати структуру системи;
легше формувати prompts для окремих помічників;
нижчий ризик architecture drift;
Project Inspector отримає основу для layer-based перевірок;
нові модулі буде легше підключати в правильний шар.

Компроміси:

потрібно підтримувати system_layers.yaml актуальним;
якщо модуль змінює роль, треба оновлювати Blueprint;
частина старої термінології має бути поступово замінена.
