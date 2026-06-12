PYTHON=.venv_blueprint/bin/python
PIP=.venv_blueprint/bin/pip

.PHONY: install test lint lint-fix format validate diagrams guides manifest-example prompt-dispatch outgoing-prompts check check-report clean
		coordination-check coordination-fix module-policy-generate module-policy-check
		module-governance-audit

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

guides:
	$(PYTHON) scripts/generate_module_guides.py

manifest-example:
	$(PYTHON) scripts/validate_module_manifest.py module_manifests/examples/calculator_engine.forprint_module_manifest.example.yaml

prompt-dispatch:
	$(PYTHON) scripts/validate_prompt_dispatch_index.py

outgoing-prompts:
	$(PYTHON) scripts/validate_outgoing_prompts.py

check: lint-fix lint test validate diagrams guides manifest-example prompt-dispatch outgoing-prompts

check-report: outgoing-prompts
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
