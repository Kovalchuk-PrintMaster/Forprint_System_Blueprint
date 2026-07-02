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
#   Use normal Makefile syntax with TAB-prefixed recipe lines.
#   Do not use .RECIPEPREFIX in standard ForPrint module Makefiles.

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
BLUEPRINT_DOCUMENT_AWARENESS_LEDGER_UPDATER ?= $(BLUEPRINT_ROOT)/scripts/coordination/update_document_awareness_ledger.py

PACKET ?=
STATUS ?= acknowledged
DOCUMENT ?=
SOURCE ?=
PRIORITY ?=
NOTES ?=
MODULE_COMMIT ?=
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
	@echo "Operator workflow:"
	@echo "  make module-start"
	@echo "  make module-sync"
	@echo "  make module-validate"
	@echo "  make module-finish PACKET=coordination/completion_packets/examples/<packet>.yaml"
	@echo ""
	@echo "Blueprint / coordination:"
	@echo "  make blueprint-sync"
	@echo "  make blueprint-instruction"
	@echo "  make blueprint-standards"
	@echo "  make blueprint-prompts"
	@echo "  make prompt-dashboard"
	@echo "  make prompt-next"
	@echo "  make prompt-read-next"
	@echo "  make document-awareness"
	@echo "  make context-bundle-print"
	@echo ""
	@echo "Module runtime / infrastructure:"
	@echo "  make install"
	@echo "  make env-check"
	@echo "  make run"
	@echo "  make start"
	@echo "  make stop"
	@echo "  make restart"
	@echo "  make services-up"
	@echo "  make services-down"
	@echo "  make db-check"
	@echo "  make adapters-check"
	@echo "  make diagnostics"
	@echo ""
	@echo "Validation:"
	@echo "  make lint"
	@echo "  make lint-fix"
	@echo "  make test"
	@echo "  make check"
	@echo "  make check-report"
	@echo "  make status-report"
	@echo "  make report-clean"

# =============================================================================
# 01 Help / navigation FINISH
# =============================================================================


# =============================================================================
# 02 Operator entrypoints / Blueprint-first workflow START
# =============================================================================

# Purpose: prepare the module for prompt execution.
# Result: Blueprint sync, document awareness, coordination status and next prompt read pass.
.PHONY: module-start
module-start:
	$(MAKE) blueprint-sync
	$(MAKE) document-awareness
	$(MAKE) coordination-check
	$(MAKE) status-report
	$(MAKE) prompt-read-next

# Purpose: run the standard synchronization workflow without reading the prompt.
# Result: Blueprint sync, document awareness, coordination check and status report pass.
.PHONY: module-sync
module-sync:
	$(MAKE) blueprint-sync
	$(MAKE) document-awareness
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
# 02 Operator entrypoints / Blueprint-first workflow FINISH
# =============================================================================


# =============================================================================
# 03 Blueprint repository synchronization START
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
# Result: Blueprint, directives, instruction intake, standards, prompts and document manifest are synchronized or checked.
.PHONY: blueprint-sync
blueprint-sync:
	$(MAKE) blueprint-pull
	$(MAKE) blueprint-check
	$(MAKE) blueprint-sync-directives
	$(MAKE) blueprint-instruction
	$(MAKE) blueprint-standards
	$(MAKE) blueprint-prompts
	$(MAKE) document-manifest

# =============================================================================
# 03 Blueprint repository synchronization FINISH
# =============================================================================


# =============================================================================
# 04 Blueprint instruction intake START
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
# 04 Blueprint instruction intake FINISH
# =============================================================================


# =============================================================================
# 05 Blueprint standards and policies START
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
# 05 Blueprint standards and policies FINISH
# =============================================================================


# =============================================================================
# 06 Blueprint outgoing prompts / prompt queue START
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
# Result: prompts are listed, checked, synchronized and prompt queue dashboard is rendered.
.PHONY: blueprint-prompts
blueprint-prompts:
	$(MAKE) blueprint-prompts-list
	$(MAKE) blueprint-prompts-check
	$(MAKE) blueprint-prompts-sync
	$(MAKE) prompt-queue-validate
	$(MAKE) prompt-dashboard

# Purpose: show the active synced prompt for legacy/non-migrated modules.
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

# =============================================================================
# 06 Blueprint outgoing prompts / prompt queue FINISH
# =============================================================================


# =============================================================================
# 07 Blueprint document awareness START
# =============================================================================

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
			"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_DOCUMENT_AWARENESS_DASHBOARD)" --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --limit "$(LIMIT)" --no-color; \
		else \
			"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_DOCUMENT_AWARENESS_DASHBOARD)" --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --limit "$(LIMIT)"; \
		fi; \
	else \
		echo "$(COLOR_YELLOW)DEFERRED: Blueprint document awareness dashboard is not available yet.$(COLOR_RESET)"; \
	fi

# Purpose: build a module coordination context bundle without writing generated files.
# Result: bundle summary is printed; no generated bundle file is written.
.PHONY: context-bundle
context-bundle:
	@if [ -x "$(BLUEPRINT_PYTHON)" ] && [ -f "$(BLUEPRINT_CONTEXT_BUNDLE_BUILDER)" ]; then \
		"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_CONTEXT_BUNDLE_BUILDER)" --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --scope "$(SCOPE)" --limit "$(LIMIT)" --no-write; \
	else \
		echo "$(COLOR_YELLOW)DEFERRED: Blueprint context bundle builder is not available yet.$(COLOR_RESET)"; \
	fi

# Purpose: build and write a module coordination context bundle.
# Result: generated bundle file is written by explicit operator request.
.PHONY: context-bundle-write
context-bundle-write:
	@if [ -x "$(BLUEPRINT_PYTHON)" ] && [ -f "$(BLUEPRINT_CONTEXT_BUNDLE_BUILDER)" ]; then \
		"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_CONTEXT_BUNDLE_BUILDER)" --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --scope "$(SCOPE)" --limit "$(LIMIT)"; \
	else \
		echo "$(COLOR_YELLOW)DEFERRED: Blueprint context bundle builder is not available yet.$(COLOR_RESET)"; \
	fi

# Purpose: print a module coordination context bundle to stdout.
# Result: bundle content is printed for copy/paste into an assistant chat.
.PHONY: context-bundle-print
context-bundle-print:
	@if [ -x "$(BLUEPRINT_PYTHON)" ] && [ -f "$(BLUEPRINT_CONTEXT_BUNDLE_BUILDER)" ]; then \
		"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_CONTEXT_BUNDLE_BUILDER)" --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --scope "$(SCOPE)" --limit "$(LIMIT)" --print; \
	else \
		echo "$(COLOR_YELLOW)DEFERRED: Blueprint context bundle builder is not available yet.$(COLOR_RESET)"; \
	fi

# Purpose: preview an update to the module-local document awareness ledger.
# Result: selected documents and hashes are shown, but the ledger file is not changed.
.PHONY: document-ledger-preview
document-ledger-preview:
	@if [ -x "$(BLUEPRINT_PYTHON)" ] && [ -f "$(BLUEPRINT_DOCUMENT_AWARENESS_LEDGER_UPDATER)" ]; then \
		if [ -z "$(DOCUMENT)$(SOURCE)$(PRIORITY)" ]; then \
			echo "$(COLOR_RED)FAILED: provide DOCUMENT=..., SOURCE=..., or PRIORITY=...$(COLOR_RESET)"; \
			exit 1; \
		fi; \
		set -- --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --status "$(STATUS)"; \
		if [ -n "$(DOCUMENT)" ]; then set -- "$$@" --document "$(DOCUMENT)"; fi; \
		if [ -n "$(SOURCE)" ]; then set -- "$$@" --source "$(SOURCE)"; fi; \
		if [ -n "$(PRIORITY)" ]; then set -- "$$@" --priority "$(PRIORITY)"; fi; \
		if [ -n "$(NOTES)" ]; then set -- "$$@" --notes "$(NOTES)"; fi; \
		if [ -n "$(MODULE_COMMIT)" ]; then set -- "$$@" --module-commit "$(MODULE_COMMIT)"; fi; \
		set -- "$$@" --no-write; \
		"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_DOCUMENT_AWARENESS_LEDGER_UPDATER)" "$$@"; \
	else \
		echo "$(COLOR_YELLOW)DEFERRED: Blueprint document awareness ledger updater is not available yet.$(COLOR_RESET)"; \
	fi

# Purpose: update the module-local document awareness ledger with current Blueprint document hashes.
# Result: selected documents are written to the local ledger with the requested review status.
.PHONY: document-ledger-update
document-ledger-update:
	@if [ -x "$(BLUEPRINT_PYTHON)" ] && [ -f "$(BLUEPRINT_DOCUMENT_AWARENESS_LEDGER_UPDATER)" ]; then \
		if [ -z "$(DOCUMENT)$(SOURCE)$(PRIORITY)" ]; then \
			echo "$(COLOR_RED)FAILED: provide DOCUMENT=..., SOURCE=..., or PRIORITY=...$(COLOR_RESET)"; \
			exit 1; \
		fi; \
		set -- --root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --status "$(STATUS)"; \
		if [ -n "$(DOCUMENT)" ]; then set -- "$$@" --document "$(DOCUMENT)"; fi; \
		if [ -n "$(SOURCE)" ]; then set -- "$$@" --source "$(SOURCE)"; fi; \
		if [ -n "$(PRIORITY)" ]; then set -- "$$@" --priority "$(PRIORITY)"; fi; \
		if [ -n "$(NOTES)" ]; then set -- "$$@" --notes "$(NOTES)"; fi; \
		if [ -n "$(MODULE_COMMIT)" ]; then set -- "$$@" --module-commit "$(MODULE_COMMIT)"; fi; \
		"$(BLUEPRINT_PYTHON)" "$(BLUEPRINT_DOCUMENT_AWARENESS_LEDGER_UPDATER)" "$$@"; \
	else \
		echo "$(COLOR_YELLOW)DEFERRED: Blueprint document awareness ledger updater is not available yet.$(COLOR_RESET)"; \
	fi

# =============================================================================
# 07 Blueprint document awareness FINISH
# =============================================================================


# =============================================================================
# 08 Module coordination metadata START
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
# 08 Module coordination metadata FINISH
# =============================================================================


# =============================================================================
# 09 Module governance / policy checks START
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
	$(MAKE) prompt-queue-validate
	$(MAKE) document-manifest
	$(MAKE) module-policy-check
	$(MAKE) coordination-check
	$(MAKE) status-report

# =============================================================================
# 09 Module governance / policy checks FINISH
# =============================================================================


# =============================================================================
# 10 Module install / bootstrap START
# =============================================================================

# Purpose: install or verify development dependencies.
# Result: local environment is ready for checks.
.PHONY: install
install:
	@echo "$(COLOR_YELLOW)DEFERRED: implement module-specific install workflow.$(COLOR_RESET)"

# Purpose: run first-time module bootstrap steps when needed.
# Result: bootstrap is completed or documented deferral is printed.
.PHONY: bootstrap
bootstrap:
	@echo "$(COLOR_YELLOW)DEFERRED: bootstrap workflow is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 10 Module install / bootstrap FINISH
# =============================================================================


# =============================================================================
# 11 Module environment / local configuration START
# =============================================================================

# Purpose: verify local environment variables, paths and executables.
# Result: environment is ready or documented deferral is printed.
.PHONY: env-check
env-check:
	@echo "$(COLOR_YELLOW)DEFERRED: environment check is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: verify local configuration files.
# Result: configuration is readable or documented deferral is printed.
.PHONY: config-check
config-check:
	@echo "$(COLOR_YELLOW)DEFERRED: configuration check is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: verify that required local secrets are configured without printing secret values.
# Result: required secrets are present or documented deferral is printed.
.PHONY: secrets-check
secrets-check:
	@echo "$(COLOR_YELLOW)DEFERRED: secrets check is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 11 Module environment / local configuration FINISH
# =============================================================================


# =============================================================================
# 12 Runtime control / process lifecycle START
# =============================================================================

# Purpose: run the module locally when a runtime exists.
# Result: local runtime starts or documented deferral is printed.
.PHONY: run
run:
	@echo "$(COLOR_YELLOW)DEFERRED: local run target is not implemented for $(MODULE_ID).$(COLOR_RESET)"

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

# Purpose: reload runtime configuration if the module supports reload.
# Result: runtime reloads or documented deferral is printed.
.PHONY: reload
reload:
	@echo "$(COLOR_YELLOW)DEFERRED: runtime reload is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: show runtime status when applicable.
# Result: runtime status is printed or documented deferral is printed.
.PHONY: status
status:
	@echo "$(COLOR_YELLOW)DEFERRED: runtime status is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: show runtime logs when applicable.
# Result: runtime logs are printed or documented deferral is printed.
.PHONY: logs
logs:
	@echo "$(COLOR_YELLOW)DEFERRED: runtime logs are not implemented for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 12 Runtime control / process lifecycle FINISH
# =============================================================================


# =============================================================================
# 13 Infrastructure / local services START
# =============================================================================

# Purpose: run local development services required by the module.
# Result: local service stack starts or clearly reports deferral.
.PHONY: services-up
services-up:
	@echo "$(COLOR_YELLOW)DEFERRED: no local services are defined for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: stop local development services required by the module.
# Result: local service stack stops or clearly reports deferral.
.PHONY: services-down
services-down:
	@echo "$(COLOR_YELLOW)DEFERRED: no local services are defined for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: restart local development services required by the module.
# Result: local service stack restarts through down/up.
.PHONY: services-restart
services-restart:
	$(MAKE) services-down
	$(MAKE) services-up

# Purpose: show local development service status.
# Result: service status is printed or documented deferral is printed.
.PHONY: services-status
services-status:
	@echo "$(COLOR_YELLOW)DEFERRED: service status is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: compatibility alias for older module Makefiles.
# Result: delegates to services-up.
.PHONY: services-start
services-start:
	$(MAKE) services-up

# Purpose: compatibility alias for older module Makefiles.
# Result: delegates to services-down.
.PHONY: services-stop
services-stop:
	$(MAKE) workers-stop

# Purpose: start local monitors, workers, queue consumers, or watchers.
# Result: background helpers start or clearly report deferral.
.PHONY: workers-start monitors-start
workers-start monitors-start:
	$(MAKE) workers-start

# Purpose: stop local monitors, workers, queue consumers, or watchers.
# Result: background helpers stop or clearly report deferral.
.PHONY: workers-stop monitors-stop
workers-stop monitors-stop:
	@echo "$(COLOR_YELLOW)DEFERRED: no workers/monitors are defined for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: restart local workers or monitors when applicable.
# Result: background helpers restart through stop/start.
.PHONY: workers-restart monitors-restart
workers-restart monitors-restart:
	$(MAKE) workers-stop
	$(MAKE) workers-start

# =============================================================================
# 13 Infrastructure / local services FINISH
# =============================================================================


# =============================================================================
# 14 Database / storage / migrations START
# =============================================================================

# Purpose: verify local database or storage connectivity.
# Result: database/storage is reachable or documented deferral is printed.
.PHONY: db-check
db-check:
	@echo "$(COLOR_YELLOW)DEFERRED: database/storage check is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: run local non-production migrations if the module has them.
# Result: local schema/state is prepared or target clearly reports deferral.
.PHONY: db-migrate migrate
db-migrate migrate:
	@echo "$(COLOR_YELLOW)DEFERRED: no local migration target is defined for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: upgrade local schema/state to the latest version.
# Result: local schema/state is upgraded or documented deferral is printed.
.PHONY: db-upgrade
db-upgrade:
	$(MAKE) db-migrate

# Purpose: downgrade local schema/state if supported.
# Result: local schema/state is downgraded or documented deferral is printed.
.PHONY: db-downgrade
db-downgrade:
	@echo "$(COLOR_YELLOW)DEFERRED: database downgrade is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: load local seed data if the module has seed fixtures.
# Result: local seed data is loaded or documented deferral is printed.
.PHONY: db-seed
db-seed:
	@echo "$(COLOR_YELLOW)DEFERRED: database seed is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: reset local database/storage state when safe for development.
# Result: local development state is reset or documented deferral is printed.
.PHONY: db-reset
db-reset:
	@echo "$(COLOR_YELLOW)DEFERRED: database reset is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 14 Database / storage / migrations FINISH
# =============================================================================

# Purpose: run local non-production migrations if the module has them.
# Result: local schema/state is prepared or target clearly reports deferral.
.PHONY: migrate
migrate:
	@echo "$(COLOR_YELLOW)DEFERRED: no local migration target is defined for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 15 Data import / export / fixtures START
# =============================================================================

# Purpose: verify local fixtures for development or offline checks.
# Result: local fixtures are readable or documented deferral is printed.
.PHONY: fixtures-check
fixtures-check:
	@echo "$(COLOR_YELLOW)DEFERRED: fixture check is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: prepare local data fixtures for development or offline checks.
# Result: local fixtures are ready or target clearly reports deferral.
.PHONY: fixtures-load data-fixtures
fixtures-load data-fixtures:
	@echo "$(COLOR_YELLOW)DEFERRED: no local data fixture target is defined for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: preview an import workflow without production writes.
# Result: import preview is printed or documented deferral is printed.
.PHONY: import-preview
import-preview:
	@echo "$(COLOR_YELLOW)DEFERRED: import preview is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: preview an export workflow without production writes.
# Result: export preview is printed or documented deferral is printed.
.PHONY: export-preview
export-preview:
	@echo "$(COLOR_YELLOW)DEFERRED: export preview is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: prepare local data fixtures for development or offline checks.
# Result: local fixtures are ready or target clearly reports deferral.
.PHONY: data-fixtures
data-fixtures:
	@echo "$(COLOR_YELLOW)DEFERRED: no local data fixture target is defined for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 15 Data import / export / fixtures FINISH
# =============================================================================


# =============================================================================
# 16 External adapters / sandbox integrations START
# =============================================================================

# Purpose: verify sandbox or external adapter configuration.
# Result: adapter configuration is valid or documented deferral is printed.
.PHONY: adapters-check
adapters-check:
	@echo "$(COLOR_YELLOW)DEFERRED: adapter checks are not implemented for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: compatibility alias for sandbox adapter and smoke checks.
# Result: delegates to the standard sandbox-check target.
.PHONY: adapters-smoke adapters-sandbox-check
adapters-smoke adapters-sandbox-check :
	$(MAKE) sandbox-check

# Purpose: verify sandbox synchronization prerequisites.
# Result: sandbox sync prerequisites are valid or documented deferral is printed.
.PHONY: sandbox-check
sandbox-check:
	@echo "$(COLOR_YELLOW)DEFERRED: sandbox check is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: run sandbox synchronization when applicable.
# Result: sandbox data is synchronized or documented deferral is printed.
.PHONY: sandbox-sync
sandbox-sync:
	@echo "$(COLOR_YELLOW)DEFERRED: sandbox sync is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: verify sandbox adapter configuration and connectivity when applicable.
# Result: sandbox adapter checks run or clearly report deferral.
.PHONY: adapters-sandbox-check
adapters-sandbox-check:
	@echo "$(COLOR_YELLOW)DEFERRED: no sandbox adapter check is defined for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 16 External adapters / sandbox integrations FINISH
# =============================================================================


# =============================================================================
# 17 Local previews / operator workflows START
# =============================================================================

# Purpose: run local operator preview workflows.
# Result: local preview output is printed or target clearly reports deferral.
.PHONY: preview
preview:
	@echo "$(COLOR_YELLOW)DEFERRED: no local preview target is defined for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: run a lightweight local smoke workflow.
# Result: smoke output is printed or documented deferral is printed.
.PHONY: smoke
smoke:
	@echo "$(COLOR_YELLOW)DEFERRED: smoke workflow is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: run a local operator demo workflow.
# Result: operator demo output is printed or documented deferral is printed.
.PHONY: operator-demo
operator-demo:
	@echo "$(COLOR_YELLOW)DEFERRED: operator demo is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 17 Local previews / operator workflows FINISH
# =============================================================================


# =============================================================================
# 18 Observability / diagnostics / logs START
# =============================================================================

# Purpose: run local diagnostics for environment, paths, and readiness.
# Result: diagnostics pass or actionable warnings are printed.
.PHONY: diagnostics
diagnostics:
	@echo "$(COLOR_YELLOW)DEFERRED: no diagnostics target is defined for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: run a lightweight module health check.
# Result: health status is printed or documented deferral is printed.
.PHONY: health
health:
	@echo "$(COLOR_YELLOW)DEFERRED: health check is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: inspect important local paths and runtime state.
# Result: inspection output is printed or documented deferral is printed.
.PHONY: inspect
inspect:
	@echo "$(COLOR_YELLOW)DEFERRED: inspect target is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 18 Observability / diagnostics / logs FINISH
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
# 19 Syntax / formatting / lint START
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

# Purpose: format source files if the module uses a formatter.
# Result: formatters run or documented deferral is printed.
.PHONY: format
format:
	@echo "$(COLOR_YELLOW)DEFERRED: formatter is not configured for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: check source formatting without modifying files.
# Result: formatting is valid or documented deferral is printed.
.PHONY: format-check
format-check:
	@echo "$(COLOR_YELLOW)DEFERRED: format check is not configured for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 19 Syntax / formatting / lint FINISH
# =============================================================================


# =============================================================================
# 20 Tests START
# =============================================================================

# Purpose: run the module test suite.
# Result: all tests pass or target returns non-zero.
.PHONY: test
test:
	$(PYTHON) -m pytest -q

# Purpose: run unit tests when the module separates test types.
# Result: unit tests pass or documented deferral is printed.
.PHONY: test-unit
test-unit:
	$(MAKE) test

# Purpose: run contract tests when the module separates test types.
# Result: contract tests pass or documented deferral is printed.
.PHONY: test-contract
test-contract:
	@echo "$(COLOR_YELLOW)DEFERRED: contract tests are not separated for $(MODULE_ID).$(COLOR_RESET)"

# Purpose: run integration tests when the module separates test types.
# Result: integration tests pass or documented deferral is printed.
.PHONY: test-integration
test-integration:
	@echo "$(COLOR_YELLOW)DEFERRED: integration tests are not separated for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 20 Tests FINISH
# =============================================================================


# =============================================================================
# 21 Validation / check reports START
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
# 21 Validation / check reports FINISH
# =============================================================================


# =============================================================================
# 22 Status reports / generated reports / cleanup START
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
# 22 Status reports / generated reports / cleanup FINISH
# =============================================================================


# =============================================================================
# 23 Completion packet / prompt finalization START
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
# 23 Completion packet / prompt finalization FINISH
# =============================================================================


# =============================================================================
# 24 Git / release / commit helpers START
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

# Purpose: run release readiness checks when release packaging exists.
# Result: release readiness is printed or documented deferral is printed.
.PHONY: release-check
release-check:
	@echo "$(COLOR_YELLOW)DEFERRED: release check is not implemented for $(MODULE_ID).$(COLOR_RESET)"

# =============================================================================
# 24 Git / release / commit helpers FINISH
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
