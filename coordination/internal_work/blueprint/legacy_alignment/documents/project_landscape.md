# Поточний ландшафт директорій ForPrint

Цей документ фіксує фактичну картину директорій на сервері станом на 2026-05-21. Він не замінює `machine/modules.yaml`, а доповнює його: `modules.yaml` описує архітектурну роль модулів, а цей документ показує, що вже реально створено на файловій системі.

## Загальний корінь

```text
/srv/software_development/forprint-project
```

## Поточна картина

| Директорія | Архітектурний модуль | Поточний стан | Коментар |
|---|---|---|---|
| `calculator_engine` | `calculator_engine` | active development | Уже має значну структуру, тести, Makefile, pyproject, data/logs/state/quarantine. |
| `forprint_accounting_registry_service` | `accounting_registry_service` | active development | Є app/config/docs/tests/tmp, окрема структура для 1С/обліку. |
| `forprint_crm` | `forprint_crm` | empty directory | Поки тільки місце під майбутній бізнес-диригент і людський інтерфейс. |
| `forprint_integration_gateway` | `forprint_integration_gateway` | empty directory | Поки тільки місце під майбутній контрактно-транспортний шар. |
| `forprint_library` | `forprint_library` | active development | Є app/config/docs/scripts/tests, але перед commit треба прибирати backup/egg-info/__pycache__. |
| `forprint_prepress_hub` | `forprint_prepress_hub` | empty directory | Поки тільки місце під майбутній Prepress Hub. |
| `forprint_system_blueprint` | `forprint_system_blueprint` | active development | Поточний верхній шар архітектурної правди. |
| `telegram_bot` | `telegram_bot` | active development / legacy-rich | Великий наявний проєкт, який треба інтегрувати обережно через manifest/контракти. |

## Важливе правило

Наявність директорії ще не означає, що модуль реалізований. Для Blueprint стан модуля треба визначати не за фактом папки, а за трьома речами:

1. чи є опис у `machine/modules.yaml`;
2. чи є фактичний код/тести/документація;
3. чи є `forprint_module_manifest.yaml` і статусний звіт модуля.

## Перший висновок

Наразі ForPrint має змішаний стан:

- частина модулів уже активно розробляється;
- частина модулів має тільки порожні директорії;
- частина майбутніх модулів ще не має директорій;
- деякі інструменти, наприклад `cloud_backup_manager`, існують поза основним коренем, але мають бути враховані архітектурно.

Це нормальний стан для ранньої фази, але саме тому Blueprint має стати верхнім джерелом правди, щоб усі модулі поступово підтягувалися до єдиної карти.
