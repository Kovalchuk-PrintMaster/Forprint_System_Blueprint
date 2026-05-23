# ADR 0011: Add Alignment Report Intake Standard

## Status

Accepted

## Context

ForPrint System Blueprint уже створив alignment prompts для ключових модулів. Наступна проблема — стандартизовано приймати відповіді від модулів.

Без єдиного формату відповіді буде важко порівнювати:

- поточний стан різних модулів;
- architecture drift;
- contract gaps;
- питання до Blueprint;
- рекомендовані пріоритети.

## Decision

Додати Alignment Report Intake Standard:

```text
coordination/templates/module_alignment_report_template.md
machine/module_alignment_report_schema.yaml
human/alignment_report_intake_workflow.md

Також додати тест, який перевіряє наявність ключових секцій.

Consequences

Позитивні наслідки:

відповіді модулів стануть порівнюваними;
легше буде приймати архітектурні рішення;
простіше визначати, які модулі треба коригувати;
можна буде поступово автоматизувати аналіз alignment reports.

Компроміси:

модульні помічники мають відповідати за шаблоном;
перші звіти можуть бути неповними;
schema поки описова, а не жорстка JSON Schema.