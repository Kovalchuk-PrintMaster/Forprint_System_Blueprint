from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest
import yaml

from scripts.coordination import (
    build_context_bundle,
    build_document_manifest,
    run_inventory_acceptance_dry_run,
    validate_inventory_acceptance_evidence_index,
)

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = (
    ROOT
    / "coordination/internal_work/blueprint/governance/"
    "2026-08-03__blueprint__controlled_failure_write_flow_"
    "contract_v0_1.yaml"
)
RELEASE_POLICY = (
    ROOT
    / "coordination/standards/governance/"
    "outgoing_prompt_release_policy_v0_1.yaml"
)

EXPECTED_HASHES = {
    "scripts/coordination/build_context_bundle.py": (
        "f41b17d6347330f2c5b71c2b4fca4c52563e28d6f0857eb8c07b236757676de0"
    ),
    "scripts/coordination/build_document_manifest.py": (
        "bb56666df0cba827c84c4709af357e3878f5e3df1eeea7827dde90072b58e09f"
    ),
    "scripts/coordination/run_inventory_acceptance_dry_run.py": (
        "1583da3acf714491a9969e7915a9b45f1d78b7c203da4cfd675d977a00889c25"
    ),
    "scripts/coordination/validate_inventory_acceptance_evidence_index.py": (
        "3b4310b0268955bb2956ea18c64520b94c8a10bb9b1269f9754f77f80bf35941"
    ),
}


def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_controlled_failure_sources_are_exact() -> None:
    assert {
        path: _sha256(ROOT / path)
        for path in EXPECTED_HASHES
    } == EXPECTED_HASHES


def test_context_bundle_no_write_skips_writer(
    tmp_path: Path,
    monkeypatch,
) -> None:
    bundle = build_context_bundle.BundleResult(
        module="example_module",
        scope="bootstrap",
        generated_at="2026-08-03T00:00:00+00:00",
        document_count=1,
        content="# Bundle\n",
    )
    monkeypatch.setattr(
        build_context_bundle,
        "build_context_bundle",
        lambda **_: bundle,
    )

    def forbidden_writer(**_):
        raise AssertionError("writer must not run in --no-write mode")

    monkeypatch.setattr(
        build_context_bundle,
        "write_context_bundle",
        forbidden_writer,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_context_bundle.py",
            "--root",
            str(tmp_path),
            "--module",
            "example_module",
            "--no-write",
            "--no-color",
        ],
    )

    assert build_context_bundle.main() == 0
    assert list(tmp_path.rglob("*")) == []


def test_manifest_no_write_skips_writer(
    tmp_path: Path,
    monkeypatch,
) -> None:
    manifest = build_document_manifest.ManifestResult(
        schema_version="coordination_document_manifest_v0_1",
        generated_at="2026-08-03T00:00:00+00:00",
        source_registry="coordination/document_awareness/source_registry.yaml",
        document_count=0,
        warning_count=0,
        warnings=[],
        documents=[],
    )
    monkeypatch.setattr(
        build_document_manifest,
        "build_manifest",
        lambda *_: manifest,
    )

    def forbidden_writer(*_):
        raise AssertionError("writer must not run in --no-write mode")

    monkeypatch.setattr(
        build_document_manifest,
        "write_manifest_reports",
        forbidden_writer,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_document_manifest.py",
            "--root",
            str(tmp_path),
            "--no-write",
            "--no-color",
        ],
    )

    assert build_document_manifest.main() == 0
    assert list(tmp_path.rglob("*")) == []


def test_context_bundle_write_failure_is_bounded(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output_dir = tmp_path / "output"
    sibling = tmp_path / "preserve.txt"
    sibling.write_text("keep", encoding="utf-8")
    bundle = build_context_bundle.BundleResult(
        module="example_module",
        scope="bootstrap",
        generated_at="2026-08-03T00:00:00+00:00",
        document_count=1,
        content="# Bundle\n",
    )
    original_write_text = Path.write_text

    def fail_output(self: Path, *args, **kwargs):
        if self.parent == output_dir:
            raise OSError("injected bundle write failure")
        return original_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_output)

    with pytest.raises(
        OSError,
        match="injected bundle write failure",
    ):
        build_context_bundle.write_context_bundle(
            root=tmp_path,
            bundle=bundle,
            output_dir=output_dir,
        )

    assert sibling.read_text(encoding="utf-8") == "keep"
    assert list(output_dir.glob("*.md")) == []


def test_manifest_partial_output_is_rerunnable(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output_dir = tmp_path / "output"
    sibling = tmp_path / "preserve.txt"
    sibling.write_text("keep", encoding="utf-8")
    manifest = build_document_manifest.ManifestResult(
        schema_version="coordination_document_manifest_v0_1",
        generated_at="2026-08-03T00:00:00+00:00",
        source_registry="coordination/document_awareness/source_registry.yaml",
        document_count=0,
        warning_count=0,
        warnings=[],
        documents=[],
    )
    markdown_path = output_dir / "document_manifest.md"
    original_write_text = Path.write_text

    def fail_markdown(self: Path, *args, **kwargs):
        if self == markdown_path:
            raise OSError("injected manifest write failure")
        return original_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_markdown)

    with pytest.raises(
        OSError,
        match="injected manifest write failure",
    ):
        build_document_manifest.write_manifest_reports(
            manifest,
            output_dir,
        )

    json_path = output_dir / "document_manifest.json"
    assert json_path.is_file()
    assert not markdown_path.exists()
    assert sibling.read_text(encoding="utf-8") == "keep"

    monkeypatch.setattr(Path, "write_text", original_write_text)
    returned_json, returned_markdown = (
        build_document_manifest.write_manifest_reports(
            manifest,
            output_dir,
        )
    )

    assert returned_json == json_path
    assert returned_markdown == markdown_path
    assert json_path.is_file()
    assert markdown_path.is_file()
    assert sibling.read_text(encoding="utf-8") == "keep"


def test_dry_run_report_failure_propagates_and_reruns(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output = tmp_path / "reports/dry_run.yaml"
    report = {
        "schema_version": "inventory_acceptance_dry_run_report_v0_1",
        "metadata": {
            "result": "PASSED",
            "module_id": "forprint_system_blueprint",
            "external_rollout_state": "gated",
        },
        "summary": {
            "candidate_acceptance_performed": False,
            "dry_run_effects_applied": False,
        },
    }
    monkeypatch.setattr(
        run_inventory_acceptance_dry_run,
        "run_dry_run",
        lambda **_: report,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_inventory_acceptance_dry_run.py",
            "--index",
            "index.yaml",
            "--index-validation",
            "index-validation.yaml",
            "--rci",
            "rci.yaml",
            "--redm",
            "redm.yaml",
            "--closure",
            "closure.yaml",
            "--reconciliation",
            "reconciliation.yaml",
            "--authority-policy",
            "authority.yaml",
            "--plan",
            "plan.yaml",
            "--roadmap",
            "roadmap.yaml",
            "--queue",
            "queue.yaml",
            "--module",
            "forprint_system_blueprint",
            "--output",
            str(output),
        ],
    )
    original_write_text = Path.write_text

    def fail_output(self: Path, *args, **kwargs):
        if self == output:
            raise OSError("injected dry-run report failure")
        return original_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_output)

    with pytest.raises(
        OSError,
        match="injected dry-run report failure",
    ):
        run_inventory_acceptance_dry_run.main()

    assert not output.exists()
    assert report["summary"]["candidate_acceptance_performed"] is False
    assert report["summary"]["dry_run_effects_applied"] is False

    monkeypatch.setattr(Path, "write_text", original_write_text)
    output.parent.mkdir(parents=True, exist_ok=True)
    assert run_inventory_acceptance_dry_run.main() == 0
    assert yaml.safe_load(output.read_text(encoding="utf-8")) == report


def test_evidence_index_report_failure_propagates_and_reruns(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output = tmp_path / "reports/index_validation.yaml"
    report = {
        "schema_version": (
            "inventory_acceptance_evidence_index_"
            "validation_report_v0_1"
        ),
        "metadata": {
            "result": "PASSED",
            "module_id": "forprint_system_blueprint",
            "external_rollout_state": "gated",
        },
        "summary": {
            "candidate_acceptance_performed": False,
        },
        "errors": [],
    }
    monkeypatch.setattr(
        validate_inventory_acceptance_evidence_index,
        "validate_index",
        lambda **_: report,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "validate_inventory_acceptance_evidence_index.py",
            "--index",
            "index.yaml",
            "--repo-root",
            str(tmp_path),
            "--module",
            "forprint_system_blueprint",
            "--output",
            str(output),
        ],
    )
    original_write_text = Path.write_text

    def fail_output(self: Path, *args, **kwargs):
        if self == output:
            raise OSError("injected index report failure")
        return original_write_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_output)

    with pytest.raises(
        OSError,
        match="injected index report failure",
    ):
        validate_inventory_acceptance_evidence_index.main()

    assert not output.exists()
    assert report["summary"]["candidate_acceptance_performed"] is False

    monkeypatch.setattr(Path, "write_text", original_write_text)
    output.parent.mkdir(parents=True, exist_ok=True)
    assert validate_inventory_acceptance_evidence_index.main() == 0
    assert yaml.safe_load(output.read_text(encoding="utf-8")) == report


def test_evidence_closes_only_controlled_failure_group() -> None:
    evidence = _load(EVIDENCE)

    assert evidence["metadata"]["status"] == "verified_not_closed"
    assert evidence["per_flow_state"] == {
        "scripts_coordination_build_context_bundle_py": (
            "verified_controlled_failure"
        ),
        "scripts_coordination_build_document_manifest_py": (
            "verified_controlled_failure"
        ),
        "scripts_coordination_run_inventory_acceptance_dry_run_py": (
            "verified_controlled_failure"
        ),
        (
            "scripts_coordination_"
            "validate_inventory_acceptance_evidence_index_py"
        ): "verified_controlled_failure",
        "remaining_manual_blocker_count_after_this_evidence": 17,
    }

    state = evidence["blocker_state"]
    assert state["write_flow_recovery_not_fully_verified"] == "remains"
    assert state["closeout_eligible"] is False
    assert state["next_unresolved_groups"] == {
        "bounded_output_writers": 15,
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
