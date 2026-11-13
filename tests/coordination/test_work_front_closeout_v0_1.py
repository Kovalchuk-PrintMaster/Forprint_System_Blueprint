from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.coordination import work_front_closeout_v0_1 as closeout


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True, stdout=subprocess.PIPE).stdout


def create(root: Path, relative: str, contents: bytes):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(contents)
    return path


@pytest.fixture
def repository(tmp_path, monkeypatch):
    root = tmp_path / "blueprint"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.email", "test@localhost")
    git(root, "config", "user.name", "Test")
    frontpath = "coordination/work_fronts/stage.yaml"
    frontdata = {"work_front_id": "wf-stage", "acceptance": ["criterion one", "criterion two"]}
    create(root, frontpath, yaml.safe_dump(frontdata).encode())
    prodpath = "scripts/coordination/runtime.py"
    create(root, prodpath, b"VALUE = 1\n")
    git(root, "add", ".")
    git(root, "commit", "-qm", "setup")
    head = git(root, "rev-parse", "HEAD").decode().strip()
    logs = {}
    for key, count in zip(closeout.VERIFICATION_KEYS, (9, 3, 2, 0, 1)):
        path = f"tmp/{key}.log"
        payload = f"{key} PASS\n".encode()
        create(root, path, payload)
        logs[key] = {"result": "PASS", "log_path": path, "log_sha256": sha(payload), "test_executions": count}
    evidence = {
        "report_kind": "local_validation_evidence_candidate",
        "schema_version": closeout.STAGE4C_SCHEMA,
        "status": closeout.EXPECTED_EVIDENCE_STATUS,
        "work_front_id": "wf-stage",
        "work_front_path": frontpath,
        "operator_authorization": {"roadmap_or_ledger_mutation": False, "dispatch": False, "commit_or_push": False},
        "source_state": {
            "work_front_sha256": closeout._hash(root / frontpath),
            "file_sha256": {prodpath: closeout._hash(root / prodpath)},
            "head": head,
            "staged_diff_sha256": sha(b""),
        },
        "verification": logs,
        "test_execution_count": 15,
        "implementation": {"live_worker_executed_by_this_report": False},
    }
    evidencepath = "tmp/evidence.json"
    create(root, evidencepath, json.dumps(evidence).encode())
    monkeypatch.setattr(closeout, "_read_front", lambda _root, _front: frontdata)
    return root, frontpath, evidencepath


def plan(repository, *, forbidden_attempt=None):
    root, front, evidence = repository
    return closeout.make_plan(root, front, evidence, forbidden_attempt=forbidden_attempt)


def test_positive_plan_and_evidence_identity(repository):
    result = plan(repository)
    assert result["status"] == "READY_FOR_OPERATOR_ACCEPTANCE_REVIEW"
    assert result["completion_evidence"]["verified_test_executions"] == 15
    assert all(row["operator_attestation"] == "PENDING_MANUAL_REVIEW" for row in result["acceptance_review"])
    assert result["authority"]["canonical_write_allowed"] is False


def test_idempotent_create_only_plan(repository):
    root, *_ = repository
    a = plan(repository)
    first = closeout.write_plan(root, a, "closeout.json")
    assert closeout.write_plan(root, a, "closeout.json") == first
    assert first.read_bytes() == closeout._canonical_json(a)
    with pytest.raises(closeout.CloseoutError, match="PLAN_EXISTS_WITH_DIFFERENT_BYTES"):
        closeout.write_plan(root, {"different": True}, "closeout.json")


def test_refuse_tampered_evidence_log(repository):
    root, *_ = repository
    (root / "tmp/focused.log").write_text("tampered", encoding="utf-8")
    with pytest.raises(closeout.CloseoutError, match="SHA_MISMATCH"):
        plan(repository)


def test_refuse_source_drift(repository):
    root, *_ = repository
    (root / "scripts/coordination/runtime.py").write_text("changed", encoding="utf-8")
    with pytest.raises(closeout.CloseoutError, match="SHA_MISMATCH"):
        plan(repository)


def test_refuse_staging_drift(repository):
    root, *_ = repository
    create(root, "staged.txt", b"staged")
    git(root, "add", "staged.txt")
    with pytest.raises(closeout.CloseoutError, match="STAGING_DRIFT"):
        plan(repository)


def test_refuse_forbidden_attempt(repository):
    root, *_ = repository
    (root / "coordination/continuity/execution_attempts").mkdir(parents=True)
    create(root, "coordination/continuity/execution_attempts/cf10-u180j-a042__x.yaml", b"x")
    with pytest.raises(closeout.CloseoutError, match="FORBIDDEN_ATTEMPT_EXISTS"):
        plan(repository, forbidden_attempt="cf10-u180j-a042")


def test_accept_no_forbidden_attempt(repository):
    root, *_ = repository
    (root / "coordination/continuity/execution_attempts").mkdir(parents=True)
    assert plan(repository, forbidden_attempt="cf10-u180j-a042")["forbidden_attempt"]["absence_in_repo_at_plan"]


def test_refuse_evidence_front_id_drift(repository):
    root, _, evidencepath = repository
    f = root / evidencepath
    data = json.loads(f.read_text())
    data["work_front_id"] = "different"
    f.write_text(json.dumps(data))
    with pytest.raises(closeout.CloseoutError, match="EVIDENCE_WORK_FRONT_MISMATCH"):
        plan(repository)


def test_refuse_authority_widening(repository):
    root, _, evidencepath = repository
    f = root / evidencepath
    data = json.loads(f.read_text())
    data["operator_authorization"]["dispatch"] = True
    f.write_text(json.dumps(data))
    with pytest.raises(closeout.CloseoutError, match="EVIDENCE_DISPATCH_WIDENED"):
        plan(repository)


def test_reject_outside_root(repository):
    root, *_ = repository
    with pytest.raises(closeout.CloseoutError, match="FILE_OUTSIDE_ROOT"):
        closeout._repo_file(root, "../escape.yaml")


def test_check_detects_stale_plan(repository):
    root, front, evidence = repository
    assert closeout.main(["--root", str(root), "--front", front, "--evidence", evidence,
                          "--action", "plan", "--plan-name", "plan.json"]) == 0
    create(root, "new-untracked", b"later changed")
    assert closeout.main(["--root", str(root), "--front", front, "--evidence", evidence,
                          "--action", "check", "--plan-name", "plan.json"]) == 2


def test_no_production_mutation(repository):
    root, front, evidence = repository
    head = git(root, "rev-parse", "HEAD")
    before = closeout._hash(root / front)
    assert closeout.main(["--root", str(root), "--front", front, "--evidence", evidence,
                          "--action", "plan", "--plan-name", "plan.json"]) == 0
    assert git(root, "rev-parse", "HEAD") == head
    assert closeout._hash(root / front) == before
    assert not (root / "coordination/internal_work/blueprint/governance").exists()
