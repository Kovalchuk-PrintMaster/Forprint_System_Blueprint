from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "coordination" / "templates" / "module_makefile_standard.template.mk"

REQUIRED_BLOCKS = (
    "00 Environment / constants",
    "01 Help / navigation",
    "02 Install / bootstrap",
    "03 Project lifecycle",
    "04 Local runtime services",
    "05 Monitors / workers / background services",
    "06 Syntax / formatting / lint",
    "07 Tests",
    "08 Validation / check reports",
    "09 Status / generated reports / cleanup",
    "10 Blueprint integration",
    "11 Blueprint instruction intake",
    "12 Blueprint standards",
    "13 Blueprint outgoing prompts",
    "14 Coordination metadata",
    "15 Module policy / governance",
    "16 Completion packet / prompt finalization",
    "17 Local data / fixtures / migrations",
    "18 Local previews / operator workflows",
    "19 External adapters / sandbox integrations",
    "20 Observability / diagnostics",
    "21 Git / release / commit helpers",
    "90 Module-specific helpers",
)

REQUIRED_TARGETS = (
    "help",
    "install",
    "start",
    "stop",
    "restart",
    "services-start",
    "services-stop",
    "monitors-start",
    "monitors-stop",
    "lint",
    "lint-fix",
    "test",
    "check",
    "check-report",
    "status-report",
    "report-clean",
    "blueprint-pull",
    "blueprint-check",
    "blueprint-sync-directives",
    "blueprint-sync",
    "blueprint-instruction-list",
    "blueprint-instruction-check",
    "blueprint-instruction-sync",
    "blueprint-instruction",
    "blueprint-standards-list",
    "blueprint-standards-check",
    "blueprint-standards-sync",
    "blueprint-standards",
    "blueprint-prompts-list",
    "blueprint-prompts-check",
    "blueprint-prompts-sync",
    "blueprint-prompts",
    "prompt-read",
    "coordination-check",
    "coordination-fix",
    "module-policy-check",
    "governance-check",
    "completion-packet-validate",
    "completion-packet-apply",
    "completion-packet-check",
    "data-fixtures",
    "migrate",
    "preview",
    "adapters-sandbox-check",
    "diagnostics",
    "git-status",
    "pre-commit",
    "module-start",
    "module-sync",
    "module-validate",
    "module-finish",
)

COMPOSITE_TARGETS = (
    "restart",
    "blueprint-sync",
    "blueprint-instruction",
    "blueprint-standards",
    "blueprint-prompts",
    "governance-check",
    "completion-packet-check",
    "pre-commit",
    "module-start",
    "module-sync",
    "module-validate",
    "module-finish",
)


def _template_text() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def _target_pattern(target: str) -> re.Pattern[str]:
    return re.compile(rf"^{re.escape(target)}:", re.MULTILINE)


def _phony_pattern(target: str) -> re.Pattern[str]:
    return re.compile(rf"^\.PHONY:\s+{re.escape(target)}$", re.MULTILINE)


def test_module_makefile_standard_template_exists() -> None:
    assert TEMPLATE.exists()


def test_module_makefile_standard_template_has_visual_blocks() -> None:
    text = _template_text()

    for block in REQUIRED_BLOCKS:
        assert f"# {block} START" in text
        assert f"# {block} FINISH" in text

    assert "# =============================================================================" in text


def test_module_makefile_standard_template_has_required_targets() -> None:
    text = _template_text()

    for target in REQUIRED_TARGETS:
        assert _phony_pattern(target).search(text), target
        assert _target_pattern(target).search(text), target


def test_module_makefile_standard_template_documents_targets() -> None:
    text = _template_text()

    assert text.count("# Purpose:") >= len(REQUIRED_TARGETS)
    assert text.count("# Result:") >= len(REQUIRED_TARGETS)


def test_module_makefile_standard_template_has_composite_targets() -> None:
    text = _template_text()

    for target in COMPOSITE_TARGETS:
        match = re.search(
            rf"^{re.escape(target)}:\n(?P<body>(?:\t.*\n)+)",
            text,
            re.MULTILINE,
        )
        assert match is not None, target
        assert "$(MAKE)" in match.group("body"), target


def test_module_makefile_standard_template_has_optional_colors() -> None:
    text = _template_text()

    assert "COLOR_GREEN" in text
    assert "COLOR_YELLOW" in text
    assert "COLOR_RED" in text
    assert "NO_COLOR" in text


def test_module_makefile_standard_template_uses_blueprint_root() -> None:
    text = _template_text()

    assert "BLUEPRINT_ROOT" in text
    assert "$(BLUEPRINT_ROOT)" in text


def test_module_makefile_standard_template_has_packet_guard() -> None:
    text = _template_text()

    assert 'PACKET is required' in text
    assert 'test -n "$(PACKET)"' in text
