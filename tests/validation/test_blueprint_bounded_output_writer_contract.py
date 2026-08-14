from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-03__blueprint__bounded_output_writer_"
    "contract_v0_1.yaml"
)
RELEASE_POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "outgoing_prompt_release_policy_v0_1.yaml"
)

SOURCE_HASHES = {'scripts/coordination/assess_repository_knowledge_freshness.py': '970e9a51eb4129014bde48d1b7e4be7318fe28a54da2e507763028e83b8fe206', 'scripts/coordination/audit_artifact_retention_consistency.py': 'b8a15ac9127659dd9b555c28202bbb7bc637a75d1ad49566aeda78948961f847', 'scripts/coordination/compare_repository_knowledge_snapshots.py': '86af0ce8add01eae43df65b3653086690b381253feede53976216be99c7915aa', 'scripts/coordination/render_repository_knowledge_coverage_dashboard.py': 'c595d24e7432c8335385f569fb1e5843e26ddc2508c32ccf4680cfd534edb015', 'scripts/coordination/validate_artifact_authority_policy.py': '3ed784658c4b34e96273b8df7f796e94162946c119635ffe82819d121d99aa0e', 'scripts/coordination/validate_blueprint_inventory_status_consistency.py': '954fd107234cf268e69f3fbacd02dfc3750ca86c2a228567dd6e9c9000e588dd', 'scripts/coordination/validate_blueprint_self_coordination.py': 'a76ccdee798b82d10eb5a73da5be6335bca90e1b6df6b3dc2d33b5abd557f1f6', 'scripts/coordination/validate_rci_semantic_enrichment.py': '5ed14c1c886275403d83f5771b2e1822b802049535455d15f233fed95f05272a', 'scripts/coordination/validate_redm_dependency_enrichment.py': 'd82db25fd69882e80a1ac5340f6a370c2c3dfdb29640499a6b82c475b747e811', 'scripts/coordination/validate_repository_knowledge_maintenance.py': '901c5d6758b8a020de4ac55bb977188c45cf17afd880209b1142f2433b48ac95', 'scripts/coordination/validate_repository_knowledge_reconciliation.py': 'bbc3b01d68a467a62a4bd93c070159aa5aa339d681093c8448a8428eaece3f53', 'scripts/coordination/validate_repository_knowledge_snapshot_comparisons.py': '3de7b300239688ee0aed7b21901ab306f5206352b4ca83362a38b813d1e09485', 'scripts/coordination/validate_semantic_coverage_closure.py': 'fb1d647a6ae87bedbd1842584ce49920f18221805399a70c1fbdcbe881d1c85b', 'scripts/generate_module_guides.py': '14e7ae69424ab9caabbb4152aafb98cf5b0251d8031f094129133ec06280e717', 'scripts/generate_module_policy_docs.py': '1779347ac37d678f4b88238d51b9a793234b599192980f787cc7455579acdab2'}

EXPECTED_MUTATIONS = {'scripts/coordination/assess_repository_knowledge_freshness.py': {'main': ['output.parent.mkdir', 'output.write_text']}, 'scripts/coordination/audit_artifact_retention_consistency.py': {'main': ['write_text']}, 'scripts/coordination/compare_repository_knowledge_snapshots.py': {'main': ['output.parent.mkdir', 'output.write_text']}, 'scripts/coordination/render_repository_knowledge_coverage_dashboard.py': {'main': ['markdown_output.parent.mkdir', 'markdown_output.write_text', 'yaml_output.parent.mkdir', 'yaml_output.write_text']}, 'scripts/coordination/validate_artifact_authority_policy.py': {'main': ['write_text']}, 'scripts/coordination/validate_blueprint_inventory_status_consistency.py': {'main': ['write_text']}, 'scripts/coordination/validate_blueprint_self_coordination.py': {'main': ['write_text']}, 'scripts/coordination/validate_rci_semantic_enrichment.py': {'main': ['write_text']}, 'scripts/coordination/validate_redm_dependency_enrichment.py': {'main': ['write_text']}, 'scripts/coordination/validate_repository_knowledge_maintenance.py': {'main': ['output.parent.mkdir', 'output.write_text']}, 'scripts/coordination/validate_repository_knowledge_reconciliation.py': {'main': ['write_text']}, 'scripts/coordination/validate_repository_knowledge_snapshot_comparisons.py': {'main': ['write_text'], 'validate_manifest': ['work_dir.mkdir']}, 'scripts/coordination/validate_semantic_coverage_closure.py': {'main': ['write_text']}, 'scripts/generate_module_guides.py': {'generate': ['write_text']}, 'scripts/generate_module_policy_docs.py': {'generate_docs': ['module_dir.mkdir', 'target.write_text']}}

DESTRUCTIVE_CALLS = {
    "os.remove",
    "os.rename",
    "os.replace",
    "os.unlink",
    "shutil.move",
    "shutil.rmtree",
    "Path.rename",
    "Path.replace",
    "Path.unlink",
}
MUTATION_LEAVES = {
    "mkdir",
    "write_text",
    "write_bytes",
}
GIT_MUTATION_VERBS = {
    "add",
    "commit",
    "push",
    "merge",
    "rebase",
    "reset",
    "checkout",
    "switch",
    "branch",
    "tag",
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


def _write_mode(node: ast.Call) -> str | None:
    name = _call_name(node)
    if name != "open" and not name.endswith(".open"):
        return None

    mode = None
    if len(node.args) >= 2:
        value = node.args[1]
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            mode = value.value
    for keyword in node.keywords:
        if keyword.arg == "mode":
            value = keyword.value
            if (
                isinstance(value, ast.Constant)
                and isinstance(value.value, str)
            ):
                mode = value.value
    return mode


def _function_mutations(tree: ast.Module) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}

    for function in tree.body:
        if not isinstance(
            function,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            continue

        calls: list[str] = []
        for node in ast.walk(function):
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node)
            leaf = name.rsplit(".", 1)[-1] if name else ""
            mode = _write_mode(node)
            if mode and any(flag in mode for flag in ("w", "a", "x", "+")):
                calls.append(f"open:{mode}")
            elif leaf in MUTATION_LEAVES:
                calls.append(name or leaf)

        if calls:
            result[function.name] = sorted(calls)

    return result


def _literal_command(node: ast.AST) -> list[str]:
    if not isinstance(node, (ast.List, ast.Tuple)):
        return []
    values: list[str] = []
    for item in node.elts:
        if isinstance(item, ast.Constant) and isinstance(item.value, str):
            values.append(item.value)
        else:
            return []
    return values


def test_sources_and_mutation_surfaces_are_exact() -> None:
    actual_hashes = {
        path: _sha256(ROOT / path)
        for path in SOURCE_HASHES
    }
    assert actual_hashes == SOURCE_HASHES

    actual_mutations = {}
    for path in SOURCE_HASHES:
        source = ROOT / path
        tree = ast.parse(
            source.read_text(encoding="utf-8"),
            filename=str(source),
        )
        actual_mutations[path] = _function_mutations(tree)

    assert actual_mutations == EXPECTED_MUTATIONS


def test_writers_use_overwrite_without_destructive_operations() -> None:
    for path in SOURCE_HASHES:
        source = ROOT / path
        tree = ast.parse(
            source.read_text(encoding="utf-8"),
            filename=str(source),
        )

        names = {
            _call_name(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
        }
        assert names.isdisjoint(DESTRUCTIVE_CALLS)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            mode = _write_mode(node)
            assert mode is None or "a" not in mode


def test_no_git_mutation_commands_are_present() -> None:
    for path in SOURCE_HASHES:
        source = ROOT / path
        tree = ast.parse(
            source.read_text(encoding="utf-8"),
            filename=str(source),
        )

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node)
            if name not in {
                "subprocess.run",
                "subprocess.check_call",
                "subprocess.check_output",
                "subprocess.Popen",
            }:
                continue
            if not node.args:
                continue

            command = _literal_command(node.args[0])
            if not command or command[0] != "git":
                continue
            assert GIT_MUTATION_VERBS.isdisjoint(command[1:])


def test_report_writers_expose_output_scope() -> None:
    generator_paths = {
        "scripts/generate_module_guides.py",
        "scripts/generate_module_policy_docs.py",
    }
    dashboard_path = (
        "scripts/coordination/"
        "render_repository_knowledge_coverage_dashboard.py"
    )

    for path in SOURCE_HASHES:
        text = (ROOT / path).read_text(encoding="utf-8")
        lowered = text.lower()

        if path in generator_paths:
            assert "generate" in lowered
            assert "write_text" in lowered
            continue

        if path == dashboard_path:
            assert "yaml_output" in text
            assert "markdown_output" in text
            continue

        assert any(
            token in text
            for token in (
                "--output",
                "output_path",
                "output_dir",
                "output =",
            )
        )


def test_generated_outputs_are_rebuildable_not_append_only() -> None:
    for path in SOURCE_HASHES:
        text = (ROOT / path).read_text(encoding="utf-8")
        tree = ast.parse(text, filename=path)

        write_text_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and _call_name(node).rsplit(".", 1)[-1] == "write_text"
        ]
        assert write_text_calls

        for call in write_text_calls:
            assert not any(
                keyword.arg == "append"
                for keyword in call.keywords
            )


def test_evidence_verifies_only_bounded_output_group() -> None:
    evidence = _load(EVIDENCE)

    assert evidence["metadata"]["status"] == "verified_not_closed"
    assert evidence["subject"]["flow_count"] == 15
    assert len(evidence["subject"]["flows"]) == 15
    assert evidence["per_flow_state"] == {
        "verified_bounded_output_writer_count": 15,
        "remaining_manual_blocker_count_after_this_evidence": 2,
    }

    state = evidence["blocker_state"]
    assert state["write_flow_recovery_not_fully_verified"] == "remains"
    assert state["closeout_eligible"] is False
    assert state["next_unresolved_group"] == {
        "explicit_recovery_contract_flows": 2
    }
    assert state["next_unresolved_paths"] == [
        (
            "scripts/coordination/modules/"
            "forprint_system_blueprint/workflows/self_audit.py"
        ),
        "scripts/validate_module_standards_template.py",
    ]


def test_operational_and_release_boundaries_remain_gated() -> None:
    evidence = _load(EVIDENCE)
    boundaries = evidence["boundaries"]

    assert boundaries["operational_readiness"] == "blocked"
    assert boundaries["reference_pilot_migration_authorized"] is False
    assert boundaries["external_module_prompts_released"] is False
    assert boundaries["external_rollout"] == "gated"
    assert boundaries["production_logic_changed"] is False
    assert boundaries["cross_repository_writes"] is False
    assert boundaries["automatic_commit_push_or_merge"] is False
    assert boundaries["historical_evidence_rewritten"] is False

    policy = _load(RELEASE_POLICY)
    assert policy["release"]["global_enabled"] is False
    assert policy["release"]["authorized_modules"] == []
    assert policy["release"]["authorization_evidence"] is None
    assert policy["result"]["operational_state"] == "gated"
    assert policy["result"]["external_rollout"] == "gated"
