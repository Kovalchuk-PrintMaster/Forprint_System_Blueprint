from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DELTA = ROOT / "coordination/human_intent/deltas/2026-08-31__evening_review__human_intent_delta_v0_1.yaml"
ROADMAP = ROOT / "coordination/internal_work/blueprint/roadmap_amendments/2026-08-31__evening_review__roadmap_amendments_v0_1.yaml"
PORTFOLIO_STANDARD = ROOT / "coordination/standards/governance/portfolio_rendering_and_content_specification_v0_1.md"


def test_evening_review_human_intent_delta_is_structured():
    data = yaml.safe_load(DELTA.read_text(encoding="utf-8"))
    assert data["status"] == "approved_evening_review_delta"
    assert "forprint_project_inspector" in data["modules"]
    assert "forprint_contract_registry" in data["modules"]
    ids = [
        item["intent_id"]
        for items in data["modules"].values()
        for item in items
    ]
    assert len(ids) == len(set(ids))


def test_inspector_and_contract_registry_full_horizon_present():
    data = yaml.safe_load(ROADMAP.read_text(encoding="utf-8"))
    inspector = data["modules"]["forprint_project_inspector"]
    contracts = data["modules"]["forprint_contract_registry"]
    assert {x["step_id"] for x in inspector} >= {"PI-S1", "PI-S5", "PI-S10"}
    assert {x["step_id"] for x in contracts} >= {"CR-01", "CR-09", "CR-16"}
    pilot = next(x for x in contracts if x["step_id"] == "CR-09")
    assert "Job Specification" in pilot["title"]


def test_portfolio_standard_preserves_synthetic_and_history_rules():
    text = PORTFOLIO_STANDARD.read_text(encoding="utf-8")
    assert "full-horizon roadmap" in text
    assert "Synthetic future steps are allowed and useful" in text
    assert "minimum safe left/right page margin: 5 mm" in text
    assert "preferred left/right margin: 12 mm" in text
    assert "never overwrite an older portfolio PDF" in text


def test_canonical_ledgers_received_key_agreements():
    checks = {
        "forprint_project_inspector.yaml": [
            "HI-FP-PROJECT-INSPECTOR-007",
            "HI-FP-PROJECT-INSPECTOR-018",
        ],
        "forprint_contract_registry.yaml": [
            "HI-FP-CONTRACT-REGISTRY-006",
            "HI-FP-CONTRACT-REGISTRY-017",
        ],
        "calculator_engine.yaml": [
            "HI-CALCULATOR-ENGINE-016",
            "HI-CALCULATOR-ENGINE-021",
        ],
        "forprint_operations_control_registry.yaml": [
            "HI-FP-OPERATIONS-CONTROL-REGISTRY-011",
            "HI-FP-OPERATIONS-CONTROL-REGISTRY-017",
        ],
    }
    for filename, expected in checks.items():
        path = ROOT / "coordination/human_intent/modules" / filename
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        ids = {x["intent_id"] for x in data["intents"]}
        assert set(expected) <= ids


def test_historical_portfolios_are_preserved():
    history = ROOT / "coordination/internal_work/blueprint/portfolio_reviews/history"
    assert (history / "2026-08-26__forprint_portfolio__module_detailed_review_sheets_v0_2.pdf").is_file()
    assert (history / "ForPrint_Portfolio_All_Modules_Comprehensive_Review_v1_1_2026-08-30.pdf").is_file()
