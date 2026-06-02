PYTHON=.venv_blueprint/bin/python
PIP=.venv_blueprint/bin/pip

.PHONY: install test lint format validate diagrams guides manifest-example prompt-dispatch check check-report clean

install:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check scripts tests

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

check: lint test validate diagrams guides manifest-example prompt-dispatch

check-report:
	$(PYTHON) scripts/run_blueprint_checks.py

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	find scripts tests -type d -name "__pycache__" -prune -exec rm -rf {} \;
	find . -maxdepth 1 -type d -name "*.egg-info" -prune -exec rm -rf {} \;
