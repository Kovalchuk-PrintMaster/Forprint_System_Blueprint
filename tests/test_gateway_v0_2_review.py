from pathlib import Path

import yaml


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_gateway_v0_2_review_exists_and_is_paused() -> None:
    root = Path(__file__).resolve().parents[1]

    data = _load_yaml(root / "machine/integration_gateway_v0_2_review.yaml")
    review = data["integration_gateway_v0_2_review"]

    assert review["module_id"] == "forprint_integration_gateway"
    assert review["review_status"] == "reviewed"
    assert review["overall_assessment"]["pause_recommended"] is True
    assert review["current_gate_status"]["recommended_status"] == "paused_after_v0_2"


def test_gateway_v0_2_review_confirms_no_forbidden_scope() -> None:
    root = Path(__file__).resolve().parents[1]

    data = _load_yaml(root / "machine/integration_gateway_v0_2_review.yaml")
    does_not_own = set(data["integration_gateway_v0_2_review"]["confirmed_boundaries"]["gateway_does_not_own"])

    assert "production_api" in does_not_own
    assert "database" in does_not_own
    assert "real_crm_integration" in does_not_own
    assert "business_workflow_logic" in does_not_own