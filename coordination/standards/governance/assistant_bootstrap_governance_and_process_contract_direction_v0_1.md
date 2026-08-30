<!-- Integrated from Evening Architecture Package v1.0 on 2026-08-30. This document does not change release/H10 authority by itself. -->

# 01. Evening Architecture Decisions v1.0

## A. Assistant onboarding and project transparency

Новий AI-помічник повинен входити в repository через один front door, а не
хаотично читати файли.

Front-door документ має бути короткою картою:
1. purpose/module identity;
2. architecture;
3. current roadmap;
4. current release/governance;
5. contracts/dependencies;
6. indexes;
7. current/completed/future work;
8. standards/tools;
9. operator interaction profile;
10. context bundle;
11. completion contract.

Два режими:
- `BOOTSTRAP_WITHOUT_TASK` — загальне входження;
- `BOOTSTRAP_FOR_TASK` — входження під конкретний roadmap step.

Контекст передається пакетно:
- bootstrap context bundle;
- task context bundle.

Мінімальний manifest:
```yaml
bundle_id: ...
bundle_type: bootstrap|task
generated_at: ...
module_id: ...
repository_head: ...
blueprint_release_id: ...
governance_snapshot_id: ...
roadmap_step_id: null
included_files: []
source_sha256: {}
bundle_sha256: ...
```

## B. Operator interaction profile

Відокремити поведінкові правила від engineering standards.

Profile:
- українська мова за замовчуванням;
- помічник використовує жіночу граматичну форму;
- оператор — чоловік;
- дружній неофіційний професійний тон;
- Europe/Kyiv;
- terminal-команди короткими блоками;
- великі скрипти — файлами;
- reports — в окремому монотонно нумерованому каталозі;
- backups/diagnostics/work artifacts не змішуються з operator-facing reports.

Рекомендована temporary workspace structure (conceptual):
```text
temporary_workspace_root
  operator_exchange
    reports
    artifacts
  work
  diagnostics
  backups
```

Reports:
```text
report_000001.txt
report_000002.txt
...
```

## C. Roadmap-step lifecycle

Roadmap step — основна керована одиниця, не кожен micro-edit.

START:
- step ID;
- repository state;
- governance snapshot;
- applicable standards;
- context bundle;
- upstream/downstream dependencies.

FINISH:
- index freshness;
- documentation update and roadmap update;
- deterministic validators;
- completion/conformance evidence;
- review/handoff state.

`make check` має лишатися read-only validator. Він не повинен сам створювати
timestamp evidence чи auto-fix index drift.

## D. Versioned process contracts

Будь-який довгий процес pin-иться на revision при старті.

Статуси:
- ACTIVE
- SUPPORTED_LEGACY
- DEPRECATED
- BLOCKED
- REVOKED

Нормальне правило:
процес стартував на R1 → завершується/звітує по R1, навіть якщо існує R2.

Новий R2 застосовується до нових процесів.

Виключення:
BLOCKED/REVOKED означає stop/migrate/restart/recovery. Normal handoff заборонений.

Приймальна сторона валідовує результат валідаторами саме pinned revision,
якщо вона ще supported.

## E. Governance Snapshot

Blueprint повинен мати machine-readable snapshot standards + applicability.

Standard metadata:
```yaml
standard_id: ...
version: ...
status: ...
scope: ...
applicability: ...
supersedes: ...
enforcement_type: machine|mixed|human
validator_id: ...
```

Модуль не доводить «я прочитав стандарт». Він доводить:
- pinned governance snapshot;
- applicable standards;
- PASS детермінованих validators;
- index freshness;
- completion evidence.

Project Inspector перевіряє це незалежно.

## F. Fundamental enforcement split

Instructions = навігація/поведінка.  
Deterministic checks = те, що можна машинно довести.  
Inspector = ecosystem-level незалежна перевірка.

Self-report модуля — evidence input, не authority.
