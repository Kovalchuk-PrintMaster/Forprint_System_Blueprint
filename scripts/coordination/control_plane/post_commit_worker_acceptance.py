"""CF-10 post-commit operator decision, distinct from promotion and publication.

PREVIEW is read-only. DECIDE requires an explicit separate human confirmation,
revalidates the same immutable evidence, and creates one append-only record.
Neither operation stages, commits, pushes, promotes or rewrites the attempt ledger.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

CONTRACT_REL = "coordination/standards/automation/cf10_post_commit_worker_result_acceptance_contract_v0_1.yaml"
DECISIONS_REL = "coordination/continuity/worker_result_decisions"
LEDGER_REL = "coordination/continuity/execution_attempts"
WORK_FRONTS_REL = "coordination/work_fronts"
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}$")
SHA_PATTERN = re.compile(r"^[a-f0-9]{64}$")
GIT_OID_PATTERN = re.compile(r"^(?:[a-f0-9]{40}|[a-f0-9]{64})$")
DECISIONS = {"ACCEPT", "RETURN", "HOLD"}

class DecisionError(RuntimeError):
    """Fail-closed acceptance gate error."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise DecisionError(reason)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def yaml_file(path: Path, label: str) -> dict[str, Any]:
    require(path.is_file(), f"missing {label}: {path}")
    value = yaml.safe_load(path.read_bytes())
    require(isinstance(value, dict), f"invalid {label}: mapping required")
    return value


def safe_relative(raw: Any) -> str:
    require(isinstance(raw, str) and raw.strip() == raw and raw, "invalid relative path")
    path = PurePosixPath(raw)
    require(not path.is_absolute() and raw == path.as_posix(), f"unsafe path: {raw!r}")
    require(not any(part in {".", ".."} for part in path.parts), f"unsafe path: {raw!r}")
    return raw


def within(root: Path, raw: Any, label: str) -> Path:
    rel = safe_relative(raw)
    result = (root / rel).resolve()
    require(result.is_relative_to(root.resolve()), f"{label} escapes root")
    return result


def git(root: Path, *args: str, data: bytes | None = None, index: str | None = None) -> bytes:
    env = os.environ.copy()
    if index is not None:
        env["GIT_INDEX_FILE"] = index
    else:
        # Don't let a caller-provided alternate index affect the proof.
        env.pop("GIT_INDEX_FILE", None)
    proc = subprocess.run(["git", *args], cwd=root, env=env, input=data,
                          capture_output=True, check=False)
    require(proc.returncode == 0, f"git {' '.join(args)} failed: {proc.stderr.decode(errors='replace')[:500]}")
    return proc.stdout


def normalize_paths(value: Any) -> list[str]:
    require(isinstance(value, list) and bool(value), "changed_paths must be nonempty list")
    normalized = [safe_relative(p) for p in value]
    require(len(set(normalized)) == len(normalized), "duplicate changed_paths")
    return sorted(normalized)


def git_sha_check(root: Path, commit: str, parent: str, paths: list[str], patch: bytes) -> None:
    require(bool(GIT_OID_PATTERN.fullmatch(commit)) and bool(GIT_OID_PATTERN.fullmatch(parent)), "invalid commit hashes")
    require(git(root, "rev-parse", "HEAD").decode().strip() == commit,
            "canonical HEAD no longer equals reviewed commit")
    parents = git(root, "rev-list", "--parents", "-n", "1", commit).decode().strip().split()
    require(parents == [commit, parent], "commit must have exactly the reviewed source parent")
    changed = git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", commit).decode().split("\x00")
    require(sorted(p for p in changed if p) == paths, "commit changed paths differ from approved scope")
    # Reconstruct approved patch in an external temp *directory*. Unlike a
    # temporary GIT_INDEX_FILE, this cannot create blobs inside .git/objects.
    import tempfile
    with tempfile.TemporaryDirectory(prefix="cf10-post-commit-patch-") as temp:
        tempdir = Path(temp)
        for path in paths:
            source_bytes = git(root, "show", f"{parent}:{path}")
            target = tempdir / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source_bytes)
        env = os.environ.copy()
        for variable in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
            env.pop(variable, None)
        applied = subprocess.run(["git", "apply", "--whitespace=error", "--binary", "-"],
                                 cwd=tempdir, input=patch, capture_output=True, env=env)
        require(applied.returncode == 0, f"exact patch cannot be reconstructed: {applied.stderr.decode(errors='replace')[:500]}")
        for path in paths:
            expected = git(root, "show", f"{commit}:{path}")
            actual = (tempdir / path).read_bytes()
            require(expected == actual, f"commit bytes differ from approved patch reconstruction: {path}")
            expected_mode = git(root, "ls-tree", commit, "--", path).decode().split()[0]
            source_mode = git(root, "ls-tree", parent, "--", path).decode().split()[0]
            require(expected_mode == source_mode, f"mode mismatch: {path}")



def verify_original_worker_review(
    *, root: Path, attempt_dir: Path, attempt: str, base: str, commit: str,
    paths: list[str], review: dict[str, Any],
    review_by_path: dict[str, dict[str, Any]], patch: bytes,
) -> dict[str, str]:
    """Prove the operator review against the original frozen Worker worktree.

    Dirty source preimages are deliberately NOT equal to Git HEAD. Reconstruct
    their original bytes by reversing the already-verified exact patch from
    the Worker candidate, and bind them to the frozen baseline snapshots.
    The separate git_sha_check independently proves the commit against HEAD.
    """
    manifest = yaml_file(attempt_dir / "manifest.yaml", "Worker manifest")
    baseline = yaml_file(attempt_dir / "evidence" / "worker_baseline_v0_1.yaml", "Worker baseline")
    workspace = (attempt_dir / "workspace" / "repo").resolve()
    require(workspace.is_dir() and not workspace.is_symlink(), "Worker candidate workspace missing")
    require(manifest.get("attempt_id") == attempt and manifest.get("source_head") == base,
            "Worker manifest attempt/source mismatch")
    require(baseline.get("source_head") == base, "Worker frozen baseline source mismatch")
    require(Path(str(manifest.get("workspace_repo", ""))).resolve() == workspace,
            "Worker manifest workspace binding mismatch")
    snapshots = baseline.get("baseline_path_snapshots")
    require(isinstance(snapshots, dict), "Worker frozen baseline path snapshots missing")
    inherited = review.get("inherited_dirty_paths")
    require(isinstance(inherited, list) and all(isinstance(x, str) for x in inherited),
            "operator review inherited dirty paths invalid")
    inherited_set = set(inherited)
    candidate_bytes: dict[str, bytes] = {}
    import tempfile
    with tempfile.TemporaryDirectory(prefix="cf10-post-commit-review-") as folder:
        temp = Path(folder)
        for path in paths:
            # Do not trust current canonical worktree (new changes may be present).
            candidate = workspace / path
            require(candidate.is_file() and not candidate.is_symlink() and
                    candidate.resolve().is_relative_to(workspace),
                    f"Worker candidate file missing or unsafe: {path}")
            content = candidate.read_bytes()
            candidate_bytes[path] = content
            expected_sha = review_by_path[path].get("candidate_sha256")
            require(bool(isinstance(expected_sha, str) and SHA_PATTERN.fullmatch(expected_sha)) and
                    sha(content) == expected_sha, f"review final hash mismatch: {path}")
            target = temp / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        env = os.environ.copy()
        for variable in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
            env.pop(variable, None)
        applied = subprocess.run(
            ["git", "apply", "--reverse", "--whitespace=error", "--binary", "-"],
            cwd=temp, input=patch, capture_output=True, env=env, check=False,
        )
        require(applied.returncode == 0,
                "original Worker review patch cannot reverse against candidate: " +
                applied.stderr.decode(errors="replace")[:300])
        modes: dict[str, str] = {}
        for path in paths:
            old_sha = review_by_path[path].get("canonical_sha256")
            require(bool(isinstance(old_sha, str) and SHA_PATTERN.fullmatch(old_sha)) and
                    sha((temp / path).read_bytes()) == old_sha,
                    f"review source hash mismatch: {path}")
            parent_sha = sha(git(root, "show", f"{base}:{path}"))
            commit_sha = sha(git(root, "show", f"{commit}:{path}"))
            dirty = old_sha != parent_sha or review_by_path[path]["candidate_sha256"] != commit_sha
            snapshot = snapshots.get(path)
            if dirty:
                require(path in inherited_set, f"unlisted inherited dirty Worker path: {path}")
                require(isinstance(snapshot, dict) and snapshot.get("kind") == "file"
                        and snapshot.get("sha256") == old_sha,
                        f"frozen dirty-baseline mismatch: {path}")
                modes[path] = "FROZEN_DIRTY_BASELINE"
            else:
                require(old_sha == parent_sha, f"review source hash mismatch: {path}")
                require(review_by_path[path]["candidate_sha256"] == commit_sha,
                        f"review final hash mismatch: {path}")
                if snapshot is not None:
                    require(isinstance(snapshot, dict) and snapshot.get("kind") == "file"
                            and snapshot.get("sha256") == old_sha,
                            f"frozen baseline snapshot mismatch: {path}")
                modes[path] = "SOURCE_HEAD"
        return modes

def unique_terminal_ledger(root: Path, attempt: str) -> tuple[Path, dict[str, Any]]:
    folder = within(root, LEDGER_REL, "attempt ledger")
    require(folder.is_dir(), "canonical attempt ledger folder missing")
    rows = []
    for path in sorted(folder.glob(f"{attempt}__*.yaml")):
        value = yaml_file(path, "ledger record")
        require(value.get("attempt_id") == attempt, "ledger filename/attempt mismatch")
        if value.get("attempt_stage") == "FINISHED":
            rows.append((path, value))
    require(len(rows) == 1, "expected exactly one FINISHED terminal ledger record")
    return rows[0]


def unique_work_front(root: Path, work_front_id: str) -> tuple[Path, dict[str, Any]]:
    folder = within(root, WORK_FRONTS_REL, "work front folder")
    require(folder.is_dir(), "work front folder missing")
    found: list[tuple[Path, dict[str, Any]]] = []
    for path in folder.rglob("*.yaml"):
        if path.is_symlink():
            continue
        try:
            data = yaml_file(path, "work front")
        except (DecisionError, yaml.YAMLError):
            continue
        if data.get("work_front_id") == work_front_id:
            found.append((path, data))
    require(len(found) == 1, f"work front id must resolve exactly once: {work_front_id} (found {len(found)})")
    return found[0]


def bind(path: Path) -> dict[str, str]:
    require(path.is_file(), f"evidence disappeared: {path}")
    return {"path": str(path.resolve()), "sha256": sha(path.read_bytes())}


def validate_report(root: Path, request: dict[str, Any]) -> dict[str, Any]:
    require(request.get("schema_version") == "forprint_cf10_post_commit_acceptance_request_v0_1", "request schema invalid")
    attempt = request.get("attempt_id")
    work_front_id = request.get("work_front_id")
    worker_id = request.get("worker_id")
    require(isinstance(attempt, str) and ID_PATTERN.fullmatch(attempt) is not None, "attempt_id invalid")
    require(isinstance(worker_id, str) and ID_PATTERN.fullmatch(worker_id) is not None, "worker_id invalid")
    require(isinstance(work_front_id, str) and ID_PATTERN.fullmatch(work_front_id) is not None, "work_front_id invalid")
    paths = normalize_paths(request.get("changed_paths"))
    base, commit = request.get("source_head"), request.get("commit_sha")
    patch_sha = request.get("patch_sha256")
    require(isinstance(patch_sha, str) and SHA_PATTERN.fullmatch(patch_sha) is not None, "patch SHA invalid")
    patch_file = within(root, request.get("patch_file"), "patch file")
    patch_bytes = patch_file.read_bytes()
    require(sha(patch_bytes) == patch_sha, "exact patch SHA-256 mismatch")

    contract = yaml_file(within(root, CONTRACT_REL, "contract"), "acceptance contract")
    require(contract.get("schema_version") == "forprint_cf10_post_commit_worker_result_acceptance_contract_v0_1", "contract schema mismatch")
    authority = contract.get("authority_boundaries")
    require(isinstance(authority, dict), "contract authority missing")
    for flag in ("automatic_accept", "replay_candidate_promotion", "automatic_commit", "automatic_push", "rewrite_attempt_ledger"):
        require(authority.get(flag) is False, f"contract authority flag must be false: {flag}")

    ledger_file, ledger = unique_terminal_ledger(root, attempt)
    require(ledger.get("result_state") == "SUCCEEDED" and ledger.get("validator_outcome") == "PASS", "terminal ledger not SUCCEEDED/PASS")
    require(ledger.get("work_front_id") == work_front_id, "ledger work front mismatch")
    wf_path, wf = unique_work_front(root, work_front_id)
    wf_scope = normalize_paths(wf.get("scope"))
    require(set(paths).issubset(wf_scope), "Worker paths exceed approved Work Front scope")
    require(wf.get("authority", {}).get("layer") == "WORK_FRONT", "work front authority layer invalid")

    runtime = Path(str(request.get("runtime_root", ""))).expanduser().resolve()
    require(runtime.is_absolute() and runtime.is_dir(), "runtime root missing")
    attempt_dir = runtime / "forprint_system_blueprint" / worker_id / attempt
    result_file = attempt_dir / "result" / "worker_result.yaml"
    evidence_file = attempt_dir / "evidence" / "governed_worker_cycle_result_return_v0_1.yaml"
    require(result_file.is_file() and evidence_file.is_file(), "missing exact result/return evidence")
    require(str(result_file.resolve()) in ledger.get("result_refs", []), "ledger not bound to exact result")
    require(str(evidence_file.resolve()) in ledger.get("validator_evidence_refs", []), "ledger not bound to exact return evidence")
    result = yaml_file(result_file, "Worker Result")
    evidence = yaml_file(evidence_file, "result return")
    require(result.get("schema_version") == "forprint_assistant_handoff_v2_result_v0_1", "Worker Result schema mismatch")
    require(result.get("attempt_id") == attempt and result.get("status") == "COMPLETED", "Worker Result identity/status mismatch")
    require(normalize_paths(result.get("changed_paths")) == paths, "Worker Result changed paths mismatch")
    require(result.get("handoff_manifest_sha256") == ledger.get("pack_hash_or_context_hash"), "Handoff manifest hash mismatch")
    require(result.get("resume_coordinates", {}).get("attempt_id") == attempt, "resume attempt mismatch")
    require(result.get("unresolved_findings") == [], "unresolved Worker findings")
    validations = result.get("validation_evidence")
    require(isinstance(validations, list) and len(validations) >= 1, "Worker validation evidence absent")
    require(any(row.get("return_code") == 0 for row in validations if isinstance(row, dict)), "no successful Worker validation")
    require(evidence.get("attempt_id") == attempt and evidence.get("result") == "PASS", "result-return identity/result mismatch")
    require(evidence.get("validation_passed") is True and evidence.get("blocked") is False, "result-return blocked or invalid")
    require(evidence.get("result_path") == str(result_file.resolve()), "return result path mismatch")
    for key in ("candidate_promotion_allowed", "automatic_accept_allowed", "commit_allowed", "push_allowed", "release_allowed"):
        require(evidence.get(key) is False, f"result-return authority was widened: {key}")

    review_file = within(root, request.get("review_file"), "operator review")
    review = yaml_file(review_file, "operator review")
    require(review.get("attempt_id") == attempt, "operator review attempt mismatch")
    require(review.get("worker_delta_exact") is True, "operator review delta not exact")
    require(review.get("terminal") == "FINISHED/SUCCEEDED/PASS", "operator review terminal mismatch")
    require(review.get("candidate_promoted") is False, "operator review incorrectly states promotion")
    require(normalize_paths(review.get("worker_changed_paths")) == paths, "operator review scope mismatch")
    file_reviews = review.get("files")
    require(isinstance(file_reviews, list) and len(file_reviews) == len(paths), "operator review hash rows mismatch")
    review_by_path = {row["path"]: row for row in file_reviews if isinstance(row, dict) and "path" in row}
    require(sorted(review_by_path) == paths, "reviewed file list mismatch")

    # Two independent proofs are required. The Git commit must equal the exact
    # approved patch applied to source HEAD; the original operator review may
    # instead describe a dirty frozen Worker baseline inherited from that HEAD.
    git_sha_check(root, commit, base, paths, patch_bytes)
    review_modes = verify_original_worker_review(
        root=root,
        attempt_dir=attempt_dir,
        attempt=attempt,
        base=base,
        commit=commit,
        paths=paths,
        review=review,
        review_by_path=review_by_path,
        patch=patch_bytes,
    )

    sources = {"terminal_ledger": bind(ledger_file), "worker_result": bind(result_file),
               "result_return": bind(evidence_file), "work_front": bind(wf_path),
               "operator_review": bind(review_file), "exact_patch": bind(patch_file),
               "worker_baseline": bind(attempt_dir / "evidence" / "worker_baseline_v0_1.yaml"),
               "worker_manifest": bind(attempt_dir / "manifest.yaml")}
    for path in paths:
        sources[f"workspace_candidate:{path}"] = bind(attempt_dir / "workspace" / "repo" / path)
    binding = {"attempt_id": attempt, "work_front_id": work_front_id,
               "source_head": base, "commit_sha": commit, "patch_sha256": patch_sha,
               "changed_paths": paths, "sources": sources}
    binding_sha = sha(json.dumps(binding, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    prior = []
    decision_dir = within(root, DECISIONS_REL, "decisions")
    if decision_dir.is_dir():
        for path in sorted(decision_dir.glob("*.yaml")):
            row = yaml_file(path, "existing decision")
            if row.get("attempt_id") == attempt:
                require(row.get("review_binding_sha256") == binding_sha,
                        "existing operator decision evidence binding differs")
                prior.append({"decision": row.get("decision"), "decision_id": row.get("decision_id"), "record": str(path)})
    require(len(prior) <= 2, "unexpected number of operator decisions")
    if len(prior) == 2:
        require(sorted(x["decision"] for x in prior) in (["ACCEPT", "HOLD"], ["HOLD", "RETURN"]),
                "contradictory operator decision history")
    accepted = any(x["decision"] == "ACCEPT" for x in prior)
    return {
        "schema_version": "forprint_cf10_post_commit_acceptance_preview_v0_1",
        "state": "EXISTING_OPERATOR_DECISION" if prior else "READY_FOR_EXPLICIT_OPERATOR_DECISION",
        "attempt_id": attempt,
        "work_front_id": work_front_id,
        "source_head": base,
        "commit_sha": commit,
        "patch_sha256": patch_sha,
        "changed_paths": paths,
        "terminal_ledger": "FINISHED/SUCCEEDED/PASS",
        "worker_result": "COMPLETED",
        "result_return": "PASS",
        "work_front_scope": "PASS",
        "reviewed_commit_exact_patch": "PASS",
        "review_baseline_modes": review_modes,
        "evidence_bindings": sources,
        "review_binding_sha256": binding_sha,
        "operator_decision_records": prior,
        "operator_acceptance_recorded": accepted,
        "promotion_replayed": False,
        "commit_performed": False,
        "push_performed": False,
        "publication_status": "NOT_ATTESTED",
        "derived_non_authoritative": True,
    }


def decide(root: Path, report: dict[str, Any], decision: str, decision_id: str,
           operator_ref: str, confirmation: str, supersedes: str | None = None) -> dict[str, Any]:
    require(decision in DECISIONS, "operator decision must be ACCEPT, RETURN or HOLD")
    require(isinstance(decision_id, str) and ID_PATTERN.fullmatch(decision_id) is not None, "invalid decision id")
    require(isinstance(operator_ref, str) and 1 <= len(operator_ref.strip()) <= 100, "operator reference required")
    exact_confirmation = f"{decision}:{report['attempt_id']}:{report['commit_sha'][:12]}"
    require(confirmation == exact_confirmation, f"explicit confirmation must equal {exact_confirmation}")
    if supersedes is not None:
        require(isinstance(supersedes, str) and ID_PATTERN.fullmatch(supersedes) is not None, "invalid supersedes id")
    target = within(root, DECISIONS_REL, "decisions")
    target.mkdir(parents=True, exist_ok=True)
    require(target.is_dir() and not target.is_symlink(), "unsafe decisions folder")
    fd = os.open(target, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        existing = []
        for f in sorted(target.glob("*.yaml")):
            row = yaml_file(f, "existing decision")
            if row.get("decision_id") == decision_id and row.get("attempt_id") != report["attempt_id"]:
                raise DecisionError("decision id already belongs to a different attempt")
            if row.get("attempt_id") == report["attempt_id"]:
                existing.append((f, row))
        for f, row in existing:
            if row.get("decision_id") == decision_id:
                require(row.get("decision") == decision and row.get("review_binding_sha256") == report["review_binding_sha256"]
                        and row.get("operator_ref") == operator_ref and row.get("supersedes_decision_id") == supersedes,
                        "decision-id conflict; immutable replay forbidden")
                return {"status": "ALREADY_RECORDED", "record": str(f), "decision": decision, "attempt_id": report["attempt_id"]}
        if existing:
            require(len(existing) == 1 and existing[0][1].get("decision") == "HOLD", "terminal decision already exists")
            require(supersedes == existing[0][1].get("decision_id"), "later decision must explicitly supersede HOLD")
            require(decision in {"ACCEPT", "RETURN"}, "only ACCEPT/RETURN can supersede HOLD in v0.1")
        else:
            require(supersedes is None, "supersedes decision not found")
        record = {
            "schema_version": "forprint_cf10_post_commit_worker_operator_decision_v0_1",
            "record_role": "post_commit_operator_decision_not_candidate_promotion",
            "decision_id": decision_id,
            "decision": decision,
            "attempt_id": report["attempt_id"],
            "work_front_id": report["work_front_id"],
            "operator_ref": operator_ref,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "supersedes_decision_id": supersedes,
            "source_head": report["source_head"],
            "reviewed_commit_sha": report["commit_sha"],
            "exact_patch_sha256": report["patch_sha256"],
            "changed_paths": report["changed_paths"],
            "review_binding_sha256": report["review_binding_sha256"],
            "evidence_bindings": report["evidence_bindings"],
            "candidate_promotion_reperformed": False,
            "execution_attempt_ledger_mutated": False,
            "automatic_accept": False,
            "commit_performed": False,
            "push_performed": False,
            "publication_state": "NOT_ATTESTED",
            "governance_follow_up": "SEPARATE_COMMIT_AND_PUBLICATION_BOUNDARY",
        }
        raw = yaml.safe_dump(record, sort_keys=False, allow_unicode=True).encode("utf-8")
        dest = target / f"{decision_id}__{sha(raw)[:12]}.yaml"
        outfd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        try:
            with os.fdopen(outfd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            dest.unlink(missing_ok=True)
            raise
        os.fsync(fd)
        return {"status": "RECORDED_LOCAL_APPEND_ONLY", "record": str(dest),
                "decision": decision, "attempt_id": report["attempt_id"],
                "publication_state": "NOT_ATTESTED",
                "commit_performed": False, "push_performed": False}
    finally:
        os.close(fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["preview", "decide"])
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--request", required=True)
    parser.add_argument("--decision", choices=sorted(DECISIONS))
    parser.add_argument("--decision-id")
    parser.add_argument("--operator-ref")
    parser.add_argument("--confirm")
    parser.add_argument("--supersedes-decision-id")
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
        require(Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() == root, "root is not Git top-level")
        request = yaml_file(within(root, args.request, "request"), "request")
        report = validate_report(root, request)
        if args.action == "preview":
            require(not any([args.decision, args.decision_id, args.operator_ref, args.confirm, args.supersedes_decision_id]),
                    "preview cannot carry operator decision flags")
            result = report
        else:
            result = decide(root, report, args.decision, args.decision_id, args.operator_ref,
                            args.confirm, args.supersedes_decision_id)
        print(yaml.safe_dump(result, sort_keys=False, allow_unicode=True), end="")
        return 0
    except (DecisionError, OSError, yaml.YAMLError) as exc:
        print(f"CF10_POST_COMMIT_OPERATOR_DECISION=BLOCKED reason={exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
