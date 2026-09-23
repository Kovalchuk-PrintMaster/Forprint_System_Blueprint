# Evidence Portfolio — Operational Registry module history

- Source SHA-256: `76cc1ad66510dfee633b2fc0bfa79bdf5734f31c23380babaef4ba6204720f07`
- Evidence records: **32**
- Attachment-only gaps: **35**
- Authority class: **Operational Registry module history / non-Blueprint authority**

> Historical evidence only. Current repositories are not audited.

## EV-OPREG2905-0001 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_design, module_role

> tional_registry , не ревізія існуючого. Орієнтир із вкладення: модуль має стати канонічним джерелом операційної правди по клієнтах, замовленнях, задачах, статусах і операційній історії , але не забирати на себе CRM, бухгалтерію, Library, Gateway, Calculator, Prepress, Warehouse чи Logistics. Pasted text Bootstrap Implementation Plan для v0.1 1. Рекомендований перший крок Почати з малого bootstrap-скелета в директорії: /srv/software_development/forprint-project/forprint_operational_registry Перший коміт має лише довести: Operational Registry exists. It owns operational tru

**Cue:** Operational Registry is framed as canonical operational truth for clients/orders/tasks/status/history.

---

## EV-OPREG2905-0002 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_boundary, module_scope

> правди по клієнтах, замовленнях, задачах, статусах і операційній історії , але не забирати на себе CRM, бухгалтерію, Library, Gateway, Calculator, Prepress, Warehouse чи Logistics. Pasted text Bootstrap Implementation Plan для v0.1 1. Рекомендований перший крок Почати з малого bootstrap-скелета в директорії: /srv/software_development/forprint-project/forprint_operational_registry Перший коміт має лише довести: Operational Registry exists. It owns operational truth. It does not absorb other modules. Коміт: Bootstrap Operational Registry skeleton 2. Що саме

**Cue:** Bootstrap explicitly excludes CRM, Accounting, Library, Gateway, Calculator, Prepress, Warehouse and Logistics ownership.

---

## EV-OPREG2905-0003 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_plan, bootstrap

> ecord OperationalTask OperationalStatus OperationalEvent Я б зробила їх поки на pydantic , не SQLModel. Причина: v0.1 має перевірити межі, життєвий цикл і структуру, а не будувати базу даних. 4. Storage choice Рекомендую для першого кроку: in-memory repository + clear storage interface Тобто: storage/memory.py storage/schema.py Цього достатньо, щоб перевірити створення клієнта, замовлення, задачі, події і простий lifecycle. SQLModel/SQLite можна додати пізніше, коли Blueprint підтвердить, що модель стабільна. 5. Lifecycle v0.1 Додати дуже про

**Cue:** v0.1 should validate models/boundaries/lifecycle before production database architecture.

---

## EV-OPREG2905-0004 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_plan, storage

> туру, а не будувати базу даних. 4. Storage choice Рекомендую для першого кроку: in-memory repository + clear storage interface Тобто: storage/memory.py storage/schema.py Цього достатньо, щоб перевірити створення клієнта, замовлення, задачі, події і простий lifecycle. SQLModel/SQLite можна додати пізніше, коли Blueprint підтвердить, що модель стабільна. 5. Lifecycle v0.1 Додати дуже простий allowed transition map, наприклад: new -> needs_review needs_review -> quote_pending quote_pending -> quote_accepted quote_accepted -> waiting_payment waiting_payment

**Cue:** First storage step is in-memory behind a clear storage interface.

---

## EV-OPREG2905-0005 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_plan, lifecycle

> ільна. 5. Lifecycle v0.1 Додати дуже простий allowed transition map, наприклад: new -> needs_review needs_review -> quote_pending quote_pending -> quote_accepted quote_accepted -> waiting_payment waiting_payment -> paid paid -> in_prepress in_prepress -> ready_for_production ready_for_production -> in_production in_production -> ready_for_pickup ready_for_pickup -> completed І окремо дозволити: any active status -> blocked blocked -> needs_review any active status -> cancelled Тести мають перевірити: valid transition passes invalid transition raises err

**Cue:** Bootstrap defines an initial order-lifecycle transition map plus blocked/cancelled paths.

---

## EV-OPREG2905-0006 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_design, domain_ownership

> ати: Operational Registry owns operational truth. CRM coordinates and displays. Accounting owns accounting/1C truth. Library owns catalogs/contracts. Gateway routes runtime commands later. Calculator calculates. Prepress processes files. 7. Тести з першого коміту Мінімальний набір: test_manifest.py test_boundaries.py test_client_model.py test_order_model.py test_task_model.py test_status_model.py test_order_lifecycle.py test_check_report.py Тести мають ловити головну небезпеку: щоб модуль не почав випадково володіти invoice/payment/catalog/prepress/file/warehouse/gatew

**Cue:** Boundary documents explicitly separate operational truth, CRM coordination, accounting/1C truth, Library contracts, Gateway routing, Calculator and Prepress.

---

## EV-OPREG2905-0007 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_rule, boundary_tests

> t_order_lifecycle.py test_check_report.py Тести мають ловити головну небезпеку: щоб модуль не почав випадково володіти invoice/payment/catalog/prepress/file/warehouse/gateway-логікою. 8. Check-report Додаємо: scripts/run_operational_registry_checks.py Він має запускати: ruff check pytest manifest boundary validation required docs validation status config validation І створювати: reports/operational_registry_check_report.json reports/operational_registry_check_report.md reports/ треба додати в .gitignore . 9. Makefile targets Мінімально: install test lint check check-report format

**Cue:** Tests must catch accidental ownership creep into invoice/payment/catalog/prepress/file/warehouse/gateway logic.

---

## EV-OPREG2905-0008 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_boundary, bootstrap_scope

> print_operational_registry/* scripts/run_operational_registry_checks.py tests/* Без API, без БД-продакшн-рівня, без інтеграцій. 3. Моделі, які можна додати першими Мінімально: ClientRecord OrderRecord OperationalTask OperationalStatus OperationalEvent Я б зробила їх поки на pydantic , не SQLModel. Причина: v0.1 має перевірити межі, життєвий цикл і структуру, а не будувати базу даних. 4. Storage choice Рекомендую для першого кроку: in-memory repository + clear storage interface Тобто: storage/memory.py storage/schema.py Цього достатньо, щоб п

**Cue:** v0.1 explicitly avoids API, production DB migrations, real integrations and other premature runtime complexity.

---

## EV-OPREG2905-0009 — turn 2
**Speaker:** assistant  
**Evidence role:** assistant_open_question, accounting_boundary

> _pending -> quote_accepted quote_accepted -> waiting_payment waiting_payment -> paid paid -> in_prepress in_prepress -> ready_for_production ready_for_production -> in_production in_production -> ready_for_pickup ready_for_pickup -> completed І окремо дозволити: any active status -> blocked blocked -> needs_review any active status -> cancelled Тести мають перевірити: valid transition passes invalid transition raises error 6. Обовʼязкові boundary-документи Створити: docs/architecture/operational_registry_boundaries.md docs/architecture/op

**Cue:** Open question: operational payment status should not be confused with accounting truth.

---

## EV-OPREG2905-0010 — turn 67
**Speaker:** user  
**Evidence role:** execution_evidence, data_foundation

> |data_history|one_c_adapter|entity_card" -rw-r--r-- 1 root root 678 Jun 8 21:08 data_foundation_strategy.md -rw-r--r-- 1 root root 327 Jun 8 21:10 data_history_versioning_policy.md -rw-r--r-- 1 root root 380 Jun 8 21:11 entity_card_design_policy.md -rw-r--r-- 1 root root 400 Jun 8 21:09 event_log_policy.md -rw-r--r-- 1 root root 449 Jun 8 21:09 external_reference_policy.md -rw-r--r-- 1 root root 432 Jun 8 21:08 master_data_policy.md -rw-r--r-- 1 root root 484 Jun 8 21:10 one_c_adapter_boundary_policy.md -rw-r--r-- 1 root root 439 Jun 8 21:08 operational_fact_po

**Cue:** Historical repository contains a named set of data-foundation and policy docs.

---

## EV-OPREG2905-0011 — turn 67
**Speaker:** user  
**Evidence role:** execution_evidence, data_foundation

> Jun 8 21:09 external_reference_policy.md -rw-r--r-- 1 root root 432 Jun 8 21:08 master_data_policy.md -rw-r--r-- 1 root root 484 Jun 8 21:10 one_c_adapter_boundary_policy.md -rw-r--r-- 1 root root 439 Jun 8 21:08 operational_fact_policy.md -rw-r--r-- 1 root root 286 Jun 8 21:10 raw_normalized_value_policy.md -rw-r--r-- 1 root root 564 Jun 8 21:09 reporting_projection_policy.md root@s01:/srv/software_development/forprint-project/forprint_operational_registry# Show more Show less

**Cue:** Historical policy surface includes master data, operational facts, event log and reporting projection docs.

---

## EV-OPREG2905-0012 — turn 67
**Speaker:** user  
**Evidence role:** execution_evidence, accounting_boundary

> ot 432 Jun 8 21:08 master_data_policy.md -rw-r--r-- 1 root root 484 Jun 8 21:10 one_c_adapter_boundary_policy.md -rw-r--r-- 1 root root 439 Jun 8 21:08 operational_fact_policy.md -rw-r--r-- 1 root root 286 Jun 8 21:10 raw_normalized_value_policy.md -rw-r--r-- 1 root root 564 Jun 8 21:09 reporting_projection_policy.md root@s01:/srv/software_development/forprint-project/forprint_operational_registry# Show more Show less

**Cue:** Historical docs include explicit 1C adapter boundary policy.

---

## EV-OPREG2905-0013 — turn 103
**Speaker:** user  
**Evidence role:** owner_instruction, blueprint_governance

> інструкції /srv/software_development/forprint-project/forprint_system_blueprint/coordination/checkup /srv/software_development/forprint-project/forprint_system_blueprint/coordination/directives /srv/software_development/forprint-project/forprint_system_blueprint/coordination/global_policy /srv/software_development/forprint-project/forprint_system_blueprint/coordination/module_policy/forprint_operational_registry Show more Show less

**Cue:** Owner asks to inspect additional Blueprint governance directories for useful instructions.

---

## EV-OPREG2905-0014 — turn 103
**Speaker:** user  
**Evidence role:** owner_instruction, blueprint_governance

> bal_policy /srv/software_development/forprint-project/forprint_system_blueprint/coordination/module_policy/forprint_operational_registry Show more Show less

**Cue:** Owner points specifically to Operational Registry module policy in Blueprint.

---

## EV-OPREG2905-0015 — turn 119
**Speaker:** user  
**Evidence role:** owner_relay, idempotency

> від blueprint ще раз уточнення невелике додати в наступний промт вимогу зробити sync snapshots і completion automation ідемпотентними, щоб повторна перевірка не створювала зайвий git diff тільки через timestamp. прибрати timestamp-only churn

**Cue:** Blueprint clarification requires snapshot/completion automation to avoid timestamp-only churn.

---

## EV-OPREG2905-0016 — turn 149
**Speaker:** user  
**Evidence role:** owner_correction, prompt_path

> oordination/prompts/active поставив BLUEPRINT_PROMPTS_ROOT ?= $(BLUEPRINT_ROOT)/coordination/outgoing_prompts ACTIVE_PROMPT_LOCAL_DIR ?= coordination/outgoing_prompts/approved даю про всяк випадок структуру blueprint щоб ти точно знала де лежить потрібна нам інформація coordination/ ├── checkup │ ├── ecosystem_checkup_policy.yaml │ ├── module_activity_thresholds.yaml │ └── README.md ├── directives │ ├── global │ │ ├── active │ │ │ └── 2026-06-02__global__directive__module-coordination-standard-v1.md │ │ └── index.yaml │ ├── modules │ │ └── calculator_engine │ │ ├

**Cue:** Owner corrects the Blueprint outgoing prompt path based on actual structure.

---

## EV-OPREG2905-0017 — turn 149
**Speaker:** user  
**Evidence role:** owner_correction, prompt_path

> Pasted text.txt Document замість цьго BLUEPRINT_PROMPTS_ROOT ?= $(BLUEPRINT_ROOT)/coordination/prompts ACTIVE_PROMPT_LOCAL_DIR ?= coordination/prompts/active поставив BLUEPRINT_PROMPTS_ROOT ?= $(BLUEPRINT_ROOT)/coordination/outgoing_prompts ACTIVE_PROMPT_LOCAL_DIR ?= coordination/outgoing_prompts/approved даю про всяк випадок структуру blueprint щоб ти точно знала де лежить потрібна нам інформація coordination/ ├── checkup │ ├── ecosystem_checkup_policy.yaml │ ├── module_activity_thresholds.yaml │ └── README.md ├── directives │ ├── global │ │ ├── active │ │ │ └── 2026-06-02__global__directive__module-coordination-standard-v1.md │ │ └── index.yaml │ ├── modules │ │ └── calculator_engine │ │ ├

**Cue:** Approved prompt source is module-specific under Blueprint outgoing_prompts.

---

## EV-OPREG2905-0018 — turn 158
**Speaker:** assistant  
**Evidence role:** assistant_artifact, make_surface

> сновний локальний validation gate. # Очікуваний результат: lint OK і pytest OK. check: lint test # Команда: make check-report # Що робить: запускає структурований Operational Registry check-report. # Очікуваний результат: усі module policy, boundary, preview і coordination checks мають статус OK. check-report: $(PYTHON) scripts/run_operational_registry_checks.py # Команда: make status-report # Що робить: експортує поточний module status JSON report. # Очікуваний результат: локально створено reports/operational_registry_module_status.json. status-repo

**Cue:** Regenerated Makefile has a read-only check target separating lint-fix from check.

---

## EV-OPREG2905-0019 — turn 158
**Speaker:** assistant  
**Evidence role:** assistant_artifact, cross_repo

> k-report status-report .PHONY: clean report-clean .PHONY: blueprint-paths-check blueprint-pull blueprint-check blueprint-sync-directives blueprint-sync .PHONY: blueprint-instruction-list blueprint-instruction-check blueprint-instruction-sync .PHONY: blueprint-standards-list blueprint-standards-check blueprint-standards-sync .PHONY: blueprint-prompts-list blueprint-prompts-sync blueprint-prompts-check blueprint-prompts prompt-read .PHONY: module-start module-sync module-validate module-finish .PHONY: coordination-check coordination-fix module-policy

**Cue:** Regenerated Makefile includes Blueprint pull as part of module-start workflow.

---

## EV-OPREG2905-0020 — turn 158
**Speaker:** assistant  
**Evidence role:** assistant_artifact, reporting

> .. \) , prompt sync бере тільки forprint_operational_registry/approved/*.md , а report-clean не падає, якщо report-файли не tracked. Pasted text Замінюй весь Makefile : Makefile PYTHON ?= .venv_operational_registry/bin/python PIP ?= .venv_operational_registry/bin/pip BLUEPRINT_ROOT ?= /srv/software_development/forprint-project/forprint_system_blueprint ACTIVE_PROMPT_MODULE ?= forprint_operational_registry BLUEPRINT_PROMPTS_ROOT ?= $(BLUEPRINT_ROOT)/coordination/outgoing_prompts BLUEPRINT_ACTIVE_PROMPT_SOURCE_DIR ?= $(BLUEPRINT_PROMPTS_ROOT)/$(ACT

**Cue:** Report cleanup is hardened not to fail on absent/untracked report files.

---

## EV-OPREG2905-0021 — turn 160
**Speaker:** assistant  
**Evidence role:** assistant_report, validation

> rrent_status.yaml module-validate теж зелений: check-report OK, Ruff OK, pytest 232 passed , governance-check OK. Pasted text Git status нормальний M Makefile M coordination/instruction_intake/blueprint_instruction_packet.yaml M coordination/standards/blueprint_standards_snapshot.yaml ?? coordination/outgoing_prompts/ Це очікувано: Makefile — наше вирівнювання під Make Command Standard v0.2. blueprint_instruction_packet.yaml і blueprint_standards_snapshot.yaml — очікуване оновлення під Blueprint commit 88db68d . coordination/outgoing_prompts/ —

**Cue:** Makefile alignment validation reports 232 tests passing and governance checks green.

---

## EV-OPREG2905-0022 — turn 160
**Speaker:** assistant  
**Evidence role:** assistant_boundary, completion_packet

> mmand_query_readiness_v0_1 . Важливе уточнення: module-validate зараз перевіряє старий packet local_launch_readiness_v0_1.yaml , бо нового packet-а ще немає. Це нормально для Makefile alignment checkpoint. Для фіналу основної задачі треба буде запускати: Bash make module-finish PACKET = coordination/completion_packets/examples/local_operator_command_query_readiness_v0_1.yaml

**Cue:** Alignment checkpoint still validates the prior local_launch_readiness packet until the new task packet exists.

---

## EV-OPREG2905-0023 — turn 161
**Speaker:** user  
**Evidence role:** execution_evidence, git

> _snapshot.yaml | 4 +- 4 files changed, 661 insertions(+), 39 deletions(-) [main a6ca69f] Align Makefile with make-first workflow 4 files changed, 661 insertions(+), 39 deletions(-) create mode 100644 coordination/outgoing_prompts/approved/2026-06-19__operational_registry__local_operator_command_query_readiness_v0_1.md Enumerating objects: 18, done. Counting objects: 100% (18/18), done. Delta compression using up to 4 threads Compressing objects: 100% (10/10), done. Writing objects: 100% (11/11), 8.96 KiB | 4.48 MiB/s, done. Total 11 (delta 3

**Cue:** User terminal output proves alignment commit on Operational Registry main branch and push to origin/main.

---

## EV-OPREG2905-0024 — turn 162
**Speaker:** assistant  
**Evidence role:** assistant_report, alignment

> re and command-level documentation. 3. Problems discovered during alignment 3.1 Wrong initial outgoing prompt path The first implementation assumed Blueprint outgoing prompts were stored under: coordination/prompts/outgoing/forprint_operational_registry But the actual Blueprint structure is: coordination/outgoing_prompts/forprint_operational_registry/approved/ This caused: No outgoing prompt directory found Resolution: The Makefile was updated to use: BLUEPRINT_PROMPTS_ROOT ?= $(BLUEPRINT_ROOT)/coordination/outgoing_prompts BLUEPRINT_ACTIVE_PROMPT_SOURCE_DIR ?= $(BLUE

**Cue:** Final alignment report identifies and resolves the wrong outgoing-prompt path.

---

## EV-OPREG2905-0025 — turn 162
**Speaker:** assistant  
**Evidence role:** assistant_report, alignment

> ng_prompts/approved This now matches the actual Blueprint directory layout. 3.2 Prompt search was too broad An intermediate version searched the entire Blueprint coordination/outgoing_prompts tree using module-name patterns. This caused the command to list unrelated .gitkeep , draft, sent, and other-module files. Resolution: The prompt workflow was narrowed to the approved prompt directory for this module only: $(BLUEPRINT_ROOT)/coordination/outgoing_prompts/forprint_operational_registry/approved Now blueprint-prompts-list only lists approved markdown prompts f

**Cue:** Final report says broad prompt discovery was narrowed to approved module prompts only.

---

## EV-OPREG2905-0026 — turn 162
**Speaker:** assistant  
**Evidence role:** assistant_report, alignment

> is simpler, safer, and matches the Blueprint prompt protocol more directly. 3.4 Unsafe prompt sync cleanup One intermediate version removed local prompt files before validating that source prompt files existed. When the command later failed, it left the local prompt directory empty, which caused governance validation to fail on: No active prompt files found in coordination/outgoing_prompts/approved Resolution: The final sync logic first verifies that approved Blueprint prompt markdown files exist. Only after that it deletes old local markdown prompt copies and

**Cue:** Final report says prompt sync now verifies source files before deleting local copies.

---

## EV-OPREG2905-0027 — turn 162
**Speaker:** assistant  
**Evidence role:** assistant_report, alignment

> ompt-read blueprint-sync module-start module-sync module-validate module-finish report-clean completion-packet-check The Makefile also needed clearer thematic structure and command-level documentation. 3. Problems discovered during alignment 3.1 Wrong initial outgoing prompt path The first implementation assumed Blueprint outgoing prompts were stored under: coordination/prompts/outgoing/forprint_operational_registry But the actual Blueprint structure is: coordination/outgoing_prompts/forprint_operational_registry/approved/ This caused: No outgoin

**Cue:** Final report says report-clean safely tolerates missing/untracked reports.

---

## EV-OPREG2905-0028 — turn 162
**Speaker:** assistant  
**Evidence role:** assistant_report, make_first

> ю реалізацією local_operator_command_query_readiness_v0_1 . Підтверджені факти: make module-start пройшов, make module-validate пройшов, pytest — 232 passed , git diff --check чистий, commit a6ca69f запушений. Pasted text Готовий звіт для Blueprint: Operational Registry → Blueprint Make-First Workflow Alignment Report Operational Registry → Blueprint Make-First Workflow Alignment Report Module forprint_operational_registry Checkpoint make_first_workflow_alignment_before_local_operator_command_query_readiness_v0_1 Related Blueprint prompt 2026-06-19__o

**Cue:** Final alignment gate requires module-start and module-validate before main prompt implementation.

---

## EV-OPREG2905-0029 — turn 162
**Speaker:** assistant  
**Evidence role:** assistant_report, provenance

> 026-06-19__operational_registry__local_operator_command_query_readiness_v0_1.md Blueprint commit used 88db68d Update Operational Registry readiness prompt for make-first workflow Operational Registry commit a6ca69f Align Makefile with make-first workflow Pushed to: origin/main 1. Why this checkpoint was needed Before starting the main implementation scope: local_operator_command_query_readiness_v0_1 Blueprint required the module to first align with Make Command Standard v0.2 and use a make-first workflow . The explicit rule was: Do not proceed to the main

**Cue:** Alignment report binds local snapshots/prompt workflow to Blueprint commit `88db68d`.

---

## EV-OPREG2905-0030 — turn 162
**Speaker:** assistant  
**Evidence role:** assistant_boundary, scope

> e with make-first workflow Remote updated: origin/main 8. Boundary confirmation This checkpoint did not implement the main business scope yet. It did not add: production API FastAPI app live CRM integration live Telegram integration live Website integration real 1C sync/write production write automatic posting Accounting payment truth CRM dashboard Telegram runtime UI Calculator final price ownership Library catalog ownership Warehouse stock truth Prepress lifecycle ownership This checkpoint only aligned Makefile workflow, Blueprint prompt visibility, Blueprint snapshot sync, and validation com

**Cue:** Make-first alignment is explicitly separated from main operational-command/query implementation scope.

---

## EV-OPREG2905-0031 — turn 162
**Speaker:** assistant  
**Evidence role:** assistant_rule, completion_packet

> ts for local/offline validation Finalization for the main prompt must use: make module-finish PACKET=coordination/completion_packets/examples/local_operator_command_query_readiness_v0_1.yaml and the local completion packet automation must generate/update the final completion report. Короткий службовий вступ для Blueprint перед цим звітом: Operational Registry reports completion of the required Make Command Standard v0.2 / make-first workflow alignment gate before starting local_operator_command_query_readiness_v0_1. The module-start and module-validate w

**Cue:** Main prompt finalization must use explicit completion-packet identity.

---

## EV-OPREG2905-0032 — turn 162
**Speaker:** assistant  
**Evidence role:** assistant_report, git

> onal Registry commit a6ca69f Align Makefile with make-first workflow Pushed to: origin/main 1. Why this checkpoint was needed Before starting the main implementation scope: local_operator_command_query_readiness_v0_1 Blueprint required the module to first align with Make Command Standard v0.2 and use a make-first workflow . The explicit rule was: Do not proceed to the main local operator command/query readiness task until: make module-start make module-validate both work successfully. Therefore, this checkpoint was handled as a separate pre-impl

**Cue:** Alignment checkpoint is reported committed/pushed separately before main prompt implementation.

---
