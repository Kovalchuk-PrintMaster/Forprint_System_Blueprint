# Evidence Portfolio — Prepress Hub 20.05 bootstrap

- Source SHA-256: `7093b97b3b5e16aed5ebc71fcbaf8f878417f0c93a99e4fc9b5f3b6b26afe0ca`
- Evidence records: **22**
- Authority class: **Prepress module history / non-Blueprint authority**
- Prior agreement attachment: **referenced but not recoverable**

> Concrete scaffold/code is historical proposal only; current implementation is not audited.

## EV-PRE2005-0001 — turn 1
**Speaker:** user  
**Evidence role:** owner_instruction, module_start

> prepress_hub.docx Document так дивись ми починаємо з тобою роботу над новим модулем ForPrint Prepress Hub у гас вже є робоча директорія на сервері деми можемо почати роботу над проєктом /srv/software_development/forprint-project/forprint_prepress_hub попередньо у нас вже була розмова над тим як може виглядати проєкт і я тобі у вкладенні даю промт і початкові домовленості Show more Show less

**Cue:** Owner says this is the start of work on the new ForPrint Prepress Hub module.

---

## EV-PRE2005-0002 — turn 1
**Speaker:** user  
**Evidence role:** owner_context, repo_path

> t Prepress Hub у гас вже є робоча директорія на сервері деми можемо почати роботу над проєктом /srv/software_development/forprint-project/forprint_prepress_hub попередньо у нас вже була розмова над тим як може виглядати проєкт і я тобі у вкладенні даю промт і початкові домовленості Show more Show less

**Cue:** Owner provides the existing server working directory.

---

## EV-PRE2005-0003 — turn 1
**Speaker:** user  
**Evidence role:** owner_context, attachment_gap

> print_prepress_hub попередньо у нас вже була розмова над тим як може виглядати проєкт і я тобі у вкладенні даю промт і початкові домовленості Show more Show less

**Cue:** Owner says prior prompt/agreements are attached; the attachment body is not visible in MHTML.

---

## EV-PRE2005-0004 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_summary_of_attachment, architecture

> Я прийняла стартові умови: модуль окремий, робоча директорія вже є, і фокус — не “плагін”, а локальний центр керування препрес-процесами. Зараз швидко зафіксую архітектурне рішення й дам перший робочий крок без роздування проєкту. Прийняла. Фіксую стартову рамку для ForPrint Prepress Hub . З вкладення я беру за основу такі домовленості: це не окремий Adobe-плагін під кожну програму, а локальний центр керування препрес-ланцюжками , де HTML/web-панель є тільки інтерфейсом, Python — мозком, Adobe actions/scripts — виконавцями, presets — технологічними картами, а logs — виробничим контролем prepress_hub .

**Cue:** Assistant summarizes the attached intent as a local prepress control center rather than one plugin per Adobe app.

---

## EV-PRE2005-0005 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_summary_of_attachment, architecture

> е окремий Adobe-плагін під кожну програму, а локальний центр керування препрес-ланцюжками , де HTML/web-панель є тільки інтерфейсом, Python — мозком, Adobe actions/scripts — виконавцями, presets — технологічними картами, а logs — виробничим контролем prepress_hub . Стартове рішення Для першого етапу робимо: ForPrint Prepress Hub = Python backend + локальна web-панель + preset engine + тести Поки не ліземо в Acrobat / Photoshop / Illustrator напряму . Спочатку будуємо стабільний каркас: /srv/software_development/forprint-project/forprint_prepress_hub Перший робочий проміжний крок: структура проєкту; venv; pyproject.toml ; FastAPI health endpoin

**Cue:** Assistant summarizes UI/backend/executor/preset/log separation from the missing attachment.

---

## EV-PRE2005-0006 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_plan, bootstrap

> им контролем prepress_hub . Стартове рішення Для першого етапу робимо: ForPrint Prepress Hub = Python backend + локальна web-панель + preset engine + тести Поки не ліземо в Acrobat / Photoshop / Illustrator напряму . Спочатку будуємо стабільний каркас: /srv/software_development/forprint-project/forprint_prepress_hub Перший робочий проміжний крок: структура проєкту; venv; pyproject.toml ; FastAPI health endpoint; конфігурація; базовий loader для YAML-пресетів; перший тестовий preset; тести; Makefile. Це буде “нульова платформа”, на яку далі безболісно додамо PDF-пресети, drag-and-drop, READY/ERROR, job log і hot folders. Команди для першого запуску У директорії проєкт

**Cue:** Assistant proposes the first bounded platform.

---

## EV-PRE2005-0007 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_plan, scope

> у робимо: ForPrint Prepress Hub = Python backend + локальна web-панель + preset engine + тести Поки не ліземо в Acrobat / Photoshop / Illustrator напряму . Спочатку будуємо стабільний каркас: /srv/software_development/forprint-project/forprint_prepress_hub Перший робочий проміжний крок: структура проєкту; venv; pyproject.toml ; FastAPI health endpoint; конфігурація; базовий loader для YAML-пресетів; перший тестовий preset; тести; Makefile. Це буде “нульова платформа”, на яку далі безболісно додамо PDF-пресети, drag-and-drop, READY/ERROR, job log і hot folders. Команди для першого запуску У директорії проєкту: Bash cd /srv/software_development/forprint-project/forpr

**Cue:** First phase avoids direct Adobe integration.

---

## EV-PRE2005-0008 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_plan, repository_structure

> srv/software_development/forprint-project/forprint_prepress_hub Перший робочий проміжний крок: структура проєкту; venv; pyproject.toml ; FastAPI health endpoint; конфігурація; базовий loader для YAML-пресетів; перший тестовий preset; тести; Makefile. Це буде “нульова платформа”, на яку далі безболісно додамо PDF-пресети, drag-and-drop, READY/ERROR, job log і hot folders. Команди для першого запуску У директорії проєкту: Bash cd /srv/software_development/forprint-project/forprint_prepress_hub python3.11 -m venv .venv_prepress_hub source .venv_prepress_hub/bin/activate mkdir -p app/forprint_prepress_hub/core mkdir -p app/forpr

**Cue:** Assistant lists the initial project structure and runtime/data/log/test directories.

---

## EV-PRE2005-0009 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_plan, service_scaffold

> forprint_prepress_hub Перший робочий проміжний крок: структура проєкту; venv; pyproject.toml ; FastAPI health endpoint; конфігурація; базовий loader для YAML-пресетів; перший тестовий preset; тести; Makefile. Це буде “нульова платформа”, на яку далі безболісно додамо PDF-пресети, drag-and-drop, READY/ERROR, job log і hot folders. Команди для першого запуску У директорії проєкту: Bash cd /srv/software_development/forprint-project/forprint_prepress_hub python3.11 -m venv .venv_prepress_hub source .venv_prepress_hub/bin/activate mkdir -p app/forprint_prepress_hub/core mkdir -p app/forprint_prepress_hub/api mkdir -p app/forprint_prepr

**Cue:** Bootstrap includes health endpoint, config and YAML preset loader.

---

## EV-PRE2005-0010 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_plan, preset

> t_data [ "_file" ] = preset_path . name presets . append( preset_data ) return presets presets/pdf_basic_check.yaml YAML name: pdf_basic_check title: "PDF: базова перевірка файлу" description: "Перший тестовий пресет. Поки не запускає Acrobat, а тільки фіксує майбутню структуру." input: extensions: - ".pdf" steps: - type: internal_check name: check_file_exists - type: internal_check name: check_extension_pdf output: folder: "data/ready" filename_template: "{original_stem}_CHECKED.pdf" on_error: move_to: "data/error" write_report: true tests/test_health.py Python Run from fastapi . testclient import TestClient from forprint_prep

**Cue:** First preset is only a structural/test preset and does not launch Acrobat.

---

## EV-PRE2005-0011 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_plan, make_surface

> (PIP) install -e ".[dev]" test: $(PYTHON) -m pytest -q lint: $(PYTHON) -m ruff check app tests check: lint test run: $(PYTHON) -m uvicorn forprint_prepress_hub.main:app --app-dir app --host 0.0.0.0 --port 8020 --reload health: curl http://127.0.0.1:8020/health app/forprint_prepress_hub/__init__.py Python Run """ForPrint Prepress Hub package.""" app/forprint_prepress_hub/main.py Python Run from fastapi import FastAPI from forprint_prepress_hub . core . settings import get_settings from forprint_prepress_hub . core . presets import load_presets settings = get_settings () app = FastAPI ( title = "ForPrint Prepress Hub" , versi

**Cue:** Proposed Makefile `check` is read-only lint+test, with run/health separate.

---

## EV-PRE2005-0012 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_plan, runtime

> tests check: lint test run: $(PYTHON) -m uvicorn forprint_prepress_hub.main:app --app-dir app --host 0.0.0.0 --port 8020 --reload health: curl http://127.0.0.1:8020/health app/forprint_prepress_hub/__init__.py Python Run """ForPrint Prepress Hub package.""" app/forprint_prepress_hub/main.py Python Run from fastapi import FastAPI from forprint_prepress_hub . core . settings import get_settings from forprint_prepress_hub . core . presets import load_presets settings = get_settings () app = FastAPI ( title = "ForPrint Prepress Hub" , version = "0.1.0" , description = "Local hub for prepress automation workflows." , ) @ app . get ( "/health" ) d

**Cue:** Proposed development server binds all interfaces with reload, despite being described as local.

---

## EV-PRE2005-0013 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_plan, configuration

> s ( BaseSettings ): """Головні налаштування локального сервісу.""" environment : str = "local" project_root : Path = Path ( "/srv/software_development/forprint-project/forprint_prepress_hub" ) presets_dir : Path = project_root / "presets" incoming_dir : Path = project_root / "data" / "incoming" processing_dir : Path = project_root / "data" / "processing" ready_dir : Path = project_root / "data" / "ready" error_dir : Path = project_root / "data" / "error" logs_dir : Path = project_root / "logs" model_config = SettingsConfigDict ( env_prefix = "FORPRINT_PREPRESS_HUB_" , env_file = ".env" , env_file_encoding = "utf-8" , ) @ lru_cache de

**Cue:** Settings hard-code the historical absolute project path as the default root.

---

## EV-PRE2005-0014 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_plan, preset_loader

> s_hub . core . settings import get_settings from forprint_prepress_hub . core . presets import load_presets settings = get_settings () app = FastAPI ( title = "ForPrint Prepress Hub" , version = "0.1.0" , description = "Local hub for prepress automation workflows." , ) @ app . get ( "/health" ) def health () -> dict : """Базова перевірка, що сервіс живий.""" return { "status" : "ok" , "service" : "ForPrint Prepress Hub" , "environment" : settings . environment, } @ app . get ( "/presets" ) def presets () -> dict : """Повертає список доступних YAML-пресетів.""" loaded_presets = load_presets ( settings . presets_dir) retu

**Cue:** Preset loader reads YAML files and annotates each with source filename.

---

## EV-PRE2005-0015 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_boundary, scope

> _dir : Path ) -> list [ dict [ str , Any ]]: """ Завантажує YAML-пресети з директорії presets. На цьому етапі це ще не виконує препрес-операції. Зараз задача — перевірити, що система бачить технологічні карти. """ if not presets_dir . exists(): return [] presets : list [ dict [ str , Any ]] = [] for preset_path in sorted ( presets_dir . glob( "*.yaml" )): with preset_path . open( "r" , encoding = "utf-8" ) as file : preset_data = yaml . safe_load( file ) or {} preset_data [ "_file" ] = preset_path . name presets . append( preset_data ) return presets presets/pdf_basic_check.yaml YAML name: pdf_basic_check title: "PDF: базова перевірка файлу" description:

**Cue:** Preset loader explicitly does not perform prepress operations yet.

---

## EV-PRE2005-0016 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_plan, job_lifecycle

> print_prepress_hub/adapters mkdir -p app/forprint_prepress_hub/workers mkdir -p config presets data/incoming data/processing data/ready data/error logs tests Після того створюємо файли. pyproject.toml TOML [build-system] requires = ["setuptools>=69", "wheel"] build-backend = "setuptools.build_meta" [project] name = "forprint-prepress-hub" version = "0.1.0" description = "Local prepress automation hub for ForPrint workflows" requires-python = ">=3.11" dependencies = [ "fastapi>=0.110", "uvicorn[standard]>=0.29", "pydantic>=2.7", "pydantic-settings>=2.2", "PyYAML>=6.0", "python-multipart>=0.0.9", ] [project.optional-depend

**Cue:** Proposed local job-state folders are incoming/processing/ready/error.

---

## EV-PRE2005-0017 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_plan, repository_hygiene

> e gitignore .venv*/ __pycache__/ *.pyc .pytest_cache/ .ruff_cache/ *.egg-info/ .env logs/*.log logs/*.jsonl data/incoming/* data/processing/* data/ready/* data/error/* !data/incoming/.gitkeep !data/processing/.gitkeep !data/ready/.gitkeep !data/error/.gitkeep Щоб Git бачив порожні директорії: Bash touch data/incoming/.gitkeep touch data/processing/.gitkeep touch data/ready/.gitkeep touch data/error/.gitkeep Перевірка Після створення файлів: Bash source .venv_prepress_hub/bin/activate make install make check Очікувано має бути приблизно так: ruff check app tests All checks passed! pytest -q ... [100%] Потім запуск: Bash

**Cue:** Proposed repository ignores runtime logs and job data while tracking .gitkeep placeholders.

---

## EV-PRE2005-0018 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_acceptance_hint, bootstrap_gate

> 127.0.0.1:8020/presets Що вважати завершенням першого кроку Перший крок завершений, якщо: Bash make check проходить без помилок, /health повертає status: ok , а /presets бачить pdf_basic_check.yaml . Після цього наступним кроком я б додала вже Job Runner v1 : прийняти шлях до PDF, скопіювати оригінал у data/processing/job_xxx/ , не чіпати оригінал, виконати internal steps і записати logs/jobs.jsonl .

**Cue:** First-step completion criteria are green `make check`, `/health` OK and preset discovery.

---

## EV-PRE2005-0019 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_plan, next_step

> tus: ok , а /presets бачить pdf_basic_check.yaml . Після цього наступним кроком я б додала вже Job Runner v1 : прийняти шлях до PDF, скопіювати оригінал у data/processing/job_xxx/ , не чіпати оригінал, виконати internal steps і записати logs/jobs.jsonl .

**Cue:** Next step is a bounded Job Runner after the zero-platform gate.

---

## EV-PRE2005-0020 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_plan, input_safety

> check.yaml . Після цього наступним кроком я б додала вже Job Runner v1 : прийняти шлях до PDF, скопіювати оригінал у data/processing/job_xxx/ , не чіпати оригінал, виконати internal steps і записати logs/jobs.jsonl .

**Cue:** Proposed Job Runner should copy original into a job processing folder rather than mutate it.

---

## EV-PRE2005-0021 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_boundary, input_safety

> ала вже Job Runner v1 : прийняти шлях до PDF, скопіювати оригінал у data/processing/job_xxx/ , не чіпати оригінал, виконати internal steps і записати logs/jobs.jsonl .

**Cue:** Original input preservation is explicit in the proposed next-step workflow.

---

## EV-PRE2005-0022 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_plan, observability

> и оригінал у data/processing/job_xxx/ , не чіпати оригінал, виконати internal steps і записати logs/jobs.jsonl .

**Cue:** Job Runner proposal includes append-style job log output.

---
