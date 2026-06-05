from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STANDARDS = ROOT / "coordination" / "standards"


def _read_standard(name: str) -> str:
    return (STANDARDS / name).read_text(encoding="utf-8")


def test_project_structure_standard_exists() -> None:
    assert (STANDARDS / "project_structure_standard.md").exists()


def test_make_command_standard_exists() -> None:
    assert (STANDARDS / "make_command_standard.md").exists()


def test_testing_and_check_report_standard_exists() -> None:
    assert (STANDARDS / "testing_and_check_report_standard.md").exists()


def test_module_alignment_policy_exists() -> None:
    assert (STANDARDS / "module_alignment_policy.md").exists()


def test_project_structure_standard_mentions_core_directories() -> None:
    content = _read_standard("project_structure_standard.md")

    required_terms = [
        "coordination/",
        "docs/",
        "scripts/",
        "tests/",
        "reports/",
        "forprint_module_manifest.yaml",
    ]

    for term in required_terms:
        assert term in content


def test_make_command_standard_mentions_required_targets() -> None:
    content = _read_standard("make_command_standard.md")

    required_targets = [
        "make install",
        "make lint",
        "make lint-fix",
        "make test",
        "make check",
        "make check-report",
        "make status-report",
        "make blueprint-pull",
        "make blueprint-check",
        "make blueprint-sync-directives",
        "make coordination-check",
        "make coordination-fix",
        "make module-policy-check",
    ]

    for target in required_targets:
        assert target in content


def test_testing_standard_mentions_visual_report_statuses() -> None:
    content = _read_standard("testing_and_check_report_standard.md")

    required_terms = [
        "OK",
        "WARN",
        "DEFERRED",
        "FAILED",
        "green",
        "yellow",
        "red",
        "reports/<module>_check_report.json",
        "reports/<module>_check_report.md",
    ]

    for term in required_terms:
        assert term in content


def test_module_alignment_policy_defines_gradual_adoption() -> None:
    content = _read_standard("module_alignment_policy.md").casefold()

    required_terms = [
        "gradual",
        "safe",
        "test-backed",
        "blueprint-pull",
        "blueprint-check",
        "blueprint-sync-directives",
        "module_directives.active",
    ]

    for term in required_terms:
        assert term.casefold() in content


def test_standards_do_not_force_destructive_refactor() -> None:
    project_structure = _read_standard("project_structure_standard.md").casefold()
    alignment_policy = _read_standard("module_alignment_policy.md").casefold()

    assert "not a destructive refactor order" in project_structure
    assert "do not perform large structural rewrites" in alignment_policy
