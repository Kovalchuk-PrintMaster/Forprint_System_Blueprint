# Публікація чекпойнту й включення в assistant-context-pack

## До staging

1. Запустити лише `install_module_review_checkpoint_v0_1.py --mode preview`, перевірити exact write set і bootstrap target SHA.
2. `--mode apply` копіює тільки нові файли з `PROJECT_FILES/`; **жодної зміни інших робіт**.
3. `--mode apply --enable-context-hook` — **окремий opt-in** на додавання одного navigation pointer до `coordination/bootstrap/assistant_context_system_specs_v0_1.yaml`. Дозволено лише при точному SHA з базового знімка, якщо target не dirty і не symlink. Якщо target drift — HOLD, без автоматичного merge.
4. Виконати проєктну перевірку `scripts/coordination/module_analysis/module_review_checkpoint_check_v0_1.py` та `git diff --check` (з увагою: foreign diff може бути unrelated).
5. Запустити `make assistant-context-pack MODULE=forprint_system_blueprint` лише після перевірки live Makefile. Перевірити реальний ZIP скриптом `python -B scripts/coordination/module_analysis/verify_assistant_context_visibility_v0_1.py --archive <generated.zip>`. Якщо `VERDICT=NAVIGATION_ONLY_NEEDS_EXPLICIT_READ` — шлях видно, але повне вбудування guide/checkpoint ще `HOLD`, дати новій помічниці точні repo paths; не заявляти full auto-loading.
6. Звірити `git status --short`; staging тільки конкретних **нових** файлів плюс один погоджений bootstrap pointer. Не зачіпати `AGENTS.md`, `Makefile`, CF-10/OC-01 і незавершену `portfolio_rebuild_candidates/` роботу.
7. Після staged diff review, ownership confirmation, owner decision і tests можна створити **окремий документальний commit**, push тільки за дозволом. Після push перевірити remote containment.

## Приклад безпечного staging (виконувати лише після review)

`git add -- coordination/bootstrap/module_deep_review_context_addendum_v0_1.yaml coordination/repository_knowledge/module_knowledge_stabilization/field_guides/2026-10-16__deep_module_roadmap_review_pilot_v0_1.md coordination/repository_knowledge/module_knowledge_stabilization/field_guides/2026-10-16__analysis_stop_and_owner_review_gates_v0_1.yaml coordination/repository_knowledge/module_roadmap_review_pilots/telegram_bot/2026-10-16_D01 scripts/coordination/module_analysis/module_review_checkpoint_check_v0_1.py scripts/coordination/module_analysis/module_analysis_boundary_probe_v0_1.py scripts/coordination/module_analysis/verify_assistant_context_visibility_v0_1.py tests/coordination/module_analysis/test_module_review_checkpoint_check_v0_1.py`

**Bootstrap specs** — окремий `git add -- coordination/bootstrap/assistant_context_system_specs_v0_1.yaml` тільки після успішного hash/ownership gate.

## Чому не комітимо великі ZIP/PDF в автоматичному режимі

Оригінальні архіви й друковане D01 збережені як `REFERENCE_COPIES/` **лише в операторському пакеті**. Перед project archive upload потрібно окремо визначити довготривалий storage, privacy та repository/artifact policy. В Git залишаємо змістовні витяги, метадані й точні SHA256.
