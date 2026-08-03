from __future__ import annotations

import ast
import hashlib
import importlib
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
BLUEPRINT_UTILS = ROOT / "scripts/blueprint_utils.py"
SHARED_IO = (
    ROOT / "scripts/coordination/modules/_shared/io.py"
)
ARTIFACT_WRITER = ROOT / "scripts/reporting/artifact_writer.py"
ARTIFACT_WRITER_TEST = (
    ROOT / "tests/reporting/test_blueprint_compact_reporting.py"
)
EVIDENCE = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-03__blueprint__shared_writer_recovery_"
    "contract_v0_1.yaml"
)
RELEASE_POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "outgoing_prompt_release_policy_v0_1.yaml"
)

EXPECTED_HASHES = {
    "scripts/blueprint_utils.py": (
        "ec0561ab32cf870c53bee7612a7a72d839d677950e51befbdeccb44ce6b3ea11"
    ),
    "scripts/coordination/modules/_shared/io.py": (
        "25e3f9ff4a6d6f39c2e6b122e889fa6fa15070eceb2fc0a7bf6389f7b0e63eeb"
    ),
    "scripts/reporting/artifact_writer.py": (
        "9cb289a7eeb41230be2b2f2a6757f2db5bb3ea2612f0f56e786d476078a72cd2"
    ),
}


def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts = [func.attr]
        value = func.value
        while isinstance(value, ast.Attribute):
            parts.append(value.attr)
            value = value.value
        if isinstance(value, ast.Name):
            parts.append(value.id)
        return ".".join(reversed(parts))
    return ""


def test_reviewed_shared_writer_sources_are_exact() -> None:
    paths = {
        "scripts/blueprint_utils.py": BLUEPRINT_UTILS,
        "scripts/coordination/modules/_shared/io.py": SHARED_IO,
        "scripts/reporting/artifact_writer.py": ARTIFACT_WRITER,
    }

    assert {
        name: _sha256(path)
        for name, path in paths.items()
    } == EXPECTED_HASHES


def test_blueprint_write_text_is_target_bounded(
    tmp_path: Path,
) -> None:
    utils = importlib.import_module("scripts.blueprint_utils")
    target = tmp_path / "nested/result.txt"
    sibling = tmp_path / "preserve.txt"
    sibling.write_text("keep", encoding="utf-8")

    utils.write_text(target, "payload")

    assert target.read_text(encoding="utf-8") == "payload"
    assert sibling.read_text(encoding="utf-8") == "keep"
    assert sorted(
        path.relative_to(tmp_path).as_posix()
        for path in tmp_path.rglob("*")
        if path.is_file()
    ) == ["nested/result.txt", "preserve.txt"]


def test_shared_yaml_and_json_writers_are_target_bounded(
    tmp_path: Path,
) -> None:
    shared_io = importlib.import_module(
        "scripts.coordination.modules._shared.io"
    )
    yaml_path = tmp_path / "yaml/result.yaml"
    json_path = tmp_path / "json/result.json"
    sibling = tmp_path / "preserve.txt"
    sibling.write_text("keep", encoding="utf-8")

    shared_io.write_yaml(yaml_path, {"value": 1})
    shared_io.write_json(json_path, {"value": 2})

    assert yaml.safe_load(
        yaml_path.read_text(encoding="utf-8")
    ) == {"value": 1}
    assert (
        __import__("json").loads(
            json_path.read_text(encoding="utf-8")
        )
        == {"value": 2}
    )
    assert sibling.read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize(
    ("module_name", "function_name", "suffix", "payload"),
    [
        (
            "scripts.blueprint_utils",
            "write_text",
            "result.txt",
            "payload",
        ),
        (
            "scripts.coordination.modules._shared.io",
            "write_yaml",
            "result.yaml",
            {"value": 1},
        ),
        (
            "scripts.coordination.modules._shared.io",
            "write_json",
            "result.json",
            {"value": 1},
        ),
    ],
)
def test_shared_writer_failures_propagate_without_sibling_mutation(
    tmp_path: Path,
    monkeypatch,
    module_name: str,
    function_name: str,
    suffix: str,
    payload,
) -> None:
    module = importlib.import_module(module_name)
    function = getattr(module, function_name)
    target = tmp_path / "nested" / suffix
    sibling = tmp_path / "preserve.txt"
    sibling.write_text("keep", encoding="utf-8")

    original = Path.write_text

    def fail_target(self: Path, *args, **kwargs):
        if self == target:
            raise OSError("injected write failure")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_target)

    with pytest.raises(OSError, match="injected write failure"):
        function(target, payload)

    assert not target.exists()
    assert sibling.read_text(encoding="utf-8") == "keep"


def test_artifact_writer_is_report_path_only() -> None:
    text = ARTIFACT_WRITER.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(ARTIFACT_WRITER))

    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "write_report_artifacts"
    )

    calls = {
        _call_name(node)
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
    }
    string_literals = {
        node.value
        for node in ast.walk(function)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
    }

    assert any(name.endswith(".mkdir") for name in calls)
    assert any(name.endswith(".write_text") for name in calls)
    assert not any(
        name.startswith("subprocess.")
        for name in calls
    )
    assert not any(
        literal.startswith(("coordination/", "machine/"))
        for literal in string_literals
    )
    assert "reports" in text
    assert "diagnostics" in text


def test_artifact_writer_has_existing_tmp_path_contract_test() -> None:
    text = ARTIFACT_WRITER_TEST.read_text(encoding="utf-8")

    assert (
        "test_artifact_writer_creates_machine_human_and_full_reports"
        in text
    )
    assert "tmp_path" in text
    assert 'paths["json"]' in text
    assert 'paths["markdown"]' in text
    assert 'paths["full_log"]' in text


def test_evidence_closes_only_shared_primitive_review_items() -> None:
    evidence = _load(EVIDENCE)

    assert evidence["metadata"]["status"] == "verified_not_closed"
    assert evidence["per_flow_state"] == {
        "scripts_blueprint_utils_py": "verified_shared_primitive",
        "scripts_coordination_modules_shared_io_py": (
            "verified_shared_primitive"
        ),
        "scripts_reporting_artifact_writer_py": (
            "verified_shared_primitive"
        ),
        "remaining_manual_blocker_count_after_this_evidence": 21,
    }

    state = evidence["blocker_state"]
    assert state["write_flow_recovery_not_fully_verified"] == "remains"
    assert state["closeout_eligible"] is False
    assert state["next_unresolved_groups"] == {
        "bounded_output_writers": 15,
        "controlled_failure_flows": 4,
        "explicit_recovery_contract_flows": 2,
    }


def test_operational_boundaries_remain_gated() -> None:
    evidence = _load(EVIDENCE)
    boundaries = evidence["boundaries"]

    assert boundaries["operational_readiness"] == "blocked"
    assert boundaries["reference_pilot_migration_authorized"] is False
    assert boundaries["external_module_prompts_released"] is False
    assert boundaries["external_rollout"] == "gated"
    assert boundaries["production_logic_changed"] is False
    assert boundaries["cross_repository_writes"] is False
    assert boundaries["automatic_commit_push_or_merge"] is False

    policy = _load(RELEASE_POLICY)
    assert policy["release"]["global_enabled"] is False
    assert policy["release"]["authorized_modules"] == []
    assert policy["release"]["authorization_evidence"] is None
    assert policy["result"]["operational_state"] == "gated"
    assert policy["result"]["external_rollout"] == "gated"
