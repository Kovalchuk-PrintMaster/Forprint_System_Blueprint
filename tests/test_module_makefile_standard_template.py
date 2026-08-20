from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "coordination" / "templates" / "module_makefile_standard.template.mk"

REQUIRED_BLOCKS = [
    "00 Environment / constants",
    "01 Help / navigation",
    "02 Operator entrypoints / Blueprint-first workflow",
    "03 Blueprint repository synchronization",
    "04 Blueprint instruction intake",
    "05 Blueprint standards and policies",
    "06 Blueprint outgoing prompts / prompt queue",
    "07 Blueprint document awareness",
    "08 Module coordination metadata",
    "09 Module governance / policy checks",
    "10 Module install / bootstrap",
    "11 Module environment / local configuration",
    "12 Runtime control / process lifecycle",
    "13 Infrastructure / local services",
    "14 Database / storage / migrations",
    "15 Data import / export / fixtures",
    "16 External adapters / sandbox integrations",
    "17 Local previews / operator workflows",
    "18 Observability / diagnostics / logs",
    "19 Syntax / formatting / lint",
    "20 Tests",
    "21 Validation / check reports",
    "22 Status reports / generated reports / cleanup",
    "23 Completion packet / prompt finalization",
    "24 Git / release / commit helpers",
    "90 Module-specific helpers",
]

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
    "coordination-sync-check",
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
    "prompt-notify",
    "prompt-read",
    "coordination-check",
    "coordination-fix",
    "roadmap-validate",
    "roadmap-dashboard",
    "roadmap-summary",
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
