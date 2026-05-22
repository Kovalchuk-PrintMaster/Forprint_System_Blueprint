# ADR 0007: Add Project Alignment Layer

## Status

Accepted

## Context

ForPrint-екосистема розвивається через декілька паралельних модулів і декілька окремих діалогів з помічниками. На ранньому етапі це дозволило швидко дослідити напрямки, але також створило ризик різної термінології та різного розуміння ролей.

Особливо ризикові терміни:

- Orchestrator;
- CRM Core;
- Sync Manager;
- Doctor;
- Source of Truth;
- Integration Layer.

## Decision

Додати в ForPrint System Blueprint окремий Project Alignment Layer.

Він складається з:

human/development_standards.md
human/system_control_model.md
human/module_alignment_audit.md
machine/module_alignment_matrix.yaml

Цей шар не є production-кодом. Він потрібен для вирівнювання напрямку розробки всіх модулів.

Consequences

Позитивні наслідки:

усі модулі отримують одну карту термінів;
зменшується ризик architecture drift;
простіше давати уточнюючі prompts окремим помічникам;
легше визначати, який модуль прискорити, який пригальмувати;
Project Inspector отримає кращу основу.

Компроміси:

з’являється ще один шар документації;
матрицю вирівнювання треба оновлювати після важливих рішень;
частину старої термінології доведеться поступово замінити.