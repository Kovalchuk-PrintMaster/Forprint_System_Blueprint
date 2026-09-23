from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "scripts/coordination/preflight_logistics_h10_bootstrap_prompt_v0_1.py"


def _load():
    spec = importlib.util.spec_from_file_location(
        "logistics_h10_preflight_under_test",
        PREFLIGHT,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_front_matter_parser():
    module = _load()
    text = "---\nprompt_id: p1\nlifecycle_state: released\n---\nbody\n"
    header = module.front_matter(text)
    assert header["prompt_id"] == "p1"
    assert header["lifecycle_state"] == "released"


def test_machine_prompt_parser():
    module = _load()
    text = "# ForPrint machine prompt\n\n```yaml\nmodule: logistics_service\nobjective: test\n```\n"
    payload = module.machine_prompt(text)
    assert payload == {"module": "logistics_service", "objective": "test"}


def test_blocking_check_helper():
    module = _load()
    rows = []
    module.check(rows, "x", True, {"value": 1})
    module.check(rows, "y", False, {"value": 2})
    assert rows[0]["state"] == "PASS"
    assert rows[1]["state"] == "HOLD"
