# Prompt Dispatch Workflow

## Призначення

Цей документ описує, як ForPrint System Blueprint веде облік уточнюючих prompts для окремих модулів.

Мета — не загубити, кому який prompt уже підготовлено, у якому він статусі, і яку відповідь ми очікуємо.

## Основна логіка

Blueprint формує prompt
↓
prompt зберігається у coordination/outgoing_prompts/<module_id>/drafts/
↓
prompt реєструється у machine/prompt_dispatch_index.yaml
↓
людина переносить prompt у відповідний модульний чат
↓
статус можна змінити з draft на sent
↓
модуль повертає alignment report
↓
відповідь зберігається у coordination/incoming_requests/<module_id>/new/
↓
Blueprint аналізує відповідь і оновлює архітектуру / module guide / prompt

Статуси
draft

Prompt підготовлено, але ще не передано в модульний чат.

approved

Prompt переглянуто людиною і дозволено до відправки.

sent

Prompt уже передано в модульний чат або відповідному помічнику.

reviewed

Відповідь модуля отримано і переглянуто.

archived

Prompt більше не актуальний або замінений новішим.

Структура outgoing prompts
coordination/outgoing_prompts/<module_id>/drafts/
coordination/outgoing_prompts/<module_id>/approved/
coordination/outgoing_prompts/<module_id>/sent/
Структура incoming requests
coordination/incoming_requests/<module_id>/new/
coordination/incoming_requests/<module_id>/reviewed/
coordination/incoming_requests/<module_id>/archived/
Що має повернути модуль

Для alignment prompt очікується короткий alignment report:

1. Current state
2. Detected architecture drift
3. Data owned by module
4. Data consumed from other modules
5. Data provided to other modules
6. Safe next corrections
7. Open questions for Blueprint
Чому це важливо

Без такого індексу prompts швидко перетворяться на хаотичні файли.

З індексом ми бачимо:

- які модулі вже отримали уточнення;
- які ще чекають;
- які відповіді ми очікуємо;
- де зберігати alignment reports;
- які prompts треба оновити після зміни Blueprint.
Правило

Prompt Dispatch Index не замінює Project Inspector.

Це легкий координаційний інструмент для ручного етапу вирівнювання модулів.