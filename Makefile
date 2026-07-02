PYTHON ?= .venv_blueprint/bin/python
PIP ?= .venv_blueprint/bin/pip

MODULE ?= forprint_library
SCOPE ?= bootstrap
LIMIT ?= 40

MODULES ?=
ROADMAP ?=
BEFORE_CURRENT ?= 5
AFTER_CURRENT ?= 10
NO_COLOR ?=
ROADMAP_SUMMARY_MODULES ?= forprint_library

STATUS ?= acknowledged
LEDGER ?= coordination/blueprint_awareness/document_review_ledger.yaml
DOCUMENT ?=
SOURCE ?=
PRIORITY ?=
NOTES ?=
MODULE_COMMIT ?=

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
	@echo "Prompt queue:"
	@echo "  make prompt-queue-validate"
	@echo "  make prompt-dashboard MODULE=forprint_library"
	@echo "  make prompt-next MODULE=forprint_library"
	@echo "  make prompt-read-next MODULE=forprint_library"
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

.PHONY: check
check:
	$(MAKE) lint-fix
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) validate
	$(MAKE) diagrams-check
	$(MAKE) guides
	$(MAKE) manifest-example
	$(MAKE) prompt-dispatch
	$(MAKE) outgoing-prompts
	$(MAKE) prompt-queue-validate
	$(MAKE) document-manifest
	$(MAKE) context-bundle
	$(MAKE) roadmap-validate
	$(MAKE) roadmap-summary NO_COLOR=1
	$(MAKE) standards-index
	$(MAKE) module-standards-template
	$(MAKE) instruction-intake
	$(MAKE) completion-packet-template

.PHONY: check-report
check-report:
	$(PYTHON) scripts/run_blueprint_checks.py

# =============================================================================

# 08 Validation / check reports FINISH

# =============================================================================

# =============================================================================

# 09 Status / generated reports / cleanup START

# =============================================================================

.PHONY: clean
clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	find scripts tests -type d -name "**pycache**" -prune -exec rm -rf {} ;
	find . -maxdepth 1 -type d -name "*.egg-info" -prune -exec rm -rf {} ;

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
diagrams-check: diagrams
	$(PYTHON) scripts/validation/validate_diagrams_index.py
	@echo "OK: Blueprint diagram artifacts are generated and documented."

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
	$(PYTHON) scripts/coordination/render_prompt_dashboard.py --module "$(MODULE)" $(if $(filter 1,$(NO_COLOR)),--no-color,)

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
	$(PYTHON) scripts/coordination/render_document_awareness_dashboard.py --module "$(MODULE)" --limit "$(LIMIT)" $(if $(filter 1,$(NO_COLOR)),--no-color,)

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
		$(PYTHON) scripts/coordination/render_module_roadmap_dashboard.py --modules "$(MODULES)" --before-current "$(BEFORE_CURRENT)" --after-current "$(AFTER_CURRENT)" $(if $(filter 1,$(NO_COLOR)),--no-color,); \
	elif [ -n "$(ROADMAP)" ]; then \
		$(PYTHON) scripts/coordination/render_module_roadmap_dashboard.py --roadmap "$(ROADMAP)" --before-current "$(BEFORE_CURRENT)" --after-current "$(AFTER_CURRENT)" $(if $(filter 1,$(NO_COLOR)),--no-color,); \
	else \
		$(PYTHON) scripts/coordination/render_module_roadmap_dashboard.py --module "$(MODULE)" --before-current "$(BEFORE_CURRENT)" --after-current "$(AFTER_CURRENT)" $(if $(filter 1,$(NO_COLOR)),--no-color,); \
	fi

.PHONY: roadmap-summary
roadmap-summary:
	$(PYTHON) scripts/coordination/render_module_roadmap_dashboard.py --modules "$(ROADMAP_SUMMARY_MODULES)" $(if $(filter 1,$(NO_COLOR)),--no-color,)

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
