"""Self-contained, synthetic CF-10 post-commit decisions; never use live a040 evidence."""
from __future__ import annotations

import difflib
import hashlib
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane import post_commit_worker_acceptance as pc


def h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_yaml(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def run(root: Path, *cmd):
    return subprocess.run(list(cmd), cwd=root, capture_output=True, check=True).stdout


def make_demo(tmp_path, *, dirty_makefile=False):
    root = tmp_path / "canonical"
    root.mkdir()
    run(root, "git", "init", "-q")
    run(root, "git", "config", "user.email", "unit@example.test")
    run(root, "git", "config", "user.name", "CF10 Test")
    paths = ["Makefile", "scripts/validation/runner.py", "tests/validation/test_runner.py"]
    for i, path in enumerate(paths):
        f = root / path
        f.parent.mkdir(parents=True, exist_ok=True)
        if dirty_makefile and path == "Makefile":
            f.write_text("old0\n" + "untouched section\n" * 10 +
                         "validation suite: before\n" + "trailer\n" * 10,
                         encoding="utf-8")
        else:
            f.write_text(f"old{i}\n", encoding="utf-8")
    run(root, "git", "add", ".")
    run(root, "git", "commit", "-qm", "origin")
    base = run(root, "git", "rev-parse", "HEAD").decode().strip()
    original_bytes = {path: (root / path).read_bytes() for path in paths}
    if dirty_makefile:
        dirty_preimage = original_bytes["Makefile"] + b"operator existing edit\n"
        candidate_makefile = dirty_preimage.replace(
            b"validation suite: before", b"validation suite: after"
        )
        candidate_bytes = {
            "Makefile": candidate_makefile,
            paths[1]: b"old1\nnew1\n",
            paths[2]: b"old2\nnew2\n",
        }
        dirty_old = dict(original_bytes, Makefile=dirty_preimage)
        parts = []
        for path in paths:
            parts.append("".join(difflib.unified_diff(
                dirty_old[path].decode().splitlines(keepends=True),
                candidate_bytes[path].decode().splitlines(keepends=True),
                fromfile=f"a/{path}", tofile=f"b/{path}",
            )))
        patch = "\n".join(parts).encode()
        # Apply the reviewed Worker-only diff to source HEAD, excluding inherited edits.
        cp = subprocess.run(["git", "apply", "--whitespace=error", "-"], cwd=root,
                            input=patch, capture_output=True, check=False)
        assert cp.returncode == 0, cp.stderr
    else:
        for i, path in enumerate(paths):
            (root / path).write_text(f"old{i}\nnew{i}\n", encoding="utf-8")
        patch = run(root, "git", "diff", "--binary", "--", *paths)
        candidate_bytes = {path: (root / path).read_bytes() for path in paths}
    patch_path = root / "tmp" / "approved.patch"
    patch_path.parent.mkdir()
    patch_path.write_bytes(patch)
    run(root, "git", "add", "--", *paths)
    run(root, "git", "commit", "-qm", "worker")
    commit = run(root, "git", "rev-parse", "HEAD").decode().strip()
    attempt = "cf10-test-a001"
    worker_id = "worker-01"
    wf_id = "wf-cf10-example"
    runtime = tmp_path / "runtime"
    attempt_dir = runtime / "forprint_system_blueprint" / worker_id / attempt
    workspace = attempt_dir / "workspace" / "repo"
    for path in paths:
        target = workspace / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(candidate_bytes[path])
    write_yaml(attempt_dir / "manifest.yaml", {
        "attempt_id": attempt, "source_head": base, "workspace_repo": str(workspace)
    })
    write_yaml(attempt_dir / "evidence" / "worker_baseline_v0_1.yaml", {
        "source_head": base,
        "baseline_path_snapshots": ({
            "Makefile": {"kind": "file", "sha256": h(dirty_preimage)}
        } if dirty_makefile else {}),
    })
    result_path = attempt_dir / "result" / "worker_result.yaml"
    evidence_path = attempt_dir / "evidence" / "governed_worker_cycle_result_return_v0_1.yaml"
    manifest_hash = "a" * 64
    write_yaml(result_path, {
        "schema_version": "forprint_assistant_handoff_v2_result_v0_1",
        "attempt_id": attempt, "status": "COMPLETED", "changed_paths": paths,
        "handoff_manifest_sha256": manifest_hash,
        "resume_coordinates": {"attempt_id": attempt},
        "unresolved_findings": [],
        "validation_evidence": [{"kind": "normal_validation", "return_code": 0}],
    })
    write_yaml(evidence_path, {
        "attempt_id": attempt, "result": "PASS", "validation_passed": True,
        "blocked": False, "result_path": str(result_path),
        "candidate_promotion_allowed": False,
        "automatic_accept_allowed": False,
        "commit_allowed": False, "push_allowed": False, "release_allowed": False,
    })
    write_yaml(root / pc.LEDGER_REL / f"{attempt}__terminal.yaml", {
        "attempt_id": attempt, "work_front_id": wf_id,
        "attempt_stage": "FINISHED", "result_state": "SUCCEEDED",
        "validator_outcome": "PASS", "pack_hash_or_context_hash": manifest_hash,
        "result_refs": [str(result_path)], "validator_evidence_refs": [str(evidence_path)],
    })
    write_yaml(root / pc.WORK_FRONTS_REL / "example.yaml", {
        "work_front_id": wf_id, "scope": paths,
        "authority": {"layer": "WORK_FRONT"},
    })
    write_yaml(root / pc.CONTRACT_REL, {
        "schema_version": "forprint_cf10_post_commit_worker_result_acceptance_contract_v0_1",
        "authority_boundaries": {s: False for s in (
            "automatic_accept", "replay_candidate_promotion", "automatic_commit",
            "automatic_push", "rewrite_attempt_ledger")},
    })
    review_path = root / "tmp" / "operator_review.yaml"
    rows = []
    for path in paths:
        rows.append({"path": path,
                     "canonical_sha256": h(dirty_preimage) if dirty_makefile and path == "Makefile"
                         else h(run(root, "git", "show", f"{base}:{path}")),
                     "candidate_sha256": h(candidate_bytes[path])})
    write_yaml(review_path, {
        "attempt_id": attempt, "worker_delta_exact": True,
        "terminal": "FINISHED/SUCCEEDED/PASS", "candidate_promoted": False,
        "worker_changed_paths": paths, "files": rows,
        "inherited_dirty_paths": ["Makefile"] if dirty_makefile else [],
    })
    request = {
        "schema_version": "forprint_cf10_post_commit_acceptance_request_v0_1",
        "attempt_id": attempt, "work_front_id": wf_id, "worker_id": worker_id,
        "runtime_root": str(runtime), "source_head": base,
        "commit_sha": commit, "patch_file": "tmp/approved.patch",
        "patch_sha256": h(patch), "review_file": "tmp/operator_review.yaml",
        "changed_paths": paths,
    }
    write_yaml(root / "tmp" / "request.yaml", request)
    return {"root": root, "request": request, "commit": commit,
            "attempt": attempt, "result_path": result_path, "evidence_path": evidence_path,
            "attempt_dir": attempt_dir}


@pytest.fixture
def demo(tmp_path):
    return make_demo(tmp_path)


@pytest.fixture
def dirty_demo(tmp_path):
    return make_demo(tmp_path, dirty_makefile=True)


def preview(demo):
    return pc.validate_report(demo["root"], demo["request"])


def approve(demo, decision="ACCEPT", decision_id="test-a001-accept", supersedes=None):
    report = preview(demo)
    confirm = f"{decision}:{demo['attempt']}:{demo['commit'][:12]}"
    return pc.decide(demo["root"], report, decision, decision_id, "operator-test", confirm, supersedes)


def test_preview_is_read_only(demo):
    before = sorted(p.as_posix() for p in demo["root"].rglob("*"))
    result = preview(demo)
    assert result["state"] == "READY_FOR_EXPLICIT_OPERATOR_DECISION"
    assert result["operator_acceptance_recorded"] is False
    assert result["reviewed_commit_exact_patch"] == "PASS"
    assert sorted(p.as_posix() for p in demo["root"].rglob("*")) == before


def test_explicit_accept_is_one_record_and_no_git_action(demo):
    oldhead = run(demo["root"], "git", "rev-parse", "HEAD")
    result = approve(demo)
    assert result["status"] == "RECORDED_LOCAL_APPEND_ONLY"
    record = yaml.safe_load(Path(result["record"]).read_text())
    assert record["decision"] == "ACCEPT"
    assert record["candidate_promotion_reperformed"] is False
    assert record["push_performed"] is False
    assert record["publication_state"] == "NOT_ATTESTED"
    assert run(demo["root"], "git", "rev-parse", "HEAD") == oldhead
    assert run(demo["root"], "git", "diff", "--cached", "--name-only") == b""
    assert approve(demo)["status"] == "ALREADY_RECORDED"
    assert len(list((demo["root"] / pc.DECISIONS_REL).glob("*.yaml"))) == 1


def test_confirmation_is_mandatory(demo):
    with pytest.raises(pc.DecisionError, match="explicit confirmation"):
        pc.decide(demo["root"], preview(demo), "ACCEPT", "id", "operator", "yes")
    assert not (demo["root"] / pc.DECISIONS_REL).exists()


def test_conflicting_operator_decision_blocked(demo):
    approve(demo)
    with pytest.raises(pc.DecisionError, match="terminal decision already"):
        approve(demo, decision="RETURN", decision_id="return-different")


def test_hold_can_be_explicitly_superseded_once(demo):
    approve(demo, decision="HOLD", decision_id="hold-a001")
    with pytest.raises(pc.DecisionError, match="supersede HOLD"):
        approve(demo)
    assert approve(demo, supersedes="hold-a001")["status"] == "RECORDED_LOCAL_APPEND_ONLY"
    with pytest.raises(pc.DecisionError, match="terminal decision"):
        approve(demo, decision="RETURN", decision_id="again")


def test_patch_digest_mismatch_blocks(demo):
    demo["request"]["patch_sha256"] = "0" * 64
    with pytest.raises(pc.DecisionError, match="patch SHA-256"):
        preview(demo)


def test_commit_scope_mismatch_blocks(demo):
    demo["request"]["changed_paths"] = demo["request"]["changed_paths"][:2]
    with pytest.raises(pc.DecisionError, match="changed paths mismatch"):
        preview(demo)


def test_result_tampering_blocks(demo):
    data = yaml.safe_load(demo["result_path"].read_text())
    data["unresolved_findings"] = ["test-drift"]
    write_yaml(demo["result_path"], data)
    with pytest.raises(pc.DecisionError, match="unresolved Worker"):
        preview(demo)


def test_review_hash_mismatch_blocks(demo):
    path = demo["root"] / "tmp" / "operator_review.yaml"
    data = yaml.safe_load(path.read_text())
    data["files"][0]["candidate_sha256"] = "f" * 64
    write_yaml(path, data)
    with pytest.raises(pc.DecisionError, match="review final hash mismatch"):
        preview(demo)


def test_head_drift_blocks(demo):
    (demo["root"] / "new.txt").write_text("later\n")
    run(demo["root"], "git", "add", "new.txt")
    run(demo["root"], "git", "commit", "-qm", "after")
    with pytest.raises(pc.DecisionError, match="canonical HEAD no longer"):
        preview(demo)


def test_missing_work_front_blocks(demo):
    (demo["root"] / pc.WORK_FRONTS_REL / "example.yaml").unlink()
    with pytest.raises(pc.DecisionError, match="work front id must resolve"):
        preview(demo)


def test_unrelated_worktree_dirty_preserved(demo):
    (demo["root"] / "unrelated.txt").write_text("untouched")
    before = (demo["root"] / "unrelated.txt").read_bytes()
    approve(demo)
    assert (demo["root"] / "unrelated.txt").read_bytes() == before


def test_result_return_authority_widening_blocks(demo):
    data = yaml.safe_load(demo["evidence_path"].read_text())
    data["push_allowed"] = True
    write_yaml(demo["evidence_path"], data)
    with pytest.raises(pc.DecisionError, match="authority was widened"):
        preview(demo)


def test_preview_reads_existing_accept_without_second_record(demo):
    approve(demo)
    report = preview(demo)
    assert report["state"] == "EXISTING_OPERATOR_DECISION"
    assert report["operator_acceptance_recorded"] is True
    assert len(report["operator_decision_records"]) == 1
    assert len(list((demo["root"] / pc.DECISIONS_REL).glob("*.yaml"))) == 1


def test_same_decision_id_on_other_attempt_blocked(demo):
    directory = demo["root"] / pc.DECISIONS_REL
    write_yaml(directory / "test-a001-accept__collision.yaml", {
        "attempt_id": "other-attempt", "decision_id": "test-a001-accept",
        "decision": "ACCEPT",
    })
    with pytest.raises(pc.DecisionError, match="different attempt"):
        approve(demo)


def test_dirty_baseline_review_and_exact_commit_pass_independently(dirty_demo):
    report = preview(dirty_demo)
    assert report["state"] == "READY_FOR_EXPLICIT_OPERATOR_DECISION"
    assert report["review_baseline_modes"] == {
        "Makefile": "FROZEN_DIRTY_BASELINE",
        "scripts/validation/runner.py": "SOURCE_HEAD",
        "tests/validation/test_runner.py": "SOURCE_HEAD",
    }
    assert report["reviewed_commit_exact_patch"] == "PASS"
    assert approve(dirty_demo)["status"] == "RECORDED_LOCAL_APPEND_ONLY"


def test_dirty_baseline_snapshot_tamper_blocks(dirty_demo):
    path = dirty_demo["attempt_dir"] / "evidence" / "worker_baseline_v0_1.yaml"
    content = yaml.safe_load(path.read_text())
    content["baseline_path_snapshots"]["Makefile"]["sha256"] = "0" * 64
    write_yaml(path, content)
    with pytest.raises(pc.DecisionError, match="frozen dirty-baseline mismatch"):
        preview(dirty_demo)


def test_dirty_workspace_candidate_tamper_blocks(dirty_demo):
    path = dirty_demo["attempt_dir"] / "workspace" / "repo" / "Makefile"
    path.write_bytes(path.read_bytes() + b"injected malicious change\n")
    with pytest.raises(pc.DecisionError, match="review final hash mismatch"):
        preview(dirty_demo)


def test_dirty_review_must_declare_inherited_makefile(dirty_demo):
    path = dirty_demo["root"] / "tmp" / "operator_review.yaml"
    content = yaml.safe_load(path.read_text())
    content["inherited_dirty_paths"] = []
    write_yaml(path, content)
    with pytest.raises(pc.DecisionError, match="unlisted inherited dirty Worker path"):
        preview(dirty_demo)


def test_dirty_review_canonical_hash_tamper_blocks(dirty_demo):
    path = dirty_demo["root"] / "tmp" / "operator_review.yaml"
    content = yaml.safe_load(path.read_text())
    content["files"][0]["canonical_sha256"] = "f" * 64
    write_yaml(path, content)
    with pytest.raises(pc.DecisionError, match="review source hash mismatch"):
        preview(dirty_demo)
