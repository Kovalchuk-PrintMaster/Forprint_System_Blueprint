from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")

def test_bootstrap_protocol_registered_in_both_indexes():
    root_index = read("coordination/standards/index.yaml")
    governance_index = read("coordination/standards/governance/index.yaml")
    assert "standard_id: new_module_bootstrap_protocol_v0_1" in root_index
    assert "file: governance/new_module_bootstrap_protocol_v0_1.md" in root_index
    assert "file: new_module_bootstrap_protocol_v0_1.md" in governance_index

def test_bootstrap_templates_and_reference_helper_exist():
    expected = [
        "coordination/standards/governance/new_module_bootstrap_protocol_v0_1.md",
        "tools/module_bootstrap/module_assistant_context.py",
        "coordination/templates/module_bootstrap/AGENTS.md.template",
        "coordination/templates/module_bootstrap/START_HERE.template.md",
        "coordination/templates/module_bootstrap/module_bootstrap_manifest.template.yaml",
        "coordination/templates/module_bootstrap/copilot-instructions.template.md",
        "coordination/templates/module_bootstrap/new_module_assistant_commissioning_prompt_v0_1.md",
    ]
    for rel in expected:
        assert (ROOT / rel).is_file(), rel

def test_make_continuity_targets_are_canonicalized():
    make_standard = read("coordination/standards/make_command_standard.md")
    target_contract = read("coordination/standards/module_make_target_contract.md")
    template = read("coordination/templates/module_makefile_standard.template.mk")
    for marker in ("assistant-handoff-check", "assistant-pack", "assistant-context-pack"):
        assert marker in make_standard
        assert marker in target_contract
        assert marker in template
    assert "MODULE_ONBOARD" in make_standard
    assert "MODULE_CONTEXT" in make_standard
    assert "MODULE_ONBOARD" in target_contract
    assert "MODULE_CONTEXT" in target_contract

def test_module_assistant_package_has_no_execution_authority():
    helper = read("tools/module_bootstrap/module_assistant_context.py")
    assert '"execution": False' in helper
    assert '"acceptance": False' in helper
    assert '"release": False' in helper
    assert '"cross_repository_write": False' in helper

def test_current_start_and_precommit_semantics():
    start = read("coordination/standards/module_assistant_start_protocol.md")
    precommit = read("coordination/standards/module_pre_commit_protocol.md")
    assert "make module-start" in start
    assert "Primary current startup command" in start
    assert "make module-validate" in precommit
    required = precommit.split("## Required pre-commit commands", 1)[1]
    required = required.split("Optional preview commands", 1)[0]

    command_blocks = re.findall(r"```(?:bash|text)?\n(.*?)```", required, flags=re.S)
    assert command_blocks
    commands_only = "\n".join(command_blocks)

    assert "blueprint-sync-directives" not in commands_only
    assert "blueprint-pull" not in commands_only

def test_clean_root_and_commission_surfaces_are_canonicalized():
    expected = [
        "coordination/standards/governance/clean_repository_root_policy_v0_1.yaml",
        "coordination/standards/governance/module_bootstrap_commission_contract_v0_1.yaml",
        "coordination/templates/module_bootstrap/module_bootstrap_commission_request.template.yaml",
        "tools/module_bootstrap/build_module_bootstrap_commission.py",
        "tests/test_module_bootstrap_commission_generator_v0_1.py",
    ]
    for rel in expected:
        assert (ROOT / rel).is_file(), rel

    helper = read("tools/module_bootstrap/module_assistant_context.py")
    assert 'DEFAULT_MODULE_MANIFEST = "coordination/module/manifest.yaml"' in helper
    assert "resolve_module_manifest_rel" in helper

    start_here = read("coordination/templates/module_bootstrap/START_HERE.template.md")
    assert "coordination/module/manifest.yaml" in start_here

    prompt = read(
        "coordination/templates/module_bootstrap/new_module_assistant_commissioning_prompt_v0_1.md"
    )
    assert "coordination/module/manifest.yaml" in prompt

    manifest_template = read(
        "coordination/templates/module_bootstrap/module_bootstrap_manifest.template.yaml"
    )
    assert "canonical_path: coordination/module/manifest.yaml" in manifest_template
    assert "root_compatibility_copy_forbidden: true" in manifest_template


def test_bootstrap_commission_is_distinct_from_module_onboard():
    contract = read(
        "coordination/standards/governance/module_bootstrap_commission_contract_v0_1.yaml"
    )
    assert "MODULE_BOOTSTRAP_COMMISSION" in contract
    assert "MODULE_ONBOARD" in contract
    assert "MODULE_CONTEXT" in contract
    assert "archive_creates_execution_authority: false" in contract
