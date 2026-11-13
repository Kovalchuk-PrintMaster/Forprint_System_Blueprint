from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

REGISTRY = ROOT / "coordination/registry/worker_runtime_adapters_v0_1.yaml"
BENCHMARK = (
    ROOT
    / "coordination/standards/automation/"
    "worker_runtime_benchmark_contract_v0_1.yaml"
)
CONTRACT = (
    ROOT
    / "coordination/standards/automation/"
    "worker_runtime_adapter_registry_contract_v0_1.yaml"
)
CONFIG = ROOT / "config/worker_runtime.yaml"


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_contracts_preserve_provider_neutral_authority() -> None:
    registry_contract = load(CONTRACT)
    authority = registry_contract["authority"]
    assert all(value is False for value in authority.values())

    registry = load(REGISTRY)
    assert registry["worker_identity"]["provider_neutral"] is True
    assert registry["adapter_interface"]["architectural_authority"] is False


def test_benchmark_contract_keeps_human_acceptance() -> None:
    benchmark = load(BENCHMARK)
    assert benchmark["quality_facts"]["semantic_acceptance_is_automatic"] is False
    assert benchmark["human_review"]["required_before_provider_comparison_acceptance"] is True
    assert benchmark["human_review"]["score_is_authority"] is False


def test_reserved_providers_do_not_guess_runtime_details() -> None:
    registry = load(REGISTRY)
    rows = {
        row["provider_id"]: row
        for row in registry["providers"]
    }
    for provider_id in (
        "openai_codex_cli",
        "anthropic_claude_code",
        "xai_grok_cli",
    ):
        row = rows[provider_id]
        assert row["executable"] is None
        assert row["model_selection"] is None
        assert row["auth"] is None
        assert row["provenance"]["command_guessed"] is False
        assert row["provenance"]["model_guessed"] is False


def test_config_has_no_secret_material() -> None:
    text = CONFIG.read_text(encoding="utf-8").lower()
    forbidden_assignments = (
        "api_key:",
        "access_token:",
        "refresh_token:",
        "password:",
    )
    assert not any(token in text for token in forbidden_assignments)
