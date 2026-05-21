# ForPrint System Blueprint

**ForPrint System Blueprint** — це верхній архітектурний шар для всієї екосистеми ForPrint.

Він не приймає замовлення, не рахує ціни, не обробляє файли і не виконує бізнес-операції. Його задача — тримати архітектурну правду: які модулі існують, хто за що відповідає, які дані кому належать, які контракти між модулями, які потоки даних активні або плануються.

## Головна формула

```text
Blueprint каже: “так має бути”.
Inspector каже: “ось що реально є”.
CRM диригує бізнес-процесом і показує людям робочий інтерфейс.
Прикладні модулі виконують свою предметну роботу.
```

## Важливе уточнення про CRM

У цьому Blueprint CRM не вважається фізичним сховищем клієнтів, замовлень і документів.

`forprint_crm` — це бізнес-диригент / прикладний оркестратор / людський інтерфейс. Він координує бізнес-процеси, показує клієнтів, замовлення, статуси, аналітику і звіти, але канонічні записи мають належати окремим реєстрам або предметним модулям.

Початковий розподіл:

- `forprint_operational_registry` — клієнти, замовлення, історія взаємодій, операційні статуси.
- `accounting_registry_service` — рахунки, оплати, бухгалтерські документи, сумісність / синхронізація з 1С.
- `forprint_crm` — керування процесом, візуалізація, звіти, аналітика, координація модулів.

Це можна буде уточнювати, але в стартовому каркасі ми не змішуємо “диригента” і “сховище правди”.

## Швидкий старт на Debian

```bash
cd /srv/software_development/forprint-project/forprint_system_blueprint
python3.11 -m venv .venv_blueprint
source .venv_blueprint/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
make check
```

## Основні команди

```bash
make validate   # перевірити YAML-опис архітектури
make diagrams   # згенерувати Mermaid-діаграми
make guides     # згенерувати module_guides/*.md
make test       # запустити unit-тести
make check      # lint + тести + валідація + генерація
```

## Структура

```text
forprint_system_blueprint/
├── human/          # людські пояснення архітектури
├── machine/        # YAML-джерело архітектурної правди
├── diagrams/       # Mermaid-діаграми
├── module_guides/  # промти / guide-файли для окремих модулів
├── coordination/   # робочі черги промтів, запитів і review-пакетів
├── adr/            # архітектурні рішення
├── scripts/        # генератори і валідатори
└── tests/          # самоконтроль цього Blueprint-проєкту
```

## Принцип роботи з модулями

1. Зміна архітектури вноситься в `machine/*.yaml`.
2. Запускається `make check`.
3. Генеруються оновлені діаграми і module guides.
4. Якщо зміна стосується дочірнього модуля, формується файл у `coordination/outgoing_prompts/<module_id>/drafts/`.
5. Після погодження промт переходить у `approved/`, потім у `sent/`.
6. Дочірній модуль може надсилати запити назад у `coordination/incoming_requests/<module_id>/new/`.
7. Для великих шматків діалогу, архівів або аналізу є `coordination/review_packets/<module_id>/new/`.

## Git-практика

Після кожного завершеного проміжного кроку:

```bash
make check
git status
git add .
git commit -m "Describe completed blueprint step"
git push
```

Не комітити:

- `.venv_blueprint/`
- `__pycache__/`
- `.pytest_cache/`
- тимчасові архіви
- службове сміття редакторів

- `.gitignore` for Python caches, virtual environments, local logs, temporary files, archives and secrets.
- `.gitkeep` files for empty coordination folders so the prompt/request/review structure is preserved in Git.

## Integration Gateway decision

Blueprint now includes `forprint_integration_gateway` as a planned transport/contract layer. It validates requests, normalizes payloads, adds correlation/idempotency context, routes requests between modules, and reports integration/audit events. It must not own business truth or business decisions.




After unpacking, run:

```bash
make clean
git status --short
```

The `.venv_blueprint/` directory must not appear in `git status --short`.
