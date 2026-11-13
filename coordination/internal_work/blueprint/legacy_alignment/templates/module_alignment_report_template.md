# Module Alignment Report

report_id: YYYY-MM-DD-<module_id>-alignment-report
module_id: <module_id>
source_prompt_id: <prompt_id>
report_status: new
created_at: YYYY-MM-DD
prepared_by: module_assistant
target_blueprint_version: 0.7.0
1. Current state

Коротко опиши поточний стан модуля:

що вже реалізовано;
що тільки заплановано;
що є експериментальним;
які частини ще не стабільні.
2. Current architectural role

Опиши, яку роль модуль фактично зараз виконує.

Важливо окремо вказати:

Чи збігається фактична роль з роллю, описаною у ForPrint System Blueprint?
3. Data currently owned by this module

Перелік даних/сутностей, які модуль зараз фактично зберігає або вважає своїми.

Формат:

- object_name:
  - current_storage: ...
  - canonical_owner_claimed: yes/no/unclear
  - should_remain_here: yes/no/needs_review
4. Data consumed from other modules

Перелік даних, які модуль має отримувати або вже отримує з інших модулів.

Формат:

- object_name:
  - expected_source_module: ...
  - current_source: ...
  - contract_exists: yes/no/unknown
5. Data provided to other modules

Перелік даних/результатів, які модуль має віддавати іншим.

Формат:

- object_name:
  - target_modules: [...]
  - current_format: ...
  - contract_exists: yes/no/unknown
6. Detected architecture drift

Перелік місць, де модуль може відхилятися від Blueprint.

Формат:

- drift_id: short_name
  severity: low/medium/high
  description: ...
  suggested_action: ...
7. Contract gaps

Перелік контрактів, яких не вистачає.

Формат:

- needed_contract: module_a_to_module_b_object.v1
  producer: ...
  consumer: ...
  data_objects: [...]
  priority: low/medium/high
8. Safe next corrections

Список невеликих безпечних кроків, які можна зробити без великого рефакторингу.

1. ...
2. ...
3. ...
9. Actions that require Blueprint decision

Список питань, які модуль не має вирішувати самостійно.

1. ...
2. ...
3. ...
10. Open questions for ForPrint System Blueprint

Питання до архітектурного шару.

1. ...
2. ...
3. ...
11. Recommended module priority

Оціни, як рухати модуль далі:

recommended_priority: active_support / high_next / medium / later / pause
reason: ...
12. Summary

Короткий підсумок:

- module_direction_is_correct: yes/no/partially
- urgent_architecture_drift: yes/no
- safe_to_continue_current_development: yes/no/with_corrections
- blueprint_update_needed: yes/no