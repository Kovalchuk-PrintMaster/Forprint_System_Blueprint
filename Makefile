# ForPrint System Blueprint Makefile
#
# This file is the executable command surface for the Blueprint repository.
# Public targets must preserve repository ownership and command semantics:
#   - preview/status/list/show/validate/check targets are operator-safe and
#     must not hide apply/commit/push/merge behavior;
#   - explicit write/apply/fix/generate targets may mutate only Blueprint;
#   - Blueprint completion intake reads module repositories but never writes them;
#   - completion-accept requires a successful read-only intake check;
#   - completion-return remains available for invalid evidence and writes only
#     Blueprint review records.
#
# GNU Make recipes use TAB indentation. Do not use .RECIPEPREFIX.

.DEFAULT_GOAL := help
.DELETE_ON_ERROR:

PYTHON ?= .venv_blueprint/bin/python
BLUEPRINT_PYTHON ?= $(PYTHON)
PIP ?= $(PYTHON) -m pip

MODULE ?= forprint_library
MODULE_ROOT ?= ../$(MODULE)
MODULES ?=
ROADMAP ?=

SCOPE ?= bootstrap
LIMIT ?= 40
BEFORE_CURRENT ?= 5
AFTER_CURRENT ?= 10
ROADMAP_SUMMARY_MODULES ?= forprint_library

PACKET ?=
REVIEW_NOTES ?=
COMPLETION_COMMIT ?=
REVIEWED_AT ?=
REMOTE ?= origin
BRANCH ?=

STATUS ?= acknowledged
LEDGER ?= coordination/blueprint_awareness/document_review_ledger.yaml
DOCUMENT ?=
SOURCE ?=
PROMPT_ID ?=
APPLY ?= 0
REPLACE ?= 0
PRIORITY ?=
NOTES ?=
MODULE_COMMIT ?=
GOVERNANCE_STATUS_FORMAT ?= status
# =============================================================================

# 00 Environment / constants START

# =============================================================================

BLUEPRINT_MODULE_MANIFEST_EXAMPLE ?= module_manifests/examples/calculator_engine.forprint_module_manifest.example.yaml

# =============================================================================

# 00 Environment / constants FINISH

# =============================================================================

# =============================================================================

# 01 Help / navigation START

# =============================================================================

.PHONY: help
help:
	@echo "ForPrint System Blueprint Make targets"
	@echo ""
	@echo "Install / bootstrap:"
	@echo "  make install"
	@echo ""
	@echo "Lint / tests / validation:"
	@echo "  make lint"
	@echo "  make lint-fix"
	@echo "  make format"
	@echo "  make test"
	@echo "  make validate"
	@echo "  make markdown-fences"
	@echo "  make check"
	@echo "  make check-report"
	@echo ""
	@echo "Blueprint artifacts:"
	@echo "  make diagrams"
	@echo "  make diagrams-check"
	@echo "  make diagrams-list"
	@echo "  make guides"
	@echo "  make manifest-example"
	@echo ""
	@echo "Prompt preparation / release:"
	@echo "  make prompt-prepare SOURCE=operator_input/prompts/example.md"
	@echo "  make prompt-prepare SOURCE=operator_input/prompts/example.md APPLY=1"
	@echo "  make prompt-prepare SOURCE=operator_input/prompts/example.md APPLY=1 REPLACE=1"
	@echo "  make prompt-release MODULE=forprint_library PROMPT_ID=library_example_v0_1"
	@echo "  make prompt-release MODULE=forprint_library PROMPT_ID=library_example_v0_1 APPLY=1"
	@echo "  Release apply remains fail-closed unless governance policy authorizes it."
	@echo ""
	@echo "Prompt queue navigation:"
	@echo "  make prompt-queue-validate"
	@echo "  make prompt-dashboard MODULE=forprint_library"
	@echo "  make prompt-next MODULE=forprint_library"
	@echo "  make prompt-read-next MODULE=forprint_library"
	@echo "  make completion-intake-check MODULE=logistics_service MODULE_ROOT=../forprint_logistics_service PACKET=coordination/completion_packets/records/example.yaml COMPLETION_COMMIT=<commit>"
	@echo "  make completion-revision-status"
	@echo "  make completion-revision-check"
	@echo "  make completion-intake-check MODULE=logistics_service MODULE_ROOT=../forprint_logistics_service PACKET=<v0.3-packet> COMPLETION_COMMIT=<commit> ALLOW_CANDIDATE_REFERENCE=1"
	@echo "  make completion-intake-preview MODULE=logistics_service MODULE_ROOT=../forprint_logistics_service PACKET=coordination/completion_packets/records/example.yaml COMPLETION_COMMIT=<commit>"
	@echo "  make completion-accept MODULE=logistics_service MODULE_ROOT=../forprint_logistics_service PACKET=coordination/completion_packets/records/example.yaml COMPLETION_COMMIT=<commit>"
	@echo "  make completion-return MODULE=logistics_service MODULE_ROOT=../forprint_logistics_service PACKET=coordination/completion_packets/records/example.yaml REVIEW_NOTES='Corrections required'"
	@echo "  make completion-finalize-check MODULE=logistics_service"
	@echo "  make next-work-suggestion MODULE=logistics_service"
	@echo ""
	@echo "Coordination document awareness:"
	@echo "  make document-manifest"
	@echo "  make document-awareness MODULE=forprint_library LIMIT=20"
	@echo "  make context-bundle MODULE=forprint_library SCOPE=bootstrap LIMIT=10"
	@echo "  make context-bundle-print MODULE=forprint_library SCOPE=bootstrap LIMIT=10"
	@echo "  make document-ledger-preview MODULE=forprint_library DOCUMENT=coordination/global_policy/forprint_project_doctrine.md"
	@echo "  make document-ledger-update MODULE=forprint_library DOCUMENT=coordination/global_policy/forprint_project_doctrine.md STATUS=acknowledged"
	@echo ""
	@echo "Module roadmap:"
	@echo "  make roadmap-validate MODULE=forprint_library"
	@echo "  make roadmap-dashboard MODULE=forprint_library"
	@echo "  make roadmap-dashboard MODULES=forprint_library,forprint_integration_gateway,forprint_crm"
	@echo "  make roadmap-summary"
	@echo "  make coordination-pulse"
	@echo "  make prompt-contract-v0-4-validate"
	@echo "  make completion-packet-v0-4-validate"
	@echo "  make roadmap-summary ROADMAP_SUMMARY_MODULES=forprint_library,forprint_integration_gateway"
	@echo "Standards / governance:"
	@echo "  make standards-index"
	@echo "  make standards"
	@echo "  make standards-check"
	@echo "  make module-standards-template"
	@echo "  make instruction-intake"
	@echo "  make completion-packet-template"
	@echo "  make coordination-check"
	@echo "  make coordination-fix"
	@echo "  make module-policy-generate"
	@echo "  make module-policy-check"
	@echo "  make module-governance-audit"
	@echo ""
	@echo "Module workflow control:"
	@echo "  make module-workflow-list"
	@echo "  make module-workflow-check"
	@echo "  make module-self-audit MODULE=forprint_system_blueprint"
	@echo "  make module-self-audit-resume MODULE=forprint_system_blueprint"
	@echo "  make module-self-status MODULE=forprint_system_blueprint"
	@echo "  make module-self-report-full MODULE=forprint_system_blueprint"
	@echo "  make blueprint-self-audit"
	@echo "  make blueprint-self-audit-resume"
	@echo "  make blueprint-self-status"
	@echo "  make blueprint-governance-status GOVERNANCE_STATUS_FORMAT=status"
	@echo "  make blueprint-governance-status GOVERNANCE_STATUS_FORMAT=yaml"
	@echo "  make blueprint-governance-status GOVERNANCE_STATUS_FORMAT=json"
	@echo "  make blueprint-self-report-full"
	@echo "  make modules-self-status"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean"

# =============================================================================

# 01 Help / navigation FINISH

# =============================================================================

# =============================================================================

# 02 Install / bootstrap START

# =============================================================================

.PHONY: install
install:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

# =============================================================================

# 02 Install / bootstrap FINISH

# =============================================================================

# =============================================================================

# 06 Syntax / formatting / lint START

# =============================================================================

.PHONY: lint
lint:
	$(PYTHON) -m ruff check scripts tests tools

.PHONY: lint-fix
lint-fix:
	$(PYTHON) -m ruff check scripts tests tools --fix

.PHONY: format
format:
	$(PYTHON) -m black scripts tests

# =============================================================================

# 06 Syntax / formatting / lint FINISH

# =============================================================================

# =============================================================================

# 07 Tests START

# =============================================================================

.PHONY: test
test:
	$(PYTHON) -m pytest -q

# =============================================================================

# 07 Tests FINISH

# =============================================================================

# =============================================================================

# 08 Validation / check reports START

# =============================================================================

.PHONY: validate
validate:
	$(PYTHON) scripts/validate_blueprint.py

.PHONY: markdown-fences
markdown-fences:
	$(PYTHON) scripts/validation/validate_markdown_fences.py

.PHONY: check
check: check-module-registry-consistency check-self-coordination-consistency check-repository-knowledge-snapshots check-inventory-status-consistency check-repository-knowledge-freshness check-rci-semantic-enrichment check-redm-dependency-enrichment check-semantic-coverage-closure check-repository-knowledge-reconciliation check-inventory-acceptance-evidence-index check-inventory-acceptance-dry-run
	$(PYTHON) scripts/run_blueprint_checks.py

.PHONY: check-report
check-report:
	$(PYTHON) scripts/run_blueprint_checks.py

.PHONY: check-report-full
check-report-full:
	$(PYTHON) scripts/run_blueprint_checks.py --full-log

.PHONY: check-fix
check-fix:
	$(MAKE) lint-fix
	$(MAKE) check

# =============================================================================

# 08 Validation / check reports FINISH

# =============================================================================

# =============================================================================

# 09 Status / generated reports / cleanup START

# =============================================================================

.PHONY: clean
clean:
	rm -rf -- .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	find scripts tests -type d -name "__pycache__" -prune -exec rm -rf -- {} +
	find . -maxdepth 1 -type d -name "*.egg-info" -prune -exec rm -rf -- {} +

# =============================================================================

# 09 Status / generated reports / cleanup FINISH

# =============================================================================

# =============================================================================

# 10 Blueprint validation / generation START

# =============================================================================

.PHONY: diagrams
diagrams:
	$(PYTHON) scripts/generate_mermaid.py

.PHONY: diagrams-check
diagrams-check:
	$(PYTHON) scripts/validation/validate_diagrams_index.py
	@echo "OK: existing Blueprint diagram artifacts are documented and valid."

.PHONY: diagrams-list
diagrams-list:
	@find diagrams -maxdepth 1 -type f | sort

.PHONY: guides
guides:
	$(PYTHON) scripts/generate_module_guides.py

.PHONY: manifest-example
manifest-example:
	$(PYTHON) scripts/validate_module_manifest.py "$(BLUEPRINT_MODULE_MANIFEST_EXAMPLE)"

# =============================================================================

# 10 Blueprint validation / generation FINISH

# =============================================================================

# =============================================================================

# 11 Prompt dispatch / outgoing prompts START

# =============================================================================

.PHONY: prompt-dispatch
prompt-dispatch:
	$(PYTHON) scripts/validate_prompt_dispatch_index.py

.PHONY: outgoing-prompts
outgoing-prompts:
	$(PYTHON) scripts/validate_outgoing_prompts.py

# Purpose: validate and prepare a non-executable Blueprint-owned prompt draft.
# Safety: preview by default; APPLY=1 mutates only Blueprint drafts/. REPLACE=1
# is explicit and never releases, commits, pushes, merges, or writes to modules.
.PHONY: prompt-prepare
prompt-prepare:
	@set -eu; \
		if [ -z "$(SOURCE)" ]; then \
			echo "FAILED: prompt-prepare requires SOURCE=<managed prompt source path>"; \
			exit 2; \
		fi; \
		case "$(APPLY)" in \
			0|1) ;; \
			*) echo "FAILED: APPLY must be 0 or 1"; exit 2 ;; \
		esac; \
		case "$(REPLACE)" in \
			0|1) ;; \
			*) echo "FAILED: REPLACE must be 0 or 1"; exit 2 ;; \
		esac; \
		set -- prepare --root "." --source "$(SOURCE)"; \
		if [ "$(APPLY)" = "1" ]; then set -- "$$@" --apply; fi; \
		if [ "$(REPLACE)" = "1" ]; then set -- "$$@" --replace; fi; \
		$(PYTHON) scripts/coordination/manage_outgoing_prompt.py "$$@"; \
		if [ "$(APPLY)" = "1" ]; then \
			$(PYTHON) scripts/coordination/validate_prompt_queue.py; \
			$(PYTHON) scripts/validate_outgoing_prompts.py; \
		fi

# Purpose: publish exactly one prepared prompt into Prompt Queue v0.2.
# Safety: preview by default; APPLY=1 is still governed by the fail-closed
# Blueprint release policy. MODULE must be passed explicitly despite its global
# navigation default. Never writes to a module repository or commit/push/merge.
.PHONY: prompt-release
prompt-release:
	@set -eu; \
		if [ "$(origin MODULE)" != "command line" ]; then \
			echo "FAILED: prompt-release requires explicit MODULE=<canonical module id>; the default MODULE is not accepted"; \
			exit 2; \
		fi; \
		if [ -z "$(MODULE)" ]; then \
			echo "FAILED: prompt-release requires MODULE=<canonical module id>"; \
			exit 2; \
		fi; \
		if [ -z "$(PROMPT_ID)" ]; then \
			echo "FAILED: prompt-release requires PROMPT_ID=<canonical prompt id>"; \
			exit 2; \
		fi; \
		case "$(APPLY)" in \
			0|1) ;; \
			*) echo "FAILED: APPLY must be 0 or 1"; exit 2 ;; \
		esac; \
		set -- release --root "." --module "$(MODULE)" --prompt-id "$(PROMPT_ID)"; \
		if [ "$(APPLY)" = "1" ]; then set -- "$$@" --apply; fi; \
		$(PYTHON) scripts/coordination/manage_outgoing_prompt.py "$$@"; \
		if [ "$(APPLY)" = "1" ]; then \
			$(PYTHON) scripts/coordination/validate_prompt_queue.py; \
			$(PYTHON) scripts/validate_outgoing_prompts.py; \
		fi

# =============================================================================

# 11 Prompt dispatch / outgoing prompts FINISH

# =============================================================================

# =============================================================================

# 12 Prompt Queue navigation START

# =============================================================================

.PHONY: prompt-queue-validate
prompt-queue-validate:
	$(PYTHON) scripts/coordination/validate_prompt_queue.py

.PHONY: prompt-dashboard
prompt-dashboard:
	$(PYTHON) scripts/coordination/render_prompt_dashboard.py --module "$(MODULE)"

# Purpose: canonical read-only Blueprint prompt status command.
# Safety: does not prepare, release, or mutate prompts.
.PHONY: prompt-status
prompt-status:
	$(MAKE) prompt-dashboard MODULE="$(MODULE)"

.PHONY: prompt-next
prompt-next:
	$(PYTHON) scripts/coordination/resolve_next_prompt.py --module "$(MODULE)"

.PHONY: prompt-read-next
prompt-read-next:
	$(PYTHON) scripts/coordination/resolve_next_prompt.py --module "$(MODULE)" --read

# =============================================================================

# 12 Prompt Queue navigation FINISH

# =============================================================================

# =============================================================================
# 12A Completion intake / finalization / next work START
# =============================================================================

# Purpose: validate/report completion exchange revision lifecycle.
# Safety: Blueprint read-only.
.PHONY: completion-revision-status completion-revision-check
completion-revision-status:
	$(PYTHON) scripts/coordination/completion_revision_status.py --root "."

completion-revision-check:
	$(PYTHON) scripts/coordination/completion_revision_status.py --root "." --output-format yaml

# Purpose: independently verify published module completion evidence.
# Safety: read-only for Blueprint and module repositories; uses git ls-remote
# without fetch/checkout/restore and never executes module code.
.PHONY: completion-intake-check
completion-intake-check:
	@set -eu; \
		if [ -z "$(MODULE)" ]; then echo "FAILED: provide MODULE=<canonical module id>"; exit 2; fi; \
		if [ -z "$(MODULE_ROOT)" ]; then echo "FAILED: provide MODULE_ROOT=<module repository path>"; exit 2; fi; \
		if [ -z "$(PACKET)" ]; then echo "FAILED: provide PACKET=<module-relative completion packet path>"; exit 2; fi; \
		if [ -z "$(COMPLETION_COMMIT)" ]; then echo "FAILED: provide COMPLETION_COMMIT=<published commit>"; exit 2; fi; \
		set -- \
			--root "." \
			--module "$(MODULE)" \
			--module-root "$(MODULE_ROOT)" \
			--packet "$(PACKET)" \
			--completion-commit "$(COMPLETION_COMMIT)" \
			--remote "$(REMOTE)"; \
		if [ -n "$(BRANCH)" ]; then set -- "$$@" --branch "$(BRANCH)"; fi; \
		if [ "$(ALLOW_CANDIDATE_REFERENCE)" = "1" ]; then set -- "$$@" --allow-candidate-reference; fi; \
		$(PYTHON) scripts/coordination/completion_intake_check.py "$$@"

# Purpose: build the accepted-decision intake plan after the same read-only check.
# Safety: read-only; no Blueprint or module files are written.
.PHONY: completion-intake-preview
completion-intake-preview:
	@set -eu; \
		if [ -z "$(MODULE)" ]; then echo "FAILED: provide MODULE=<canonical module id>"; exit 2; fi; \
		if [ -z "$(MODULE_ROOT)" ]; then echo "FAILED: provide MODULE_ROOT=<module repository path>"; exit 2; fi; \
		if [ -z "$(PACKET)" ]; then echo "FAILED: provide PACKET=<module-relative completion packet path>"; exit 2; fi; \
		if [ -z "$(COMPLETION_COMMIT)" ]; then echo "FAILED: provide COMPLETION_COMMIT=<published commit>"; exit 2; fi; \
		set -- \
			--root "." \
			--module "$(MODULE)" \
			--module-root "$(MODULE_ROOT)" \
			--packet "$(PACKET)" \
			--decision accepted \
			--completion-commit "$(COMPLETION_COMMIT)" \
			--remote "$(REMOTE)"; \
		if [ -n "$(BRANCH)" ]; then set -- "$$@" --branch "$(BRANCH)"; fi; \
		if [ -n "$(REVIEW_NOTES)" ]; then set -- "$$@" --review-notes "$(REVIEW_NOTES)"; fi; \
		if [ -n "$(REVIEWED_AT)" ]; then set -- "$$@" --reviewed-at "$(REVIEWED_AT)"; fi; \
		$(PYTHON) scripts/coordination/module_completion_intake.py "$$@"

# Purpose: accept validated module completion evidence.
# Safety: mutates Blueprint queue/roadmap/review files only; the Python layer
# independently blocks writes unless completion-intake-check passed.
.PHONY: completion-accept
completion-accept:
	@set -eu; \
		if [ -z "$(MODULE)" ]; then echo "FAILED: provide MODULE=<canonical module id>"; exit 2; fi; \
		if [ -z "$(MODULE_ROOT)" ]; then echo "FAILED: provide MODULE_ROOT=<module repository path>"; exit 2; fi; \
		if [ -z "$(PACKET)" ]; then echo "FAILED: provide PACKET=<module-relative completion packet path>"; exit 2; fi; \
		if [ -z "$(COMPLETION_COMMIT)" ]; then echo "FAILED: provide COMPLETION_COMMIT=<published commit>"; exit 2; fi; \
		set -- \
			--root "." \
			--module "$(MODULE)" \
			--module-root "$(MODULE_ROOT)" \
			--packet "$(PACKET)" \
			--decision accepted \
			--completion-commit "$(COMPLETION_COMMIT)" \
			--remote "$(REMOTE)" \
			--write; \
		if [ -n "$(BRANCH)" ]; then set -- "$$@" --branch "$(BRANCH)"; fi; \
		if [ -n "$(REVIEW_NOTES)" ]; then set -- "$$@" --review-notes "$(REVIEW_NOTES)"; fi; \
		if [ -n "$(REVIEWED_AT)" ]; then set -- "$$@" --reviewed-at "$(REVIEWED_AT)"; fi; \
		$(PYTHON) scripts/coordination/module_completion_intake.py "$$@"

# Purpose: return completion evidence for correction with explicit notes.
# Safety: does not require a GREEN intake check and writes only Blueprint
# queue/roadmap/review records. It never mutates the module repository.
.PHONY: completion-return
completion-return:
	@set -eu; \
		if [ -z "$(MODULE)" ]; then echo "FAILED: provide MODULE=<canonical module id>"; exit 2; fi; \
		if [ -z "$(MODULE_ROOT)" ]; then echo "FAILED: provide MODULE_ROOT=<module repository path>"; exit 2; fi; \
		if [ -z "$(PACKET)" ]; then echo "FAILED: provide PACKET=<module-relative completion packet path>"; exit 2; fi; \
		if [ -z "$(REVIEW_NOTES)" ]; then echo "FAILED: completion-return requires REVIEW_NOTES=..."; exit 2; fi; \
		set -- \
			--root "." \
			--module "$(MODULE)" \
			--module-root "$(MODULE_ROOT)" \
			--packet "$(PACKET)" \
			--decision returned_for_fix \
			--review-notes "$(REVIEW_NOTES)" \
			--write; \
		if [ -n "$(COMPLETION_COMMIT)" ]; then set -- "$$@" --completion-commit "$(COMPLETION_COMMIT)"; fi; \
		if [ -n "$(REVIEWED_AT)" ]; then set -- "$$@" --reviewed-at "$(REVIEWED_AT)"; fi; \
		$(PYTHON) scripts/coordination/module_completion_intake.py "$$@"

# Purpose: show the next Blueprint coordination action for a module.
# Safety: read-only.
.PHONY: next-work-suggestion
next-work-suggestion:
	$(PYTHON) scripts/coordination/resolve_next_module_work.py --root "." --module "$(MODULE)"

# Purpose: validate queue/roadmap state after an explicit accept/return action.
# Safety: read-only; does not finalize or write completion state.
.PHONY: completion-finalize-check
completion-finalize-check:
	$(PYTHON) scripts/coordination/validate_prompt_queue.py --root "."
	$(PYTHON) scripts/coordination/validate_module_roadmap.py --root "." --module "$(MODULE)"
	$(PYTHON) scripts/coordination/resolve_next_module_work.py --root "." --module "$(MODULE)"

# =============================================================================
# 12A Completion intake / finalization / next work FINISH
# =============================================================================

# =============================================================================

# 13 Coordination document awareness START

# =============================================================================

.PHONY: document-manifest
document-manifest:
	$(PYTHON) scripts/coordination/build_document_manifest.py --no-write

.PHONY: document-manifest-write
document-manifest-write:
	$(PYTHON) scripts/coordination/build_document_manifest.py

.PHONY: document-awareness
document-awareness:
	$(PYTHON) scripts/coordination/render_document_awareness_dashboard.py --module "$(MODULE)" --limit "$(LIMIT)"

.PHONY: context-bundle
context-bundle:
	$(PYTHON) scripts/coordination/build_context_bundle.py --module "$(MODULE)" --scope "$(SCOPE)" --limit "$(LIMIT)" --no-write

.PHONY: context-bundle-write
context-bundle-write:
	$(PYTHON) scripts/coordination/build_context_bundle.py --module "$(MODULE)" --scope "$(SCOPE)" --limit "$(LIMIT)"

.PHONY: context-bundle-print
context-bundle-print:
	$(PYTHON) scripts/coordination/build_context_bundle.py --module "$(MODULE)" --scope "$(SCOPE)" --limit "$(LIMIT)" --print

.PHONY: document-ledger-preview
document-ledger-preview:
	@set -eu; \
	if [ -z "$(DOCUMENT)$(SOURCE)$(PRIORITY)" ]; then \
		echo "FAILED: provide DOCUMENT=..., SOURCE=..., or PRIORITY=..."; \
		exit 1; \
	fi; \
	set -- --root "." --module "$(MODULE)" --ledger "$(LEDGER)" --status "$(STATUS)"; \
	if [ -n "$(DOCUMENT)" ]; then set -- "$$@" --document "$(DOCUMENT)"; fi; \
	if [ -n "$(SOURCE)" ]; then set -- "$$@" --source "$(SOURCE)"; fi; \
	if [ -n "$(PRIORITY)" ]; then set -- "$$@" --priority "$(PRIORITY)"; fi; \
	if [ -n "$(NOTES)" ]; then set -- "$$@" --notes "$(NOTES)"; fi; \
	if [ -n "$(MODULE_COMMIT)" ]; then set -- "$$@" --module-commit "$(MODULE_COMMIT)"; fi; \
	set -- "$$@" --no-write; \
	$(PYTHON) scripts/coordination/update_document_awareness_ledger.py "$$@"

.PHONY: document-ledger-update
document-ledger-update:
	@set -eu; \
	if [ -z "$(DOCUMENT)$(SOURCE)$(PRIORITY)" ]; then \
		echo "FAILED: provide DOCUMENT=..., SOURCE=..., or PRIORITY=..."; \
		exit 1; \
	fi; \
	set -- --root "." --module "$(MODULE)" --ledger "$(LEDGER)" --status "$(STATUS)"; \
	if [ -n "$(DOCUMENT)" ]; then set -- "$$@" --document "$(DOCUMENT)"; fi; \
	if [ -n "$(SOURCE)" ]; then set -- "$$@" --source "$(SOURCE)"; fi; \
	if [ -n "$(PRIORITY)" ]; then set -- "$$@" --priority "$(PRIORITY)"; fi; \
	if [ -n "$(NOTES)" ]; then set -- "$$@" --notes "$(NOTES)"; fi; \
	if [ -n "$(MODULE_COMMIT)" ]; then set -- "$$@" --module-commit "$(MODULE_COMMIT)"; fi; \
	$(PYTHON) scripts/coordination/update_document_awareness_ledger.py "$$@"

# =============================================================================

# 13 Coordination document awareness FINISH


# =============================================================================

# 14 Module roadmap START

# =============================================================================

.PHONY: roadmap-validate
roadmap-validate:
	@if [ -n "$(ROADMAP)" ]; then \
		$(PYTHON) scripts/coordination/validate_module_roadmap.py --roadmap "$(ROADMAP)"; \
	else \
		$(PYTHON) scripts/coordination/validate_module_roadmap.py --module "$(MODULE)"; \
	fi

.PHONY: roadmap-dashboard
roadmap-dashboard:
	@if [ -n "$(MODULES)" ]; then \
		$(PYTHON) scripts/coordination/render_module_roadmap_dashboard.py --modules "$(MODULES)" --before-current "$(BEFORE_CURRENT)" --after-current "$(AFTER_CURRENT)"; \
	elif [ -n "$(ROADMAP)" ]; then \
		$(PYTHON) scripts/coordination/render_module_roadmap_dashboard.py --roadmap "$(ROADMAP)" --before-current "$(BEFORE_CURRENT)" --after-current "$(AFTER_CURRENT)"; \
	else \
		$(PYTHON) scripts/coordination/render_module_roadmap_dashboard.py --module "$(MODULE)" --before-current "$(BEFORE_CURRENT)" --after-current "$(AFTER_CURRENT)"; \
	fi

.PHONY: roadmap-summary
roadmap-summary:
	$(PYTHON) scripts/coordination/render_module_roadmap_dashboard.py --modules "$(ROADMAP_SUMMARY_MODULES)"

# =============================================================================

# 14 Module roadmap FINISH

# =============================================================================

# =============================================================================

# 15 Standards / templates / instruction intake START

# =============================================================================

.PHONY: standards-index
standards-index:
	$(PYTHON) scripts/validate_standards_index.py

.PHONY: standards
standards:
	$(PYTHON) scripts/validate_standards_index.py

.PHONY: standards-check
standards-check: standards

.PHONY: module-standards-template
module-standards-template:
	$(PYTHON) scripts/validate_module_standards_template.py

.PHONY: instruction-intake
instruction-intake:
	$(PYTHON) scripts/validate_instruction_intake.py

.PHONY: completion-packet-template
completion-packet-template:
	$(PYTHON) scripts/validate_completion_packet_template.py

# =============================================================================

# 15 Standards / templates / instruction intake FINISH

# =============================================================================

# =============================================================================

# 16 Coordination metadata / module policy / governance START

# =============================================================================

.PHONY: coordination-check
coordination-check:
	$(PYTHON) scripts/check_coordination_metadata.py --module-root .

.PHONY: coordination-fix
coordination-fix:
	$(PYTHON) scripts/fix_coordination_metadata.py --module-root .

.PHONY: module-policy-generate
module-policy-generate:
	$(PYTHON) scripts/generate_module_policy_docs.py

.PHONY: module-policy-check
module-policy-check:
	$(PYTHON) scripts/generate_module_policy_docs.py --check

.PHONY: module-governance-audit
module-governance-audit:
	$(PYTHON) scripts/audit_module_governance.py

.PHONY: module-governance-audit-check
module-governance-audit-check:
	$(PYTHON) scripts/audit_module_governance.py --no-write

# =============================================================================

# 16 Coordination metadata / module policy / governance FINISH

# =============================================================================

# =============================================================================
# Blueprint reporting consolidation audit
# =============================================================================

.PHONY: reporting-consolidation-audit
reporting-consolidation-audit:
	$(PYTHON) scripts/reporting/audit_consolidation.py

.PHONY: reporting-consolidation-audit-json
reporting-consolidation-audit-json:
	@$(PYTHON) scripts/reporting/audit_consolidation.py --json

# =============================================================================

# 17 Module workflow control / self-knowledge START

# =============================================================================

.PHONY: module-workflow-list
module-workflow-list:
	$(PYTHON) -m scripts.coordination.modules.module_workflow_cli --root "." list

.PHONY: module-workflow-check
module-workflow-check:
	$(PYTHON) -m scripts.coordination.modules.module_workflow_cli --root "." check

.PHONY: module-self-audit
module-self-audit:
	$(PYTHON) -m scripts.coordination.modules.module_workflow_cli --root "." --module "$(MODULE)" self-audit

.PHONY: module-self-audit-resume
module-self-audit-resume:
	$(PYTHON) -m scripts.coordination.modules.module_workflow_cli --root "." --module "$(MODULE)" self-audit-resume

.PHONY: module-self-status
module-self-status:
	$(PYTHON) -m scripts.coordination.modules.module_workflow_cli --root "." --module "$(MODULE)" self-status

.PHONY: module-self-report-full
module-self-report-full:
	$(PYTHON) -m scripts.coordination.modules.module_workflow_cli --root "." --module "$(MODULE)" self-report-full

.PHONY: modules-self-status
modules-self-status:
	$(PYTHON) -m scripts.coordination.modules.module_workflow_cli --root "." modules-status

.PHONY: blueprint-self-audit
blueprint-self-audit:
	$(MAKE) module-self-audit MODULE=forprint_system_blueprint

.PHONY: blueprint-self-audit-resume
blueprint-self-audit-resume:
	$(MAKE) module-self-audit-resume MODULE=forprint_system_blueprint

.PHONY: blueprint-self-status
blueprint-self-status:
	$(MAKE) module-self-status MODULE=forprint_system_blueprint

.PHONY: blueprint-self-report-full
blueprint-self-report-full:
	$(MAKE) module-self-report-full MODULE=forprint_system_blueprint

.PHONY: blueprint-governance-status
blueprint-governance-status:
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_blueprint_governance_status.py --repo-root "." --format "$(GOVERNANCE_STATUS_FORMAT)"

# =============================================================================

# 17 Module workflow control / self-knowledge FINISH

# =============================================================================

# =============================================================================
# 18 Blueprint inventory / repository-knowledge gates START
# =============================================================================

# These targets may write only declared generated reports/tmp evidence.
# They are invoked by the repository gate and must never mutate source records.

.PHONY: check-module-registry-consistency
check-module-registry-consistency:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_module_registry_resolution.py --manifest coordination/repository_knowledge/registries/module_registry_resolution_v0_1.yaml --repo-root . --output reports/module_registry_consistency_report.yaml

.PHONY: roadmap-status
roadmap-status:
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_blueprint_self_coordination_status.py --module "$(MODULE)" --view roadmap

.PHONY: prompts-status
prompts-status:
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_blueprint_self_coordination_status.py --module "$(MODULE)" --view prompts

.PHONY: check-self-coordination-consistency
check-self-coordination-consistency:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_blueprint_self_coordination.py --repo-root . --roadmap coordination/self_coordination/roadmap.yaml --queue coordination/self_coordination/prompt_queue/index.yaml --completion coordination/self_coordination/completion_packets/2026-07-30__forprint_system_blueprint__self_coordination_consistency_ci_gate_v0_1.yaml --module-plan coordination/self_coordination/module_plans/forprint_library.yaml --module-plan coordination/self_coordination/module_plans/logistics_service.yaml --module-plan coordination/self_coordination/module_plans/telegram_bot.yaml --output reports/blueprint_self_coordination_consistency_report.yaml

.PHONY: inventory-status
inventory-status:
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_blueprint_inventory_status.py --module "$(MODULE)"

.PHONY: check-repository-knowledge-snapshots
check-repository-knowledge-snapshots:
	@mkdir -p reports tmp/repository_knowledge_snapshot_comparisons
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_repository_knowledge_snapshot_comparisons.py --manifest coordination/repository_knowledge/snapshot_comparison_gate_v0_1.yaml --repo-root . --work-dir tmp/repository_knowledge_snapshot_comparisons --output reports/repository_knowledge_snapshot_comparison_report.yaml

.PHONY: check-inventory-status-consistency
check-inventory-status-consistency:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_blueprint_inventory_status_consistency.py --wave coordination/internal_work/blueprint/inventory_refresh/2026-07-29__blueprint__semantic_inventory_wave_2_v0_1.yaml --dashboard coordination/internal_work/blueprint/inventory_refresh/2026-07-29__blueprint__inventory_coverage_drift_dashboard_v0_1.yaml --maintenance coordination/repository_knowledge/inventory_maintenance_v0_1.yaml --roadmap coordination/self_coordination/roadmap.yaml --renderer scripts/coordination/render_blueprint_inventory_status.py --module forprint_system_blueprint --output reports/blueprint_inventory_status_consistency_report.yaml

.PHONY: check-repository-knowledge-freshness
check-repository-knowledge-freshness:
	@mkdir -p tmp
	@$(BLUEPRINT_PYTHON) scripts/coordination/assess_repository_knowledge_freshness.py --manifest coordination/repository_knowledge/snapshot_comparison_gate_v0_1.yaml --repo-root . --output tmp/repository_knowledge_freshness_status.yaml

.PHONY: repository-knowledge-freshness-status
repository-knowledge-freshness-status:
	@mkdir -p tmp
	@$(BLUEPRINT_PYTHON) scripts/coordination/assess_repository_knowledge_freshness.py --manifest coordination/repository_knowledge/snapshot_comparison_gate_v0_1.yaml --repo-root . --output tmp/repository_knowledge_freshness_status.yaml
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_repository_knowledge_freshness_status.py --report tmp/repository_knowledge_freshness_status.yaml

.PHONY: check-rci-semantic-enrichment
check-rci-semantic-enrichment:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_rci_semantic_enrichment.py --source coordination/repository_knowledge/inventory/2026-07-29__forprint_system_blueprint__repository_capability_inventory_v0_3.yaml --candidate coordination/repository_knowledge/inventory/2026-07-30__forprint_system_blueprint__repository_capability_inventory_v0_4.yaml --enrichment-record coordination/internal_work/blueprint/inventory_refresh/2026-07-30__blueprint__rci_semantic_enrichment_v0_1.yaml --repo-root . --expected-source-sha256 3b9278a9bea091ae83f045a2fb5028c97f5fbd00a69b2be173a92a6d9d58d9aa --output reports/rci_semantic_enrichment_validation_report.yaml

.PHONY: check-redm-dependency-enrichment
check-redm-dependency-enrichment:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_redm_dependency_enrichment.py --source coordination/repository_knowledge/flows/2026-07-29__forprint_system_blueprint__repository_execution_dependency_map_v0_3.yaml --candidate coordination/repository_knowledge/flows/2026-07-30__forprint_system_blueprint__repository_execution_dependency_map_v0_4.yaml --capability-context coordination/repository_knowledge/inventory/2026-07-30__forprint_system_blueprint__repository_capability_inventory_v0_4.yaml --enrichment-record coordination/internal_work/blueprint/inventory_refresh/2026-07-30__blueprint__redm_dependency_enrichment_v0_1.yaml --repo-root . --expected-source-sha256 33b0224e3a3b7651412e49fc17b3a0f8192714bd009155d12877712067b8ee70 --output reports/redm_dependency_enrichment_validation_report.yaml

.PHONY: check-semantic-coverage-closure
check-semantic-coverage-closure:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_semantic_coverage_closure.py --rci coordination/repository_knowledge/inventory/2026-07-30__forprint_system_blueprint__repository_capability_inventory_v0_4.yaml --redm coordination/repository_knowledge/flows/2026-07-30__forprint_system_blueprint__repository_execution_dependency_map_v0_4.yaml --rci-validation reports/rci_semantic_enrichment_validation_report.yaml --redm-validation reports/redm_dependency_enrichment_validation_report.yaml --freshness reports/repository_knowledge_freshness_report.yaml --unknowns coordination/internal_work/blueprint/inventory_refresh/2026-07-30__blueprint__semantic_inventory_unknowns_triage_v0_1.yaml --module forprint_system_blueprint --output reports/semantic_coverage_closure_report.yaml

.PHONY: semantic-coverage-status
semantic-coverage-status:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_semantic_coverage_closure.py --rci coordination/repository_knowledge/inventory/2026-07-30__forprint_system_blueprint__repository_capability_inventory_v0_4.yaml --redm coordination/repository_knowledge/flows/2026-07-30__forprint_system_blueprint__repository_execution_dependency_map_v0_4.yaml --rci-validation reports/rci_semantic_enrichment_validation_report.yaml --redm-validation reports/redm_dependency_enrichment_validation_report.yaml --freshness reports/repository_knowledge_freshness_report.yaml --unknowns coordination/internal_work/blueprint/inventory_refresh/2026-07-30__blueprint__semantic_inventory_unknowns_triage_v0_1.yaml --module "$(MODULE)" --output reports/semantic_coverage_closure_report.yaml
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_semantic_coverage_closure_status.py --report reports/semantic_coverage_closure_report.yaml

.PHONY: check-repository-knowledge-reconciliation
check-repository-knowledge-reconciliation:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_repository_knowledge_reconciliation.py --rci coordination/repository_knowledge/inventory/2026-07-30__forprint_system_blueprint__repository_capability_inventory_v0_4.yaml --redm coordination/repository_knowledge/flows/2026-07-30__forprint_system_blueprint__repository_execution_dependency_map_v0_4.yaml --coordination-direction coordination/repository_knowledge/direction/blueprint_coordination/2026-07-29__forprint_system_blueprint__state_direction_rationale_snapshot_v0_2.yaml --portfolio-direction coordination/repository_knowledge/direction/system_portfolio/2026-07-29__forprint_system__state_direction_rationale_snapshot_v0_2.yaml --authority-policy coordination/repository_knowledge/artifact_authority_policy_v0_1.yaml --module-registry coordination/repository_knowledge/registries/module_registry_resolution_v0_1.yaml --closure-report reports/semantic_coverage_closure_report.yaml --rci-validation reports/rci_semantic_enrichment_validation_report.yaml --redm-validation reports/redm_dependency_enrichment_validation_report.yaml --module forprint_system_blueprint --output reports/repository_knowledge_reconciliation_report.yaml

.PHONY: repository-knowledge-reconciliation-status
repository-knowledge-reconciliation-status:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_repository_knowledge_reconciliation.py --rci coordination/repository_knowledge/inventory/2026-07-30__forprint_system_blueprint__repository_capability_inventory_v0_4.yaml --redm coordination/repository_knowledge/flows/2026-07-30__forprint_system_blueprint__repository_execution_dependency_map_v0_4.yaml --coordination-direction coordination/repository_knowledge/direction/blueprint_coordination/2026-07-29__forprint_system_blueprint__state_direction_rationale_snapshot_v0_2.yaml --portfolio-direction coordination/repository_knowledge/direction/system_portfolio/2026-07-29__forprint_system__state_direction_rationale_snapshot_v0_2.yaml --authority-policy coordination/repository_knowledge/artifact_authority_policy_v0_1.yaml --module-registry coordination/repository_knowledge/registries/module_registry_resolution_v0_1.yaml --closure-report reports/semantic_coverage_closure_report.yaml --rci-validation reports/rci_semantic_enrichment_validation_report.yaml --redm-validation reports/redm_dependency_enrichment_validation_report.yaml --module "$(MODULE)" --output reports/repository_knowledge_reconciliation_report.yaml
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_repository_knowledge_reconciliation_status.py --report reports/repository_knowledge_reconciliation_report.yaml

.PHONY: check-inventory-acceptance-evidence-index
check-inventory-acceptance-evidence-index:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_inventory_acceptance_evidence_index.py --index coordination/internal_work/blueprint/inventory_refresh/2026-07-30__blueprint__inventory_acceptance_evidence_index_v0_1.yaml --repo-root . --module forprint_system_blueprint --output reports/inventory_acceptance_evidence_index_validation_report.yaml

.PHONY: inventory-acceptance-evidence-status
inventory-acceptance-evidence-status:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_inventory_acceptance_evidence_index.py --index coordination/internal_work/blueprint/inventory_refresh/2026-07-30__blueprint__inventory_acceptance_evidence_index_v0_1.yaml --repo-root . --module "$(MODULE)" --output reports/inventory_acceptance_evidence_index_validation_report.yaml
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_inventory_acceptance_evidence_status.py --index coordination/internal_work/blueprint/inventory_refresh/2026-07-30__blueprint__inventory_acceptance_evidence_index_v0_1.yaml --report reports/inventory_acceptance_evidence_index_validation_report.yaml

.PHONY: check-inventory-acceptance-dry-run
check-inventory-acceptance-dry-run:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/run_inventory_acceptance_dry_run.py --index coordination/internal_work/blueprint/inventory_refresh/2026-07-30__blueprint__inventory_acceptance_evidence_index_v0_1.yaml --index-validation reports/inventory_acceptance_evidence_index_validation_report.yaml --rci coordination/repository_knowledge/inventory/2026-07-30__forprint_system_blueprint__repository_capability_inventory_v0_4.yaml --redm coordination/repository_knowledge/flows/2026-07-30__forprint_system_blueprint__repository_execution_dependency_map_v0_4.yaml --closure reports/semantic_coverage_closure_report.yaml --reconciliation reports/repository_knowledge_reconciliation_report.yaml --authority-policy coordination/repository_knowledge/artifact_authority_policy_v0_1.yaml --plan coordination/internal_work/blueprint/inventory_refresh/2026-07-29__blueprint__inventory_refresh_plan_v0_1.yaml --roadmap coordination/self_coordination/roadmap.yaml --queue coordination/self_coordination/prompt_queue/index.yaml --module forprint_system_blueprint --output reports/inventory_acceptance_dry_run_report.yaml

.PHONY: inventory-acceptance-dry-run-status
inventory-acceptance-dry-run-status:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/run_inventory_acceptance_dry_run.py --index coordination/internal_work/blueprint/inventory_refresh/2026-07-30__blueprint__inventory_acceptance_evidence_index_v0_1.yaml --index-validation reports/inventory_acceptance_evidence_index_validation_report.yaml --rci coordination/repository_knowledge/inventory/2026-07-30__forprint_system_blueprint__repository_capability_inventory_v0_4.yaml --redm coordination/repository_knowledge/flows/2026-07-30__forprint_system_blueprint__repository_execution_dependency_map_v0_4.yaml --closure reports/semantic_coverage_closure_report.yaml --reconciliation reports/repository_knowledge_reconciliation_report.yaml --authority-policy coordination/repository_knowledge/artifact_authority_policy_v0_1.yaml --plan coordination/internal_work/blueprint/inventory_refresh/2026-07-29__blueprint__inventory_refresh_plan_v0_1.yaml --roadmap coordination/self_coordination/roadmap.yaml --queue coordination/self_coordination/prompt_queue/index.yaml --module "$(MODULE)" --output reports/inventory_acceptance_dry_run_report.yaml
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_inventory_acceptance_dry_run_status.py --report reports/inventory_acceptance_dry_run_report.yaml

# =============================================================================
# 18 Blueprint inventory / repository-knowledge gates FINISH
# =============================================================================

COORDINATION_PULSE_FORMAT ?= text

.PHONY: coordination-pulse
coordination-pulse:
	@$(BLUEPRINT_PYTHON) scripts/coordination/coordination_pulse.py --root . --output-format "$(COORDINATION_PULSE_FORMAT)"

PROMPT_CONTRACT_V0_4 ?= coordination/prompt_contracts/forprint_system_blueprint/blueprint_v0_4_immutable_prompt_contract_v0_1/blueprint_v0_4_immutable_prompt_contract_v0_1__contract_v0_1.yaml

.PHONY: prompt-contract-v0-4-validate
prompt-contract-v0-4-validate:
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_prompt_contract_v0_4.py --root . --contract "$(PROMPT_CONTRACT_V0_4)"

COMPLETION_PACKET_V0_4 ?= coordination/templates/module_completion_packet_v0_4.example.yaml

.PHONY: completion-packet-v0-4-validate
completion-packet-v0-4-validate:
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_completion_packet_v0_4.py --root . --packet "$(COMPLETION_PACKET_V0_4)" --template-mode

.PHONY: completion-outbox-v0-4-validate
completion-outbox-v0-4-validate:
	.venv_blueprint/bin/python scripts/coordination/validate_completion_outbox_v0_4.py coordination/templates/module_completion_outbox_v0_4.example.yaml --root . --registry coordination/registry/coordination_source_registry_v0_1.yaml --template

.PHONY: completion-discovery-intake-v0-4
completion-discovery-intake-v0-4:
	.venv_blueprint/bin/python scripts/coordination/completion_discovery_and_intake_v0_4.py --root .

.PHONY: review-roadmap-queue-transaction-v0-4
review-roadmap-queue-transaction-v0-4:
	.venv_blueprint/bin/python scripts/coordination/review_roadmap_queue_transaction_v0_4.py --root . --live-status

.PHONY: next-prompt-selection-activation-v0-4
next-prompt-selection-activation-v0-4:
	.venv_blueprint/bin/python scripts/coordination/next_prompt_selection_activation_v0_4.py --root . --live-status
