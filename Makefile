PYTHON=.venv_blueprint/bin/python
PIP=.venv_blueprint/bin/pip

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
	@test -r diagrams/README.md || (echo "FAILED: diagrams/README.md is missing."; exit 1)
	@test -r diagrams/index.yaml || (echo "FAILED: diagrams/index.yaml is missing."; exit 1)
	@test -s diagrams/module_graph.mmd || (echo "FAILED: diagrams/module_graph.mmd is missing or empty."; exit 1)
	@test -s diagrams/ownership_map.mmd || (echo "FAILED: diagrams/ownership_map.mmd is missing or empty."; exit 1)
	@test -s diagrams/data_flow.mmd || (echo "FAILED: diagrams/data_flow.mmd is missing or empty."; exit 1)
	@test -s diagrams/project_landscape.mmd || (echo "FAILED: diagrams/project_landscape.mmd is missing or empty."; exit 1)
	@test -s diagrams/system_detail_map.mmd || (echo "FAILED: diagrams/system_detail_map.mmd is missing or empty."; exit 1)
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

standards-index:
	$(PYTHON) scripts/validate_standards_index.py

standards:
	$(PYTHON) scripts/validate_standards_index.py

standards-check: standards

check: lint-fix lint test validate diagrams guides manifest-example prompt-dispatch outgoing-prompts standards-index module-standards-template instruction-intake completion-packet-template

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
