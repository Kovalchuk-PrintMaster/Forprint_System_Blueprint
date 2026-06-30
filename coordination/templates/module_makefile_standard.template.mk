# ForPrint Module Makefile Standard Template
#
# Purpose:
#   Provide a shared Makefile structure for ForPrint modules.
#
# Usage:
#   Copy this file to a module Makefile and adapt MODULE_ID, MODULE_NAME,
#   PYTHON, path variables, and module-specific targets.
#
# Rule:
#   Keep block names and public target names stable across modules.
#   Implementation may differ per module.

.DEFAULT_GOAL := help

# =============================================================================
# 00 Environment / constants START
# =============================================================================

# Purpose: define shared module constants and local runtime paths.
# Result: all targets can use stable variables and optional colored output.
MODULE_ID ?= forprint_module
MODULE_NAME ?= ForPrint Module
PYTHON ?= python
BLUEPRINT_ROOT ?= /srv/software_development/forprint-project/forprint_system_blueprint
BLUEPRINT_PYTHON ?= $(BLUEPRINT_ROOT)/.venv_blueprint/bin/python
BLUEPRINT_PROMPT_QUEUE_VALIDATOR ?= $(BLUEPRINT_ROOT)/scripts/coordination/validate_prompt_queue.py
BLUEPRINT_PROMPT_DASHBOARD_RENDERER ?= $(BLUEPRINT_ROOT)/scripts/coordination/render_prompt_dashboard.py
BLUEPRINT_NEXT_PROMPT_RESOLVER ?= $(BLUEPRINT_ROOT)/scripts/coordination/resolve_next_prompt.py
BLUEPRINT_DOCUMENT_MANIFEST_BUILDER ?= $(BLUEPRINT_ROOT)/scripts/coordination/build_document_manifest.py
BLUEPRINT_DOCUMENT_AWARENESS_DASHBOARD ?= $(BLUEPRINT_ROOT)/scripts/coordination/render_document_awareness_dashboard.py
BLUEPRINT_CONTEXT_BUNDLE_BUILDER ?= $(BLUEPRINT_ROOT)/scripts/coordination/build_context_bundle.py

SCOPE ?= bootstrap
LIMIT ?= 40

REPORTS_DIR ?= reports
COORDINATION_DIR ?= coordination
MODULE_DOCUMENT_AWARENESS_LEDGER ?= $(CURDIR)/$(COORDINATION_DIR)/blueprint_awareness/document_review_ledger.yaml
PROMPTS_DIR ?= $(COORDINATION_DIR)/prompts
LOCAL_PROMPTS_DIR ?= $(PROMPTS_DIR)/received
BLUEPRINT_PROMPTS_ROOT ?= $(BLUEPRINT_ROOT)/coordination/outgoing_prompts
BLUEPRINT_MODULE_PROMPTS_DIR ?= $(BLUEPRINT_PROMPTS_ROOT)/$(MODULE_ID)
ACTIVE_PROMPT_DIR ?= $(BLUEPRINT_MODULE_PROMPTS_DIR)/approved

COLOR_RESET ?= \033[0m
COLOR_BOLD ?= \033[1m
COLOR_GREEN ?= \033[32m
COLOR_YELLOW ?= \033[33m
COLOR_BLUE ?= \033[34m
COLOR_CYAN ?= \033[36m
COLOR_RED ?= \033[31m

ifeq ($(NO_COLOR),1)
COLOR_RESET :=
COLOR_BOLD :=
COLOR_GREEN :=
COLOR_YELLOW :=
COLOR_BLUE :=
COLOR_CYAN :=
COLOR_RED :=
endif

# =============================================================================
# 00 Environment / constants FINISH
# =============================================================================


# =============================================================================
# 01 Help / navigation START
# =============================================================================

# Purpose: list available public targets for quick operator navigation.
# Result: prints a concise list of standard module commands.
.PHONY: help
help:
	@echo "$(COLOR_BOLD)$(MODULE_NAME) Make targets$(COLOR_RESET)"
	@echo ""
	@echo "Core:"
	@echo "  make install"
	@echo "  make lint"
	@echo "  make lint-fix"
	@echo "  make test"
	@echo "  make check"
	@echo "  make check-report"
	@echo "  make status-report"
	@echo ""
	@echo "Blueprint:"
	@echo "  make blueprint-sync"
	@echo "  make blueprint-instruction"
	@echo "  make blueprint-standards"
	@echo "  make blueprint-prompts"
	@echo "  make prompt-read"
	@echo ""
	@echo "  make prompt-queue-validate"
	@echo "  make prompt-dashboard"
	@echo "  make prompt-next"
	@echo "  make prompt-read-next"
	@echo ""
	@echo "  Blueprint document awareness:"
	@echo "  make document-manifest"
	@echo "  make document-awareness"
	@echo "  make context-bundle"
	@echo "  make context-bundle-print"
	@echo ""
	@echo "Workflow:"
	@echo "  make module-start"
	@echo "  make module-sync"
	@echo "  make module-validate"
	@echo "  make module-finish PACKET=coordination/completion_packets/examples/<packet>.yaml"

# =============================================================================
# 01 Help / navigation FINISH
# =============================================================================


# =============================================================================
# 02 Install / bootstrap START
# =============================================================================

# Purpose: install or verify development dependencies.
# Result: local environment is ready for checks.
.PHONY: install
install:
	@echo "$(COLOR_YELLOW)DEFERRED: implement module-specific install workflow.$(COLOR_RESET)"

# =============================================================================
# 02 Install / bootstrap FINISH
# =============================================================================


# =============================================================================
# 03 Project lifecycle START
# =============================================================================

# Purpose: start local project runtime if the module has one.
# Result: local service starts or clearly reports deferral.
.PHONY: start
start:
	@echo "$(COLOR_YELLOW)DEFERRED: no local runtime start target is defined for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: stop local project runtime if the module has one.
# Result: local service stops or clearly reports deferral.
.PHONY: stop
stop:
	@echo "$(COLOR_YELLOW)DEFERRED: no local runtime stop target is defined for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: restart local project runtime if the module has one.
# Result: local service restarts through stop/start.
.PHONY: restart
restart:
	$(MAKE) stop
	$(MAKE) start

# =============================================================================
# 03 Project lifecycle FINISH
# =============================================================================


# =============================================================================
# 04 Local runtime services START
# =============================================================================

# Purpose: run local development services required by the module.
# Result: local service stack starts or clearly reports deferral.
.PHONY: services-start
services-start:
	@echo "$(COLOR_YELLOW)DEFERRED: no local services are defined for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: stop local development services required by the module.
# Result: local service stack stops or clearly reports deferral.
.PHONY: services-stop
services-stop:
	@echo "$(COLOR_YELLOW)DEFERRED: no local services are defined for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 04 Local runtime services FINISH
# =============================================================================


# =============================================================================
# 05 Monitors / workers / background services START
# =============================================================================

# Purpose: start local monitors, workers, queue consumers, or watchers.
# Result: background helpers start or clearly report deferral.
.PHONY: monitors-start
monitors-start:
	@echo "$(COLOR_YELLOW)DEFERRED: no monitors are defined for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: stop local monitors, workers, queue consumers, or watchers.
# Result: background helpers stop or clearly report deferral.
.PHONY: monitors-stop
monitors-stop:
	@echo "$(COLOR_YELLOW)DEFERRED: no monitors are defined for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 05 Monitors / workers / background services FINISH
# =============================================================================


# =============================================================================
# 06 Syntax / formatting / lint START
# =============================================================================

# Purpose: run configured linter without modifying files.
# Result: returns non-zero if style or syntax checks fail.
.PHONY: lint
lint:
	$(PYTHON) -m ruff check app scripts tests

# Purpose: run safe automatic lint fixes.
# Result: fixable lint issues are corrected.
.PHONY: lint-fix
lint-fix:
	$(PYTHON) -m ruff check app scripts tests --fix

# =============================================================================
# 06 Syntax / formatting / lint FINISH
# =============================================================================


# =============================================================================
# 07 Tests START
# =============================================================================

# Purpose: run the module test suite.
# Result: all tests pass or target returns non-zero.
.PHONY: test
test:
	$(PYTHON) -m pytest -q

# =============================================================================
# 07 Tests FINISH
# =============================================================================


# =============================================================================
# 08 Validation / check reports START
# =============================================================================

# Purpose: run the main local validation flow before commit.
# Result: lint, tests, and module validations pass.
.PHONY: check
check:
	$(MAKE) lint-fix
	$(MAKE) lint
	$(MAKE) test

# Purpose: run module checks and generate human/machine reports.
# Result: check report is created under reports/ or target fails.
.PHONY: check-report
check-report:
	@echo "$(COLOR_BOLD)== $(MODULE_NAME) check report ==$(COLOR_RESET)"
	@mkdir -p "$(REPORTS_DIR)"
	@echo "$(COLOR_YELLOW)DEFERRED: implement module-specific check report generator.$(COLOR_RESET)"

# =============================================================================
# 08 Validation / check reports FINISH
# =============================================================================


# =============================================================================
# 09 Status / generated reports / cleanup START
# =============================================================================

# Purpose: show or export concise module status without full validation.
# Result: current coordination status is printed or stale status is reported.
.PHONY: status-report
status-report:
	@echo "$(COLOR_BOLD)== $(MODULE_NAME) status ==$(COLOR_RESET)"
	@test -f "$(COORDINATION_DIR)/status/current_status.yaml" || \
		(echo "$(COLOR_RED)Missing coordination/status/current_status.yaml$(COLOR_RESET)"; exit 1)
	@sed -n '1,160p' "$(COORDINATION_DIR)/status/current_status.yaml"

# Purpose: clean or restore generated reports so the working tree remains reviewable.
# Result: ignored runtime reports are removed and tracked generated runtime reports are restored when applicable.
.PHONY: report-clean
report-clean:
	@rm -f "$(REPORTS_DIR)/$(MODULE_ID)_check_report.json" "$(REPORTS_DIR)/$(MODULE_ID)_check_report.md"
	@git restore -- "$(REPORTS_DIR)/$(MODULE_ID)_module_status.json" 2>/dev/null || true
	@echo "$(COLOR_GREEN)Report cleanup completed.$(COLOR_RESET)"

# =============================================================================
# 09 Status / generated reports / cleanup FINISH
# =============================================================================


# =============================================================================
# 10 Blueprint integration START
# =============================================================================

# Purpose: update the local ForPrint System Blueprint repository.
# Result: Blueprint repo is pulled using ff-only.
.PHONY: blueprint-pull
blueprint-pull:
	git -C "$(BLUEPRINT_ROOT)" pull --ff-only

# Purpose: verify that required Blueprint paths are readable.
# Result: required Blueprint directories and indexes exist.
.PHONY: blueprint-check
blueprint-check:
	@test -d "$(BLUEPRINT_ROOT)/coordination/global_policy"
	@test -d "$(BLUEPRINT_ROOT)/coordination/standards"
	@test -f "$(BLUEPRINT_ROOT)/coordination/module_policy/$(MODULE_ID)/module_policy.md"
	@test -f "$(BLUEPRINT_ROOT)/coordination/outgoing_prompts/$(MODULE_ID)/index.yaml"
	@echo "$(COLOR_GREEN)Blueprint paths are readable for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: import active Blueprint directives into local coordination.
# Result: directives sync runs or clearly reports documented deferral.
.PHONY: blueprint-sync-directives
blueprint-sync-directives:
	@echo "$(COLOR_YELLOW)DEFERRED: Blueprint directive sync is not wired for this module yet.$(COLOR_RESET)"

# Purpose: run all Blueprint synchronization needed before work starts.
# Result: Blueprint, directives, instruction intake, standards, and prompts are synchronized.
.PHONY: blueprint-sync
blueprint-sync:
	$(MAKE) blueprint-pull
	$(MAKE) blueprint-check
	$(MAKE) blueprint-sync-directives
	$(MAKE) blueprint-instruction
	$(MAKE) blueprint-standards
	$(MAKE) blueprint-prompts

# =============================================================================
# 10 Blueprint integration FINISH
# =============================================================================


# =============================================================================
# 11 Blueprint instruction intake START
# =============================================================================

# Purpose: list Blueprint instruction intake sources.
# Result: operator can see instruction files relevant to module work.
.PHONY: blueprint-instruction-list
blueprint-instruction-list:
	@find "$(BLUEPRINT_ROOT)/coordination/instruction_intake" -maxdepth 1 -type f | sort

# Purpose: verify Blueprint instruction intake sources.
# Result: required instruction intake files are readable.
.PHONY: blueprint-instruction-check
blueprint-instruction-check:
	@test -f "$(BLUEPRINT_ROOT)/coordination/instruction_intake/assistant_reading_order.md"
	@test -f "$(BLUEPRINT_ROOT)/coordination/instruction_intake/instruction_sources.yaml"
	@test -f "$(BLUEPRINT_ROOT)/coordination/instruction_intake/module_profile_model.md"
	@test -f "$(BLUEPRINT_ROOT)/coordination/instruction_intake/default_profile_traits.yaml"
	@echo "$(COLOR_GREEN)Blueprint instruction intake is readable.$(COLOR_RESET)"

# Purpose: synchronize Blueprint instruction intake snapshot.
# Result: local module instruction packet is refreshed or safely deferred.
.PHONY: blueprint-instruction-sync
blueprint-instruction-sync:
	@echo "$(COLOR_YELLOW)DEFERRED: implement module-specific instruction packet sync.$(COLOR_RESET)"

# Purpose: run complete instruction intake workflow.
# Result: instruction sources are listed, checked, and synchronized.
.PHONY: blueprint-instruction
blueprint-instruction:
	$(MAKE) blueprint-instruction-list
	$(MAKE) blueprint-instruction-check
	$(MAKE) blueprint-instruction-sync

# =============================================================================
# 11 Blueprint instruction intake FINISH
# =============================================================================


# =============================================================================
# 12 Blueprint standards START
# =============================================================================

# Purpose: list Blueprint standards.
# Result: operator can see available standard documents.
.PHONY: blueprint-standards-list
blueprint-standards-list:
	@find "$(BLUEPRINT_ROOT)/coordination/standards" -maxdepth 2 -type f | sort

# Purpose: verify Blueprint standards are readable.
# Result: standards index and standard documents are readable.
.PHONY: blueprint-standards-check
blueprint-standards-check:
	@test -f "$(BLUEPRINT_ROOT)/coordination/standards/index.yaml"
	@test -f "$(BLUEPRINT_ROOT)/coordination/standards/make_command_standard.md"
	@test -d "$(BLUEPRINT_ROOT)/coordination/standards/modular_topology_and_resilience"
	@test -d "$(BLUEPRINT_ROOT)/coordination/standards/third_party_reuse"
	@echo "$(COLOR_GREEN)Blueprint standards are readable.$(COLOR_RESET)"

# Purpose: synchronize Blueprint standards snapshot.
# Result: local module standards snapshot is refreshed or safely deferred.
.PHONY: blueprint-standards-sync
blueprint-standards-sync:
	@echo "$(COLOR_YELLOW)DEFERRED: implement module-specific standards snapshot sync.$(COLOR_RESET)"

# Purpose: run complete standards workflow.
# Result: standards are listed, checked, and synchronized.
.PHONY: blueprint-standards
blueprint-standards:
	$(MAKE) blueprint-standards-list
	$(MAKE) blueprint-standards-check
	$(MAKE) blueprint-standards-sync

# =============================================================================
# 12 Blueprint standards FINISH
# =============================================================================


# =============================================================================
# 13 Blueprint outgoing prompts START
# =============================================================================

# Purpose: list active Blueprint outgoing prompts for this module.
# Result: prompt files approved for module work are printed.
.PHONY: blueprint-prompts-list
blueprint-prompts-list:
	@test -d "$(ACTIVE_PROMPT_DIR)" || \
		(echo "$(COLOR_RED)Missing active prompt directory: $(ACTIVE_PROMPT_DIR)$(COLOR_RESET)"; exit 1)
	@find "$(ACTIVE_PROMPT_DIR)" -maxdepth 1 -type f -name "*.md" | sort

# Purpose: verify active Blueprint outgoing prompts are readable.
# Result: at least one approved prompt markdown file exists.
.PHONY: blueprint-prompts-check
blueprint-prompts-check:
	@test -d "$(ACTIVE_PROMPT_DIR)"
	@test -n "$$(find "$(ACTIVE_PROMPT_DIR)" -maxdepth 1 -type f -name '*.md' -print -quit)"
	@echo "$(COLOR_GREEN)Blueprint outgoing prompts are readable for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: synchronize active Blueprint outgoing prompts into the module-local coordination area.
# Result: approved prompt files are copied into coordination/prompts/received.
.PHONY: blueprint-prompts-sync
blueprint-prompts-sync:
	@mkdir -p "$(LOCAL_PROMPTS_DIR)"
	@test -n "$$(find "$(ACTIVE_PROMPT_DIR)" -maxdepth 1 -type f -name '*.md' -print -quit)" || \
		(echo "$(COLOR_RED)No active prompt files found in $(ACTIVE_PROMPT_DIR)$(COLOR_RESET)"; exit 1)
	@find "$(LOCAL_PROMPTS_DIR)" -maxdepth 1 -type f -name "*.md" -delete
	@cp "$(ACTIVE_PROMPT_DIR)"/*.md "$(LOCAL_PROMPTS_DIR)/"
	@echo "$(COLOR_GREEN)Blueprint outgoing prompts synced to $(LOCAL_PROMPTS_DIR).$(COLOR_RESET)"

# Purpose: run complete Blueprint outgoing prompt workflow.
# Result: prompts are listed, checked, and synchronized.
.PHONY: blueprint-prompts
blueprint-prompts:
	$(MAKE) blueprint-prompts-list
	$(MAKE) blueprint-prompts-check
	$(MAKE) blueprint-prompts-sync
	$(MAKE) prompt-queue-validate
	$(MAKE) prompt-dashboard

# Purpose: show the active prompt for the module assistant.
# Result: active local synced prompt is printed to console.
.PHONY: prompt-read
prompt-read:
	@test -n "$$(find "$(LOCAL_PROMPTS_DIR)" -maxdepth 1 -type f -name '*.md' -print -quit)" || \
		(echo "$(COLOR_RED)No local prompt found. Run make blueprint-prompts-sync first.$(COLOR_RESET)"; exit 1)
	@sed -n '1,260p' "$$(find "$(LOCAL_PROMPTS_DIR)" -maxdepth 1 -type f -name '*.md' | sort | head -n 1)"

# Purpose: validate Blueprint Prompt Queue v0.2 indexes.
# Result: prompt queue indexes are valid or legacy indexes are clearly skipped.
.PHONY: prompt-queue-validate
prompt-queue-validate:
		@if [ -x "$(BLUEPRINT_PYTHON)" ] && [ -f "$(BLUEPRINT_PROMPT_QUEUE_VALIDATOR)" ]; then \
				"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_PROMPT_QUEUE_VALIDATOR)" --root "$(BLUEPRINT_ROOT)"; \
		else \
				echo "$(COLOR_YELLOW)DEFERRED: Blueprint Prompt Queue validator is not available yet.$(COLOR_RESET)"; \
		fi

# Purpose: render the Blueprint prompt queue dashboard for this module.
# Result: operator can see prompt order, execution state, Blueprint review state and next prompt.
.PHONY: prompt-dashboard
prompt-dashboard:
		@if [ -x "$(BLUEPRINT_PYTHON)" ] && [ -f "$(BLUEPRINT_PROMPT_DASHBOARD_RENDERER)" ]; then \
				if [ "$(NO_COLOR)" = "1" ]; then \
						"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_PROMPT_DASHBOARD_RENDERER)" --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --no-color; \
				else \
						"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_PROMPT_DASHBOARD_RENDERER)" --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)"; \
				fi; \
		else \
				echo "$(COLOR_YELLOW)DEFERRED: Blueprint Prompt Queue dashboard renderer is not available yet.$(COLOR_RESET)"; \
		fi

# Purpose: resolve the next ready Blueprint prompt for this module.
# Result: prints the next prompt metadata and path or fails if the module is not migrated/has no ready prompt.
.PHONY: prompt-next
prompt-next:
		"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_NEXT_PROMPT_RESOLVER)" --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)"

# Purpose: read the next ready Blueprint prompt for this module.
# Result: prints next prompt metadata and prompt file content.
.PHONY: prompt-read-next
prompt-read-next:
		"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_NEXT_PROMPT_RESOLVER)" --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --read

# Purpose: build and validate the Blueprint coordination document manifest without writing reports.
# Result: document manifest summary is printed or deferral is reported.
.PHONY: document-manifest
document-manifest:
		@if [ -x "$(BLUEPRINT_PYTHON)" ] && [ -f "$(BLUEPRINT_DOCUMENT_MANIFEST_BUILDER)" ]; then \
				"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_DOCUMENT_MANIFEST_BUILDER)" --root "$(BLUEPRINT_ROOT)" --no-write; \
		else \
				echo "$(COLOR_YELLOW)DEFERRED: Blueprint document manifest builder is not available yet.$(COLOR_RESET)"; \
		fi

# Purpose: build and write the Blueprint coordination document manifest reports.
# Result: generated manifest reports are written by explicit operator request.
.PHONY: document-manifest-write
document-manifest-write:
		@if [ -x "$(BLUEPRINT_PYTHON)" ] && [ -f "$(BLUEPRINT_DOCUMENT_MANIFEST_BUILDER)" ]; then \
				"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_DOCUMENT_MANIFEST_BUILDER)" --root "$(BLUEPRINT_ROOT)"; \
		else \
				echo "$(COLOR_YELLOW)DEFERRED: Blueprint document manifest builder is not available yet.$(COLOR_RESET)"; \
		fi

# Purpose: render the Blueprint coordination document awareness dashboard for this module.
# Result: operator can see new, changed, in-progress, applied and deferred coordination documents.
.PHONY: document-awareness
document-awareness:
		@if [ -x "$(BLUEPRINT_PYTHON)" ] && [ -f "$(BLUEPRINT_DOCUMENT_AWARENESS_DASHBOARD)" ]; then \
				if [ "$(NO_COLOR)" = "1" ]; then \
						"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_DOCUMENT_AWARENESS_DASHBOARD)" --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --limit "$(LIMIT)" --no-color;
				else \
						"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_DOCUMENT_AWARENESS_DASHBOARD)" --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --limit "$(LIMIT)";
				fi; \
		else \
				echo "$(COLOR_YELLOW)DEFERRED: Blueprint document awareness dashboard is not available yet.$(COLOR_RESET)"; \
		fi

# Purpose: build a module coordination context bundle without writing generated files.
# Result: bundle summary is printed; no generated bundle file is written.
.PHONY: context-bundle
context-bundle:
		@if [ -x "$(BLUEPRINT_PYTHON)" ] && [ -f "$(BLUEPRINT_CONTEXT_BUNDLE_BUILDER)" ]; then \
				"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_CONTEXT_BUNDLE_BUILDER)" --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --scope "$(SCOPE)" --limit "$(LIMIT)" --no-write;
		else \
				echo "$(COLOR_YELLOW)DEFERRED: Blueprint context bundle builder is not available yet.$(COLOR_RESET)"; \
		fi

# Purpose: build and write a module coordination context bundle.
# Result: generated bundle file is written by explicit operator request.
.PHONY: context-bundle-write
context-bundle-write:
		@if [ -x "$(BLUEPRINT_PYTHON)" ] && [ -f "$(BLUEPRINT_CONTEXT_BUNDLE_BUILDER)" ]; then \
				"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_CONTEXT_BUNDLE_BUILDER)" --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --scope "$(SCOPE)" --limit "$(LIMIT)";
		else \
				echo "$(COLOR_YELLOW)DEFERRED: Blueprint context bundle builder is not available yet.$(COLOR_RESET)"; \
		fi

# Purpose: print a module coordination context bundle to stdout.
# Result: bundle content is printed for copy/paste into an assistant chat.
.PHONY: context-bundle-print
context-bundle-print:
		@if [ -x "$(BLUEPRINT_PYTHON)" ] && [ -f "$(BLUEPRINT_CONTEXT_BUNDLE_BUILDER)" ]; then \
				"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_CONTEXT_BUNDLE_BUILDER)" --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --scope "$(SCOPE)" --limit "$(LIMIT)" --print;
		else \
				echo "$(COLOR_YELLOW)DEFERRED: Blueprint context bundle builder is not available yet.$(COLOR_RESET)"; \
		fi

# =============================================================================
# 13 Blueprint outgoing prompts FINISH
# =============================================================================


# =============================================================================
# 14 Coordination metadata START
# =============================================================================

# Purpose: validate module coordination metadata.
# Result: required coordination files exist and metadata checks pass.
.PHONY: coordination-check
coordination-check:
	@test -f "$(COORDINATION_DIR)/status/current_status.yaml"
	@test -f "$(COORDINATION_DIR)/reports/index.yaml"
	@test -f "$(COORDINATION_DIR)/prompts/index.yaml"
	@echo "$(COLOR_GREEN)Coordination files exist.$(COLOR_RESET)"

# Purpose: safely fix simple coordination metadata issues.
# Result: simple metadata repairs run or clearly report deferral.
.PHONY: coordination-fix
coordination-fix:
	@echo "$(COLOR_YELLOW)DEFERRED: automatic coordination fix is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 14 Coordination metadata FINISH
# =============================================================================


# =============================================================================
# 15 Module policy / governance START
# =============================================================================

# Purpose: verify Blueprint module policy is readable.
# Result: module policy exists and module-specific checks pass.
.PHONY: module-policy-check
module-policy-check:
	@test -f "$(BLUEPRINT_ROOT)/coordination/module_policy/$(MODULE_ID)/module_policy.md"
	@echo "$(COLOR_GREEN)Module policy is readable for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: run the module governance check sequence.
# Result: governance checks pass or target returns non-zero.
.PHONY: governance-check
governance-check:
	$(MAKE) blueprint-pull
	$(MAKE) blueprint-check
	$(MAKE) blueprint-sync-directives
	$(MAKE) blueprint-instruction-check
	$(MAKE) blueprint-standards-check
	$(MAKE) blueprint-prompts-check
	$(MAKE) module-policy-check
	$(MAKE) coordination-check
	$(MAKE) status-report

# =============================================================================
# 15 Module policy / governance FINISH
# =============================================================================


# =============================================================================
# 16 Completion packet / prompt finalization START
# =============================================================================

# Purpose: validate a completion packet.
# Result: packet is valid or target returns non-zero.
.PHONY: completion-packet-validate
completion-packet-validate:
	@test -n "$(PACKET)" || (echo "$(COLOR_RED)PACKET is required.$(COLOR_RESET)"; exit 2)
	$(PYTHON) scripts/validate_completion_packet.py "$(PACKET)"

# Purpose: apply a completion packet to module coordination records.
# Result: completion report and coordination metadata are updated idempotently.
.PHONY: completion-packet-apply
completion-packet-apply:
	@test -n "$(PACKET)" || (echo "$(COLOR_RED)PACKET is required.$(COLOR_RESET)"; exit 2)
	$(PYTHON) scripts/apply_completion_packet.py "$(PACKET)"

# Purpose: validate and apply a completion packet twice to verify idempotency.
# Result: packet apply is idempotency-safe.
.PHONY: completion-packet-check
completion-packet-check:
	@test -n "$(PACKET)" || (echo "$(COLOR_RED)PACKET is required.$(COLOR_RESET)"; exit 2)
	$(MAKE) completion-packet-validate PACKET="$(PACKET)"
	$(MAKE) completion-packet-apply PACKET="$(PACKET)"
	$(MAKE) completion-packet-apply PACKET="$(PACKET)"

# =============================================================================
# 16 Completion packet / prompt finalization FINISH
# =============================================================================


# =============================================================================
# 17 Local data / fixtures / migrations START
# =============================================================================

# Purpose: prepare local data fixtures for development or offline checks.
# Result: local fixtures are ready or target clearly reports deferral.
.PHONY: data-fixtures
data-fixtures:
	@echo "$(COLOR_YELLOW)DEFERRED: no local data fixture target is defined for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: run local non-production migrations if the module has them.
# Result: local schema/state is prepared or target clearly reports deferral.
.PHONY: migrate
migrate:
	@echo "$(COLOR_YELLOW)DEFERRED: no local migration target is defined for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 17 Local data / fixtures / migrations FINISH
# =============================================================================


# =============================================================================
# 18 Local previews / operator workflows START
# =============================================================================

# Purpose: run local operator preview workflows.
# Result: local preview output is printed or target clearly reports deferral.
.PHONY: preview
preview:
	@echo "$(COLOR_YELLOW)DEFERRED: no local preview target is defined for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 18 Local previews / operator workflows FINISH
# =============================================================================


# =============================================================================
# 19 External adapters / sandbox integrations START
# =============================================================================

# Purpose: run sandbox-only adapter checks.
# Result: sandbox adapter checks pass or target clearly reports deferral.
.PHONY: adapters-sandbox-check
adapters-sandbox-check:
	@echo "$(COLOR_YELLOW)DEFERRED: no sandbox adapter checks are defined for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 19 External adapters / sandbox integrations FINISH
# =============================================================================


# =============================================================================
# 20 Observability / diagnostics START
# =============================================================================

# Purpose: run local diagnostics for environment, paths, and readiness.
# Result: diagnostics pass or actionable warnings are printed.
.PHONY: diagnostics
diagnostics:
	@echo "$(COLOR_YELLOW)DEFERRED: no diagnostics target is defined for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 20 Observability / diagnostics FINISH
# =============================================================================


# =============================================================================
# 21 Git / release / commit helpers START
# =============================================================================

# Purpose: show concise git state before review or commit.
# Result: branch status and changed files are printed.
.PHONY: git-status
git-status:
	git status --short
	git log -1 --oneline

# Purpose: run pre-commit validation sequence.
# Result: module is ready for commit if all checks pass.
.PHONY: pre-commit
pre-commit:
	$(MAKE) module-validate
	git diff --check
	git status --short

# =============================================================================
# 21 Git / release / commit helpers FINISH
# =============================================================================


# =============================================================================
# 90 Module-specific helpers START
# =============================================================================

# Purpose: reserved area for module-specific helper targets.
# Result: module-specific helpers remain separated from standard workflow targets.

# Add module-specific targets below this line.

# =============================================================================
# 90 Module-specific helpers FINISH
# =============================================================================


# =============================================================================
# ForPrint high-level module workflow START
# =============================================================================

# Purpose: prepare the module for prompt execution.
# Result: Blueprint sync, coordination check, status report and prompt read pass.
.PHONY: module-start
module-start:
	$(MAKE) blueprint-sync
	$(MAKE) coordination-check
	$(MAKE) status-report
	$(MAKE) prompt-read

# Purpose: run the standard synchronization workflow without reading the prompt.
# Result: Blueprint sync, coordination check and status report pass.
.PHONY: module-sync
module-sync:
	$(MAKE) blueprint-sync
	$(MAKE) coordination-check
	$(MAKE) status-report

# Purpose: run standard validation before completion or commit.
# Result: check-report, check, governance-check, report-clean and status-report pass.
.PHONY: module-validate
module-validate:
	$(MAKE) check-report
	$(MAKE) check
	$(MAKE) governance-check
	$(MAKE) report-clean
	$(MAKE) status-report

# Purpose: finalize a completed prompt using completion packet automation.
# Result: completion packet idempotency check and module validation pass.
.PHONY: module-finish
module-finish:
	@test -n "$(PACKET)" || (echo "$(COLOR_RED)PACKET is required.$(COLOR_RESET)"; exit 2)
	$(MAKE) completion-packet-check PACKET="$(PACKET)"
	$(MAKE) module-validate

# =============================================================================
# ForPrint high-level module workflow FINISH
# =============================================================================
