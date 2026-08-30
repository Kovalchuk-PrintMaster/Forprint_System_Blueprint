from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "coordination/human_intent/index.yaml"


def test_human_intent_ledger_integrity():
    data = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    assert data["schema_version"] == "forprint_human_intent_index_v0_1"
    assert data["append_only"] is True
    assert len(data["modules"]) == 22

    seen = set()
    all_text = []
    for entry in data["modules"]:
        path = INDEX.parent / entry["file"]
        module = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert module["module_id"] == entry["module_id"]
        assert module["append_only"] is True
        assert len(module["intents"]) == entry["intent_count"]
        for intent in module["intents"]:
            iid = intent["intent_id"]
            assert iid not in seen
            seen.add(iid)
            assert intent["status"] in {"AGREED", "RECOVERED", "PROPOSED", "GAP"}
            assert intent["text"].strip()
            all_text.append(intent["text"].lower())

    assert len(seen) >= 150
    assert any("лінійк" in text and "стопк" in text for text in all_text)
    assert any("точні назви/url" in text or "точні назви/urls" in text for text in all_text)


def test_human_intent_governance_protocol_and_gap_are_present():
    protocol = (
        ROOT
        / "coordination/standards/governance/"
        "human_intent_capture_and_portfolio_projection_protocol_v0_1.md"
    ).read_text(encoding="utf-8")
    assert "No silent loss" in protocol
    assert "Human Intent Delta" in protocol

    data = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    gap_ids = {g["gap_id"] for g in data["known_gaps"]}
    assert "GAP-CALCULATOR-DESIGN-REFERENCE-URLS-001" in gap_ids

def test_human_intent_front_door_links_every_module_ledger():
    data = yaml.safe_load(INDEX.read_text(encoding="utf-8"))
    readme = (INDEX.parent / "README.md").read_text(encoding="utf-8")
    for entry in data["modules"]:
        assert f"]({entry['file']})" in readme

