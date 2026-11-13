from __future__ import annotations

import importlib.util
import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = (
    ROOT
    / "scripts/validation/"
    "validate_blueprint_command_applicability.py"
)
REGISTRY = (
    ROOT
    / "coordination/standards/adoption/"
    "blueprint_command_applicability_v0_1.yaml"
)
TEMPLATE = (
    ROOT
    / "coordination/templates/"
    "module_makefile_standard.template.mk"
)


def _validator():
    spec = importlib.util.spec_from_file_location(
        "prompt_workflow_applicability_validator",
        VALIDATOR_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["make", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def test_current_prompt_workflow_applicability_passes() -> None:
    assert _validator().validate(ROOT) == []


def test_registry_marks_prompt_commands_implemented() -> None:
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    commands = {
        row["command_id"]: row
        for row in data["commands"]
    }

    prepare = commands["prompt-prepare"]
    release = commands["prompt-release"]

    assert prepare["target_present"] is True
    assert prepare["default_mode"] == "preview"
    assert prepare["conformance"] == "pass"

    assert release["target_present"] is True
    assert release["default_mode"] == "preview"
    assert release["release_policy_state"] == "gated"
    assert release["conformance"] == "pass"


def test_module_template_does_not_define_blueprint_mutations() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    targets = set(
        re.findall(
            r"^([A-Za-z0-9_.-]+):(?:\s|$)",
            text,
            flags=re.MULTILINE,
        )
    )

    assert "prompt-prepare" not in targets
    assert "prompt-release" not in targets
    assert (
        "Blueprint-owned prompt mutations "
        "(intentionally unavailable here):"
        in text
    )
    assert (
        "Approved files are inventory only; readiness "
        "comes from Prompt Queue v0.2."
        in text
    )


def test_prompt_prepare_requires_source() -> None:
    result = _make("prompt-prepare")

    assert result.returncode == 2
    assert "requires SOURCE=" in result.stdout


def test_prompt_prepare_rejects_invalid_apply() -> None:
    result = _make(
        "prompt-prepare",
        "SOURCE=operator_input/prompts/example.md",
        "APPLY=2",
    )

    assert result.returncode == 2
    assert "APPLY must be 0 or 1" in result.stdout


def test_prompt_release_requires_explicit_module() -> None:
    result = _make(
        "prompt-release",
        "PROMPT_ID=example_prompt_v0_1",
    )

    assert result.returncode == 2
    assert "requires explicit MODULE=" in result.stdout


def test_prompt_release_requires_prompt_id() -> None:
    result = _make(
        "prompt-release",
        "MODULE=forprint_library",
    )

    assert result.returncode == 2
    assert "requires PROMPT_ID=" in result.stdout


def test_make_dry_runs_include_explicit_mutation_flags() -> None:
    prepare = _make(
        "-n",
        "prompt-prepare",
        "SOURCE=operator_input/prompts/example.md",
        "APPLY=1",
        "REPLACE=1",
    )
    release = _make(
        "-n",
        "prompt-release",
        "MODULE=forprint_library",
        "PROMPT_ID=example_prompt_v0_1",
        "APPLY=1",
    )

    assert prepare.returncode == 0
    assert "manage_outgoing_prompt.py" in prepare.stdout
    assert "--apply" in prepare.stdout
    assert "--replace" in prepare.stdout

    assert release.returncode == 0
    assert "manage_outgoing_prompt.py" in release.stdout
    assert "--module" in release.stdout
    assert "--prompt-id" in release.stdout
    assert "--apply" in release.stdout
