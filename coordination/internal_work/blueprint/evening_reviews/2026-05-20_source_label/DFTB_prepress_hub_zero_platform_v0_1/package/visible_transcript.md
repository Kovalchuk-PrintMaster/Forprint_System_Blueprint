# Visible Transcript

> Exact recoverable MHTML text. Referenced `prepress_hub.docx` body is absent.

## conversation-turn-1.1 — user
Message ID: `f44fadbd-9cc1-449b-abd7-88ca450105bb`

prepress_hub.docx
Document
так дивись ми починаємо з тобою роботу над новим модулем 
ForPrint Prepress Hub
у гас вже є робоча директорія на сервері деми можемо почати роботу над проєктом 
/srv/software_development/forprint-project/forprint_prepress_hub
попередньо у нас вже була розмова над тим як може виглядати проєкт і я тобі у вкладенні даю промт і початкові домовленості
Show more
Show less

## conversation-turn-2.1 — assistant
Message ID: `0109dcf5-fd64-4a57-aca1-b4e4d71dba11`

Я прийняла стартові умови: модуль окремий, робоча директорія вже є, і фокус — не “плагін”, а локальний центр керування препрес-процесами. Зараз швидко зафіксую архітектурне рішення й дам перший робочий крок без роздування проєкту.

## conversation-turn-2.2 — assistant
Message ID: `7d3be04c-df68-4785-8f06-68de4dfa6857`

Прийняла. Фіксую стартову рамку для
ForPrint Prepress Hub
.
З вкладення я беру за основу такі домовленості: це не окремий Adobe-плагін під кожну програму, а
локальний центр керування препрес-ланцюжками
, де HTML/web-панель є тільки інтерфейсом, Python — мозком, Adobe actions/scripts — виконавцями, presets — технологічними картами, а logs — виробничим контролем
prepress_hub
.
Стартове рішення
Для першого етапу робимо:
ForPrint Prepress Hub = Python backend + локальна web-панель + preset engine + тести
Поки
не ліземо в Acrobat / Photoshop / Illustrator напряму
. Спочатку будуємо стабільний каркас:
/srv/software_development/forprint-project/forprint_prepress_hub
Перший робочий проміжний крок:
структура проєкту;
venv;
pyproject.toml
;
FastAPI health endpoint;
конфігурація;
базовий loader для YAML-пресетів;
перший тестовий preset;
тести;
Makefile.
Це буде “нульова платформа”, на яку далі безболісно додамо PDF-пресети, drag-and-drop, READY/ERROR, job log і hot folders.
Команди для першого запуску
У директорії проєкту:
Bash
cd
/srv/software_development/forprint-project/forprint_prepress_hub

python3.11
-m
venv .venv_prepress_hub
source
.venv_prepress_hub/bin/activate
mkdir
-p
app/forprint_prepress_hub/core
mkdir
-p
app/forprint_prepress_hub/api
mkdir
-p
app/forprint_prepress_hub/adapters
mkdir
-p
app/forprint_prepress_hub/workers
mkdir
-p
config presets data/incoming data/processing data/ready data/error logs tests
Після того створюємо файли.
pyproject.toml
TOML
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "forprint-prepress-hub"
version = "0.1.0"
description = "Local prepress automation hub for ForPrint workflows"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.29",
    "pydantic>=2.7",
    "pydantic-settings>=2.2",
    "PyYAML>=6.0",
    "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "ruff>=0.4",
]

[tool.setuptools.packages.find]
where = ["app"]

[tool.pytest.ini_options]
pythonpath = ["app"]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
Makefile
Makefile
PYTHON=.venv_prepress_hub/bin/python
PIP=.venv_prepress_hub/bin/pip

.PHONY: install test lint check run health

install:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check app tests

check: lint test

run:
	$(PYTHON) -m uvicorn forprint_prepress_hub.main:app --app-dir app --host 0.0.0.0 --port 8020 --reload

health:
	curl http://127.0.0.1:8020/health
app/forprint_prepress_hub/__init__.py
Python
Run
"""ForPrint Prepress Hub package."""
app/forprint_prepress_hub/main.py
Python
Run
from
fastapi
import
FastAPI
from
forprint_prepress_hub
.
core
.
settings
import
get_settings
from
forprint_prepress_hub
.
core
.
presets
import
load_presets
settings
=
get_settings
()
app
=
FastAPI
(
title
=
"ForPrint Prepress Hub"
,
version
=
"0.1.0"
,
description
=
"Local hub for prepress automation workflows."
,
)
@
app
.
get
(
"/health"
)
def
health
() ->
dict
:
"""Базова перевірка, що сервіс живий."""
return
{
"status"
:
"ok"
,
"service"
:
"ForPrint Prepress Hub"
,
"environment"
:
settings
.
environment,
    }
@
app
.
get
(
"/presets"
)
def
presets
() ->
dict
:
"""Повертає список доступних YAML-пресетів."""
loaded_presets
=
load_presets
(
settings
.
presets_dir)
return
{
"count"
:
len
(
loaded_presets
),
"presets"
:
loaded_presets
,
    }
app/forprint_prepress_hub/core/__init__.py
Python
Run
"""Core logic for ForPrint Prepress Hub."""
app/forprint_prepress_hub/core/settings.py
Python
Run
from
functools
import
lru_cache
from
pathlib
import
Path
from
pydantic_settings
import
BaseSettings
,
SettingsConfigDict
class
Settings
(
BaseSettings
):
"""Головні налаштування локального сервісу."""
environment
:
str
=
"local"
project_root
:
Path
=
Path
(
"/srv/software_development/forprint-project/forprint_prepress_hub"
)
presets_dir
:
Path
=
project_root
/
"presets"
incoming_dir
:
Path
=
project_root
/
"data"
/
"incoming"
processing_dir
:
Path
=
project_root
/
"data"
/
"processing"
ready_dir
:
Path
=
project_root
/
"data"
/
"ready"
error_dir
:
Path
=
project_root
/
"data"
/
"error"
logs_dir
:
Path
=
project_root
/
"logs"
model_config
=
SettingsConfigDict
(
env_prefix
=
"FORPRINT_PREPRESS_HUB_"
,
env_file
=
".env"
,
env_file_encoding
=
"utf-8"
,
    )
@
lru_cache
def
get_settings
() ->
Settings
:
"""Повертає кешований обʼєкт налаштувань."""
return
Settings
()
app/forprint_prepress_hub/core/presets.py
Python
Run
from
pathlib
import
Path
from
typing
import
Any
import
yaml
def
load_presets
(
presets_dir
:
Path
) ->
list
[
dict
[
str
,
Any
]]:
"""
    Завантажує YAML-пресети з директорії presets.

    На цьому етапі це ще не виконує препрес-операції.
    Зараз задача — перевірити, що система бачить технологічні карти.
    """
if
not
presets_dir
.
exists():
return
[]
presets
:
list
[
dict
[
str
,
Any
]]
=
[]
for
preset_path
in
sorted
(
presets_dir
.
glob(
"*.yaml"
)):
with
preset_path
.
open(
"r"
,
encoding
=
"utf-8"
)
as
file
:
preset_data
=
yaml
.
safe_load(
file
)
or
{}
preset_data
[
"_file"
]
=
preset_path
.
name
presets
.
append(
preset_data
)
return
presets
presets/pdf_basic_check.yaml
YAML
name: pdf_basic_check
title:
"PDF: базова перевірка файлу"
description:
"Перший тестовий пресет. Поки не запускає Acrobat, а тільки фіксує майбутню структуру."
input:
  extensions:
    -
".pdf"
steps:
  - type: internal_check
    name: check_file_exists

  - type: internal_check
    name: check_extension_pdf

output:
  folder:
"data/ready"
filename_template:
"{original_stem}_CHECKED.pdf"
on_error:
  move_to:
"data/error"
write_report: true
tests/test_health.py
Python
Run
from
fastapi
.
testclient
import
TestClient
from
forprint_prepress_hub
.
main
import
app
def
test_health_endpoint_returns_ok
() ->
None
:
client
=
TestClient
(
app
)
response
=
client
.
get(
"/health"
)
assert
response
.
status_code
==
200
assert
response
.
json()[
"status"
]
==
"ok"
assert
response
.
json()[
"service"
]
==
"ForPrint Prepress Hub"
tests/test_presets.py
Python
Run
from
pathlib
import
Path
from
forprint_prepress_hub
.
core
.
presets
import
load_presets
def
test_load_presets_reads_yaml_files
(
tmp_path
:
Path
) ->
None
:
preset_file
=
tmp_path
/
"sample.yaml"
preset_file
.
write_text(
"""
name: sample_preset
title: "Sample preset"
input:
  extensions:
    - ".pdf"
steps:
  - type: internal_check
    name: check_file_exists
"""
,
encoding
=
"utf-8"
,
    )
presets
=
load_presets
(
tmp_path
)
assert
len
(
presets
)
==
1
assert
presets
[
0
][
"name"
]
==
"sample_preset"
assert
presets
[
0
][
"_file"
]
==
"sample.yaml"
def
test_load_presets_returns_empty_list_when_dir_missing
(
tmp_path
:
Path
) ->
None
:
missing_dir
=
tmp_path
/
"missing"
presets
=
load_presets
(
missing_dir
)
assert
presets
==
[]
.gitignore
gitignore
.venv*/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
*.egg-info/

.env
logs/*.log
logs/*.jsonl

data/incoming/*
data/processing/*
data/ready/*
data/error/*

!data/incoming/.gitkeep
!data/processing/.gitkeep
!data/ready/.gitkeep
!data/error/.gitkeep
Щоб Git бачив порожні директорії:
Bash
touch
data/incoming/.gitkeep
touch
data/processing/.gitkeep
touch
data/ready/.gitkeep
touch
data/error/.gitkeep
Перевірка
Після створення файлів:
Bash
source
.venv_prepress_hub/bin/activate
make
install
make
check
Очікувано має бути приблизно так:
ruff check app tests
All checks passed!

pytest -q
... [100%]
Потім запуск:
Bash
make
run
В іншому терміналі:
Bash
make
health
curl
http://127.0.0.1:8020/presets
Що вважати завершенням першого кроку
Перший крок завершений, якщо:
Bash
make
check
проходить без помилок,
/health
повертає
status: ok
, а
/presets
бачить
pdf_basic_check.yaml
.
Після цього наступним кроком я б додала вже
Job Runner v1
: прийняти шлях до PDF, скопіювати оригінал у
data/processing/job_xxx/
, не чіпати оригінал, виконати internal steps і записати
logs/jobs.jsonl
.
