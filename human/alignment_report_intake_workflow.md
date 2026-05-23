# Alignment Report Intake Workflow

## Призначення

Цей документ описує, як ForPrint System Blueprint приймає й обробляє відповіді модулів на alignment prompts.

## Базовий цикл

```text
Blueprint створює alignment prompt
↓
prompt зберігається у coordination/outgoing_prompts/<module_id>/drafts/
↓
prompt реєструється у machine/prompt_dispatch_index.yaml
↓
людина переносить prompt у чат відповідного модуля
↓
модульний помічник повертає alignment report
↓
звіт зберігається у coordination/incoming_requests/<module_id>/new/
↓
Blueprint аналізує звіт
↓
якщо треба — оновлює machine/*.yaml, human/*.md, module_guides або prompts
↓
звіт переноситься у reviewed/ або archived/
Де зберігати відповідь модуля

Для кожного модуля:

coordination/incoming_requests/<module_id>/new/

Рекомендована назва:

YYYY-MM-DD-<module_id>-alignment-report.md

Приклад:

coordination/incoming_requests/calculator_engine/new/2026-05-22-calculator-engine-alignment-report.md
Що має бути у звіті

Мінімально:

1. Current state
2. Current architectural role
3. Data currently owned by this module
4. Data consumed from other modules
5. Data provided to other modules
6. Detected architecture drift
7. Contract gaps
8. Safe next corrections
9. Actions that require Blueprint decision
10. Open questions for Blueprint
11. Recommended module priority
12. Summary
Як Blueprint обробляє звіт

Після отримання alignment report треба визначити:

1. Чи модуль рухається в правильному напрямку?
2. Чи є architecture drift?
3. Чи треба змінити Blueprint?
4. Чи треба змінити module guide?
5. Чи треба створити новий contract/data object/impact rule?
6. Чи треба дати модулю новий уточнюючий prompt?
7. Чи треба пригальмувати модуль?
8. Чи треба підняти модуль у пріоритеті?
Статуси обробки
new

Звіт отримано, але ще не розглянуто.

reviewed

Звіт розглянуто, висновки перенесено в Blueprint або зафіксовано окремим рішенням.

archived

Звіт більше не актуальний або замінений новішим.

Що не можна робити

Не можна:

- автоматично приймати всі пропозиції модуля;
- дозволяти модулю самостійно міняти ownership;
- дозволяти модулю самостійно створювати глобальні контракти;
- змішувати alignment report з production status report;
- вважати self-report абсолютною правдою.
Важливе правило

Alignment report — це не наказ Blueprint.

Це вхідна інформація для архітектурного аналізу.

Остаточне рішення приймається у ForPrint System Blueprint через:

machine/*.yaml
human/*.md
adr/*.md
module_guides/*.md
Після обробки

Після аналізу відповіді модулю можна створити:

- уточнений prompt;
- architecture decision record;
- новий data object;
- новий contract;
- нове impact rule;
- зміну module alignment matrix;
- зміну module priority;
- запит до Project Inspector.