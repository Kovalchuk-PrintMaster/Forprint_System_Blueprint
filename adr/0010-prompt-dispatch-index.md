# ADR 0010: Add Prompt Dispatch Index

## Status

Accepted

## Context

ForPrint System Blueprint почав формувати уточнюючі prompts для активних модулів. Якщо зберігати prompts тільки як окремі Markdown-файли, швидко стане незрозуміло:

- які prompts уже створено;
- кому вони адресовані;
- чи були вони відправлені;
- яку відповідь ми очікуємо;
- де має лежати alignment report;
- які prompts уже переглянуто.

## Decision

Додати машинний індекс:

machine/prompt_dispatch_index.yaml

А також документ:

human/prompt_dispatch_workflow.md

І легкий валідатор:

scripts/validate_prompt_dispatch_index.py
Consequences

Позитивні наслідки:

prompts стають керованими;
видно статус кожного prompt;
простіше планувати ручне перенесення prompts у модульні чати;
майбутній Project Inspector зможе враховувати prompt/response cycle;
легше бачити, які модулі вже отримали alignment guidance.

Компроміси:

треба оновлювати індекс після створення нових prompts;
статуси поки змінюються вручну;
це не автоматична система синхронізації, а контрольована файлова процедура.