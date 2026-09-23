from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESOLVER = ROOT / "scripts/coordination/render_blueprint_canonical_state_freshness_impact.py"


def _load():
    spec = importlib.util.spec_from_file_location(
        "canonical_state_freshness_impact_under_test",
        RESOLVER,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _state(total: int = 357):
    return {
        "hardening_release": "v0.4.1",
        "hardening_state": "ACTIVE_CURRENT",
        "pilot_module": "logistics_service",
        "logistics_prompt_id": ("logistics_service_authority_lineage_and_module_bootstrap_v0_1"),
        "logistics_queue_status": "ready_for_module_pull",
        "release_policy_state": "FAIL_CLOSED",
        "automatic_accept": False,
        "automatic_release_next_prompt": False,
        "human_intent_total": total,
    }


def _agents(total: int) -> str:
    return (
        "<!-- FORPRINT_MODULE_INVENTORY_PROGRAM_U111_BEGIN -->\n"
        "release: `v0.4.1`, hardening state `ACTIVE_CURRENT`\n"
        "external reference pilot: `logistics_service`; the bounded Blueprint internal zero-stage pilot comes first\n"
        "Logistics bootstrap prompt: "
        "`logistics_service_authority_lineage_and_module_bootstrap_v0_1`\n"
        "queue state: `ready_for_module_pull`\n"
        "release policy: fail-closed\n"
        "automatic Blueprint ACCEPT: disabled\n"
        "automatic next-prompt release: disabled\n"
        f"Human Intent portfolio: `{total}` captured intents\n"
        "<!-- FORPRINT_MODULE_INVENTORY_PROGRAM_U111_END -->\n"
    )


def test_agents_projection_is_fresh_when_claims_match():
    module = _load()
    result = module.evaluate_agents_current_state_text(
        _agents(357),
        _state(),
    )
    assert result["state"] == "FRESH"
    assert result["refresh_required"] is False
    assert result["missing_expected_fragments"] == []


def test_agents_projection_detects_historical_stale_intent_count():
    module = _load()
    result = module.evaluate_agents_current_state_text(
        _agents(329),
        _state(),
    )
    assert result["state"] == "STALE"
    assert result["refresh_required"] is True
    assert any("357" in item for item in result["missing_expected_fragments"])


def test_path_matching_supports_exact_and_recursive_prefix():
    module = _load()
    assert module.path_matches(
        "coordination/releases/current.yaml",
        "coordination/releases/current.yaml",
    )
    assert module.path_matches(
        "coordination/human_intent/modules/logistics_service.yaml",
        "coordination/human_intent/**",
    )
    assert not module.path_matches(
        "scripts/example.py",
        "coordination/human_intent/**",
    )
