from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "coordination" / "standards" / "current_status_extension_policy.md"


def test_current_status_extension_policy_exists() -> None:
    assert POLICY.exists()


def test_current_status_extension_policy_defines_boundary_meaning() -> None:
    content = POLICY.read_text(encoding="utf-8")

    assert "boundary = general Blueprint coordination contract" in content
    assert "boundaries = module-specific safety assertions" in content
    assert "validation = module-local validation/status evidence" in content


def test_current_status_extension_policy_preserves_module_specific_blocks() -> None:
    content = POLICY.read_text(encoding="utf-8").casefold()

    required_terms = [
        "must not delete unknown or module-specific keys",
        "preserve all module-specific blocks",
        "do not rewrite current_status.yaml from scratch",
        "only add or update required standard keys",
        "delete validation",
        "delete boundaries",
    ]

    for term in required_terms:
        assert term.casefold() in content


def test_current_status_extension_policy_lists_required_central_keys() -> None:
    content = POLICY.read_text(encoding="utf-8")

    required_keys = [
        "module_name",
        "module_status",
        "priority",
        "last_commit",
        "checks",
        "boundary",
        "recommended_next_step",
        "updated_at",
    ]

    for key in required_keys:
        assert key in content


def test_current_status_extension_policy_contains_operational_registry_example() -> None:
    content = POLICY.read_text(encoding="utf-8")

    expected_terms = [
        "client_card_preview",
        "production_api_added",
        "real_1c_sync_added",
        "warehouse_stock_truth_added",
    ]

    for term in expected_terms:
        assert term in content


def test_current_status_extension_policy_mentions_safe_merge_strategy() -> None:
    content = POLICY.read_text(encoding="utf-8").casefold()

    expected_terms = [
        "load existing current_status.yaml",
        "update only known central keys",
        "preserve every unknown key",
        "write the merged mapping back",
    ]

    for term in expected_terms:
        assert term in content
