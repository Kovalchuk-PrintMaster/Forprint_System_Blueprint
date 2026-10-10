"""Focused, temporary-repo verification of long-term CF-10 evidence retention."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane.persist_worker_acceptance_evidence_v0_1 import (
    GateError, assemble, persist, verify_snapshot,
)


def git(root, *args):
    result = subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def write(root, name, raw):
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(raw)
    return p


def sha(data):
    return hashlib.sha256(data).hexdigest()


def yaml_bytes(value):
    return yaml.safe_dump(value, sort_keys=False).encode()


def fixture(tmp_path):
    repo = tmp_path / "repo"
    runtime = tmp_path / "worker-runtime"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test")
    write(repo, ".gitignore", b"tmp/\n")
    for name in ("Makefile", "scripts/validation/run_validation_suite_v0_1.py", "tests/validation/test_validation_suite_runner_v0_1.py"):
        write(repo, name, b"baseline\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "source")
    source_head = git(repo, "rev-parse", "HEAD")
    changed_paths = ["Makefile", "scripts/validation/run_validation_suite_v0_1.py", "tests/validation/test_validation_suite_runner_v0_1.py"]
    for name in changed_paths:
        write(repo, name, b"baseline\nworker change\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "worker")
    worker_commit = git(repo, "rev-parse", "HEAD")

    attempt = "cf10-u180j-a040"
    record_rel = Path("coordination/continuity/worker_result_decisions/decision.yaml")
    ledger_root = "coordination/continuity/execution_attempts"
    ledgers = {}
    for stage, state, validator in (("STARTED", "PENDING", "NOT_RUN"), ("FINISHED", "SUCCEEDED", "PASS")):
        name = f"{ledger_root}/{attempt}__{stage.lower()}.yaml"
        raw = yaml_bytes({"attempt_id": attempt, "attempt_stage": stage, "result_state": state,
                          "validator_outcome": validator})
        write(repo, name, raw)
        ledgers[stage] = (name, raw)
    work_front = write(repo, "coordination/work_fronts/original.yaml", b"work_front_id: original\n")
    run = runtime / attempt
    extra = {
        "worker_result": run / "result/worker_result.yaml",
        "result_return": run / "evidence/result_return.yaml",
        "operator_review": repo / "tmp/review.yaml",
        "exact_patch": repo / "tmp/delta.patch",
        "worker_baseline": run / "evidence/worker_baseline.yaml",
        "worker_manifest": run / "manifest.yaml",
        "workspace_candidate:Makefile": run / "workspace/repo/Makefile",
        "workspace_candidate:scripts/validation/run_validation_suite_v0_1.py": run / "workspace/repo/scripts/validation/run_validation_suite_v0_1.py",
        "workspace_candidate:tests/validation/test_validation_suite_runner_v0_1.py": run / "workspace/repo/tests/validation/test_validation_suite_runner_v0_1.py",
    }
    bindings = {}
    for key, path in extra.items():
        raw = (b"patch v1\n" if key == "exact_patch" else f"proof of {key}\n".encode())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        bindings[key] = {"path": str(path), "sha256": sha(raw)}
    bindings["terminal_ledger"] = {
        "path": str(repo / ledgers["FINISHED"][0]), "sha256": sha(ledgers["FINISHED"][1])}
    bindings["work_front"] = {"path": str(work_front), "sha256": sha(work_front.read_bytes())}
    for name in ("governed_worker_cycle_origin_handoff_manifest_v0_1.yaml",
                 "governed_worker_cycle_explicit_dispatch_decision_v0_1.yaml"):
        write(run, "input/" + name, f"source {name}\n".encode())
    decision = {
        "schema_version": "forprint_cf10_post_commit_worker_operator_decision_v0_1",
        "decision_id": "a040-accept", "decision": "ACCEPT", "attempt_id": attempt,
        "source_head": source_head, "reviewed_commit_sha": worker_commit,
        "review_binding_sha256": sha(b"review"),
        "exact_patch_sha256": bindings["exact_patch"]["sha256"],
        "candidate_promotion_reperformed": False, "publication_state": "NOT_ATTESTED",
        "changed_paths": changed_paths, "evidence_bindings": bindings,
    }
    write(repo, record_rel, yaml_bytes(decision))
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "governance")
    return repo, runtime, record_rel, extra, work_front, ledgers


def test_persist_and_verify_after_tmp_and_runtime_are_deleted(tmp_path):
    repo, runtime, decision_rel, extra, work_front, ledgers = fixture(tmp_path)
    dest, content, manifest = assemble(repo, runtime, decision_rel)
    assert len(manifest["bound_evidence"]) == 11
    assert len(manifest["supplemental_inputs"]) == 2
    assert len(content) == 12  # Nine untracked proofs + two supplemental inputs + manifest
    persist(repo, dest, content)
    result = verify_snapshot(repo, decision_rel)
    assert result["verification_independent_of_tmp_and_runtime"] is True
    import shutil
    shutil.rmtree(runtime)
    shutil.rmtree(repo / "tmp")
    # Even a changed working-tree work front must not rewrite the historic git-anchored proof.
    work_front.write_text("uncommitted future work front edit\n")
    (repo / ledgers["FINISHED"][0]).write_text("uncommitted future ledger corruption\n")
    verify_snapshot(repo, decision_rel)
    # Commit a later revision of a canonical referenced file; old snapshot still verifies.
    git(repo, "add", str(work_front.relative_to(repo)))
    git(repo, "commit", "-qm", "later work front revision")
    verify_snapshot(repo, decision_rel)
    with pytest.raises(GateError, match="content checksum mismatch"):
        copy_path = next(dest.glob("objects/worker_result.*"))
        copy_path.write_bytes(b"corrupted\n")
        verify_snapshot(repo, decision_rel)


def test_no_overwrite_or_silent_duplicate(tmp_path):
    repo, runtime, decision_rel, *_ = fixture(tmp_path)
    dest, content, _ = assemble(repo, runtime, decision_rel)
    persist(repo, dest, content)
    with pytest.raises(GateError, match="already exists"):
        persist(repo, dest, content)


def test_original_evidence_tamper_blocks_preflight(tmp_path):
    repo, runtime, decision_rel, extra, *_ = fixture(tmp_path)
    extra["exact_patch"].write_bytes(b"changed after acceptance\n")
    with pytest.raises(GateError, match="content checksum mismatch"):
        assemble(repo, runtime, decision_rel)


def test_embedded_private_key_blocks_preflight(tmp_path):
    repo, runtime, decision_rel, extra, *_ = fixture(tmp_path)
    raw = b"-----BEGIN OPENSSH PRIVATE KEY-----\nsensitive\n"
    extra["worker_result"].write_bytes(raw)
    # Independently of SHA binding, such a payload must not be persisted.
    with pytest.raises(GateError, match="possible credential/private key"):
        assemble(repo, runtime, decision_rel)
