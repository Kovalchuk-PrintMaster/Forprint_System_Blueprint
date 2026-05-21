# Coordination Workspace

Це легкий робочий контур для промтів, запитів і review-пакетів між Blueprint та дочірніми модулями.

Це не окремий важкий сервіс. На старті використовується проста файлова структура + git.

## Outgoing prompts

`coordination/outgoing_prompts/<module_id>/drafts/` — чернетки промтів для модуля.

`approved/` — погоджені промти, готові до передачі в модуль.

`sent/` — промти, які вже передані / використані.

## Incoming requests

`coordination/incoming_requests/<module_id>/new/` — запити від модуля до Blueprint.

`reviewed/` — переглянуті запити.

`archived/` — закриті запити.

## Review packets

`coordination/review_packets/<module_id>/new/` — місце для великих фрагментів діалогу, архівів, коду, які треба проаналізувати з погляду архітектури.

## Рекомендований формат назви файлу

```text
YYYY-MM-DD__short-topic__target-module.md
```

Наприклад:

```text
2026-05-21__calculator-quote-contract-review__calculator_engine.md
```
