# ADR 0012: Add Module Alignment Execution Plan

## Status

Accepted

## Context

ForPrint System Blueprint уже має alignment prompts і стандарт прийому alignment reports. Але без порядку виконання є ризик знову рухати модулі стихійно.

Потрібно визначити:

- кого аналізувати першим;
- які prompts переносити в першу чергу;
- які модулі тримати в active support;
- які модулі відкласти;
- що робити після отримання alignment report.

## Decision

Додати Module Alignment Execution Plan:

```text
machine/module_alignment_execution_plan.yaml
human/module_alignment_execution_plan.md
```

План розділяє модулі на хвилі:

Wave 1 — core direction alignment
Wave 2 — active support modules
Wave 3 — deferred / later modules

Першим модулем для alignment report обрано calculator_engine.

Consequences

Позитивні наслідки:

зменшується хаос у розвитку модулів;
зрозуміло, кого аналізувати першим;
простіше планувати наступні prompts;
mobile_app враховується як майбутній канал, але не запускається в розробку;
Blueprint стає не тільки картою, а й інструментом керування чергою архітектурного вирівнювання.

Компроміси:

план треба оновлювати після отримання alignment reports;
пріоритети можуть змінюватися після аналізу реального стану модулів;
це ще ручний workflow, не автоматичний Project Inspector.
