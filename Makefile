PYTHON=.venv_blueprint/bin/python
PIP=.venv_blueprint/bin/pip
MODULE ?= forprint_library
SCOPE ?= bootstrap
LIMIT ?= 40

.PHONY: guides manifest-example prompt-dispatch outgoing-prompts  check check-report
	install
	test
	lint
	lint-fix
	format
	validate
	clean
	coordination-check coordination-fix module-policy-generate module-policy-check
	module-governance-audit
	standards-index
	standards standards-check
	diagrams diagrams-check diagrams-list

install:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check scripts tests tools

lint-fix:
	$(PYTHON) -m ruff check scripts tests tools --fix

format:
	$(PYTHON) -m black scripts tests

validate:
	$(PYTHON) scripts/validate_blueprint.py

diagrams:
	$(PYTHON) scripts/generate_mermaid.py

diagrams-check: diagrams
	$(PYTHON) scripts/validation/validate_diagrams_index.py
	@echo "OK: Blueprint diagram artifacts are generated and documented."

diagrams-list:
	@find diagrams -maxdepth 1 -type f | sort

guides:
	$(PYTHON) scripts/generate_module_guides.py

manifest-example:
	$(PYTHON) scripts/validate_module_manifest.py module_manifests/examples/calculator_engine.forprint_module_manifest.example.yaml

prompt-dispatch:
	$(PYTHON) scripts/validate_prompt_dispatch_index.py

outgoing-prompts:
	$(PYTHON) scripts/validate_outgoing_prompts.py

.PHONY: prompt-queue-validate prompt-dashboard prompt-next prompt-read-next

prompt-queue-validate:
	$(PYTHON) scripts/coordination/validate_prompt_queue.py

prompt-dashboard:
	@if [ "$(NO_COLOR)" = "1" ]; then \
		$(PYTHON) scripts/coordination/render_prompt_dashboard.py --module "$(MODULE)" --no-color; \
	else \
		$(PYTHON) scripts/coordination/render_prompt_dashboard.py --module "$(MODULE)"; \
	fi

prompt-next:
	$(PYTHON) scripts/coordination/resolve_next_prompt.py --module "$(MODULE)"

prompt-read-next:
	$(PYTHON) scripts/coordination/resolve_next_prompt.py --module "$(MODULE)" --read

.PHONY: document-manifest document-awareness context-bundle context-bundle-print

document-manifest:
	$(PYTHON) scripts/coordination/build_document_manifest.py --no-write

document-awareness:
	@if [ "$(NO_COLOR)" = "1" ]; then \
		$(PYTHON) scripts/coordination/render_document_awareness_dashboard.py --module "$(MODULE)" --no-color --limit "$(LIMIT)"; \
	else \
		$(PYTHON) scripts/coordination/render_document_awareness_dashboard.py --module "$(MODULE)" --limit "$(LIMIT)"; \
	fi

context-bundle:
	$(PYTHON) scripts/coordination/build_context_bundle.py --module "$(MODULE)" --scope "$(SCOPE)" --limit "$(LIMIT)" --no-write

context-bundle-print:
	$(PYTHON) scripts/coordination/build_context_bundle.py --module "$(MODULE)" --scope "$(SCOPE)" --limit "$(LIMIT)" --print

standards-index:
	$(PYTHON) scripts/validate_standards_index.py

standards:
	$(PYTHON) scripts/validate_standards_index.py

standards-check: standards

check: lint-fix lint test validate diagrams guides manifest-example prompt-dispatch outgoing-prompts
	standards-index module-standards-template instruction-intake completion-packet-template
	prompt-queue-validate document-manifest context-bundle

check-report:
	$(PYTHON) scripts/run_blueprint_checks.py

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	find scripts tests -type d -name "__pycache__" -prune -exec rm -rf {} \;
	find . -maxdepth 1 -type d -name "*.egg-info" -prune -exec rm -rf {} \;

coordination-check:
	$(PYTHON) scripts/check_coordination_metadata.py --module-root .

coordination-fix:
	$(PYTHON) scripts/fix_coordination_metadata.py --module-root .

module-policy-generate:
	$(PYTHON) scripts/generate_module_policy_docs.py

module-policy-check:
	$(PYTHON) scripts/generate_module_policy_docs.py --check

module-governance-audit:
	$(PYTHON) scripts/audit_module_governance.py

.PHONY: module-standards-template
module-standards-template:
	$(PYTHON) scripts/validate_module_standards_template.py

.PHONY: instruction-intake
instruction-intake:
	$(PYTHON) scripts/validate_instruction_intake.py

.PHONY: completion-packet-template
completion-packet-template:
	$(PYTHON) scripts/validate_completion_packet_template.py
