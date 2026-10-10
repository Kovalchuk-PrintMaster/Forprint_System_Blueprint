#!/usr/bin/env python3
"""Persist CF-10 post-commit acceptance evidence into tracked project space.

This creates a *derived* content-addressed copy for long-term verification.
It never mutates the original worker result, immutable ledger, or ACCEPT decision.

Project-root examples:
  .venv_blueprint/bin/python -B scripts/coordination/control_plane/persist_worker_acceptance_evidence_v0_1.py \
      --decision-record coordination/continuity/worker_result_decisions/<record>.yaml --check
  .venv_blueprint/bin/python -B scripts/coordination/control_plane/persist_worker_acceptance_evidence_v0_1.py \
      --decision-record coordination/continuity/worker_result_decisions/<record>.yaml --persist
  .venv_blueprint/bin/python -B scripts/coordination/control_plane/persist_worker_acceptance_evidence_v0_1.py \
      --decision-record coordination/continuity/worker_result_decisions/<record>.yaml --verify

No Git staging, commit, push, source modification, promotion or acceptance action.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

import yaml

SCHEMA = "forprint_cf10_worker_acceptance_evidence_snapshot_v0_1"
RECORD_ROLE = "derived_portable_snapshot_not_authoritative_acceptance"
TARGET_BASE = Path("coordination/continuity/worker_evidence")
MAX_SINGLE = 2 * 1024 * 1024
MAX_TOTAL = 12 * 1024 * 1024
HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
ATTEMPT_PATTERN = re.compile(r"^cf10-[A-Za-z0-9_-]+$")
DANGEROUS_PATTERNS = [
    re.compile(rb"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(rb"\bgh[opusr]_[A-Za-z0-9]{20,}"),
    re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(rb"\bBearer\s+[A-Za-z0-9_.+/=-]{24,}", re.I),
]


class GateError(RuntimeError):
    pass


def require(test: bool, message: str) -> None:
    if not test:
        raise GateError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bytes(path: Path, *, expected: str | None = None) -> bytes:
    require(path.is_file() and not path.is_symlink(), f"missing or symlinked file: {path}")
    require(path.stat().st_size <= MAX_SINGLE, f"evidence file exceeds size limit: {path}")
    data = path.read_bytes()
    require(b"\x00" not in data, f"binary evidence requires manual review: {path}")
    for pattern in DANGEROUS_PATTERNS:
        require(not pattern.search(data), f"possible credential/private key, manual review needed: {path}")
    if expected is not None:
        require(digest(data) == expected, f"content checksum mismatch: {path}")
    return data


def parse_yaml(data: bytes, label: str) -> dict[str, Any]:
    value = yaml.safe_load(data)
    require(isinstance(value, dict), f"expected mapping in {label}")
    return value


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    require(result.returncode == 0, f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def git_blob_bytes(root: Path, commit: str, relative: Path) -> bytes:
    proc = subprocess.run(["git", "show", f"{commit}:{relative}"], cwd=root,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    require(proc.returncode == 0,
            f"missing historical Git blob: {commit}:{relative} {proc.stderr.decode(errors='replace')}")
    data = proc.stdout
    require(len(data) <= MAX_SINGLE and b"\x00" not in data,
            f"invalid historical Git blob: {commit}:{relative}")
    return data


def child_of(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def verify_decision(root: Path, rel: Path) -> tuple[dict[str, Any], bytes]:
    require(not rel.is_absolute() and ".." not in rel.parts, "decision must be a repository-relative path")
    full = root / rel
    decision_raw = read_bytes(full)
    decision = parse_yaml(decision_raw, "operator decision")
    require(decision.get("schema_version") == "forprint_cf10_post_commit_worker_operator_decision_v0_1",
            "wrong acceptance record schema")
    require(decision.get("decision") == "ACCEPT", "this evidence snapshot is for explicit ACCEPT")
    require(decision.get("candidate_promotion_reperformed") is False, "promotion replay unexpectedly recorded")
    require(decision.get("publication_state") == "NOT_ATTESTED", "unexpected acceptance publication state")
    attempt = decision.get("attempt_id")
    require(isinstance(attempt, str) and ATTEMPT_PATTERN.fullmatch(attempt) is not None,
            "invalid attempt id")
    commit = decision.get("reviewed_commit_sha")
    require(isinstance(commit, str) and COMMIT_PATTERN.fullmatch(commit) is not None,
            "missing reviewed commit SHA")
    require(isinstance(decision.get("review_binding_sha256"), str) and
            HASH_PATTERN.fullmatch(decision["review_binding_sha256"]) is not None,
            "missing review binding")
    run_git(root, "cat-file", "-e", f"{commit}^{{commit}}")
    # May be run against a descendant HEAD after more local governance commits.
    run_git(root, "merge-base", "--is-ancestor", commit, "HEAD")
    require(run_git(root, "ls-files", "--", str(rel)) == str(rel),
            "decision must already be Git-tracked")
    return decision, decision_raw


def artifact_name(key: str, original: Path) -> str:
    friendly = re.sub(r"[^A-Za-z0-9_.-]+", "_", key).strip("_.")
    suffix = original.suffix if original.suffix in {".yaml", ".json", ".patch", ".py", ".txt"} else ".txt"
    return f"{friendly}{suffix}"


def assemble(root: Path, runtime_root: Path, decision_rel: Path) -> tuple[Path, dict[str, bytes], dict[str, Any]]:
    decision, decision_raw = verify_decision(root, decision_rel)
    attempt = decision["attempt_id"]
    # Anchor canonical references to the commit that introduced the ACCEPT decision,
    # not a mutable future working-tree version of the same path.
    anchor_commit = run_git(root, "log", "-1", "--format=%H", "--", str(decision_rel))
    require(re.fullmatch(r"[0-9a-f]{40}", anchor_commit) is not None,
            "decision is not in a historical Git commit")
    require(git_blob_bytes(root, anchor_commit, decision_rel) == decision_raw,
            "current decision differs from the immutable Git anchor")
    dest_rel = TARGET_BASE / attempt
    dest = root / dest_rel
    bindings = decision.get("evidence_bindings")
    require(isinstance(bindings, dict) and bindings, "evidence bindings missing")
    require(bindings.get("exact_patch", {}).get("sha256") == decision.get("exact_patch_sha256"),
            "patch binding does not equal acceptance patch hash")
    require(1 <= len(bindings) <= 128, "invalid bound evidence count")
    mapping: list[dict[str, Any]] = []
    objects: dict[str, bytes] = {}
    used_names: set[str] = set()

    for key, row in sorted(bindings.items()):
        require(isinstance(key, str) and isinstance(row, dict), "invalid evidence binding")
        original = row.get("path")
        expected = row.get("sha256")
        require(isinstance(original, str) and Path(original).is_absolute(), f"nonabsolute evidence: {key}")
        require(isinstance(expected, str) and HASH_PATTERN.fullmatch(expected) is not None,
                f"invalid expected SHA for {key}")
        path = Path(original)
        require(child_of(path.resolve(), root) or child_of(path.resolve(), runtime_root),
                f"unexpected evidence source outside allowed roots: {key}")
        raw = read_bytes(path, expected=expected)
        if child_of(path, root) and run_git(root, "ls-files", "--", str(path.relative_to(root))) == str(path.relative_to(root)) and \
                digest(git_blob_bytes(root, anchor_commit, path.relative_to(root))) == expected:
            # Canonical files are pinned to immutable Git blobs even if later edited.
            relative = path.relative_to(root)
            storage = "canonical_git_reference"
        else:
            name = artifact_name(key, path)
            require(name not in used_names, f"artifact name collision for {key}: {name}")
            used_names.add(name)
            relative = dest_rel / "objects" / name
            storage = "immutable_snapshot_copy"
            objects[str(relative)] = raw
        mapping.append({
            "binding": key,
            "repository_relative_path": str(relative),
            "sha256": expected,
            "size_bytes": len(raw),
            "storage": storage,
            **({"git_revision": anchor_commit} if storage == "canonical_git_reference" else {}),
        })

    # Save the input that established the Handoff S4 boundary, even though it was not
    # included among the 11 original ACCEPT bindings. Mark it supplemental, not authoritative.
    result_row = bindings.get("worker_result")
    require(isinstance(result_row, dict), "worker_result binding missing")
    worker_result_path = Path(result_row["path"])
    run_dir = worker_result_path.parent.parent
    supplemental = [
        ("origin_handoff_manifest", run_dir / "input" / "governed_worker_cycle_origin_handoff_manifest_v0_1.yaml"),
        ("explicit_dispatch_decision", run_dir / "input" / "governed_worker_cycle_explicit_dispatch_decision_v0_1.yaml"),
    ]
    extra_map: list[dict[str, Any]] = []
    for key, path in supplemental:
        require(child_of(path.resolve(), runtime_root), f"supplemental evidence outside runtime: {key}")
        raw = read_bytes(path)
        relative = dest_rel / "supplemental" / f"{key}.yaml"
        objects[str(relative)] = raw
        extra_map.append({
            "artifact": key,
            "repository_relative_path": str(relative),
            "sha256": digest(raw),
            "size_bytes": len(raw),
            "authority": "supplemental_copy_not_in_accept_binding",
        })

    # Both attempt ledger records are already committed to the canonical repository.
    ledger_dir = root / "coordination/continuity/execution_attempts"
    ledger_refs = sorted(ledger_dir.glob(f"{attempt}__*.yaml"))
    require(len(ledger_refs) == 2, "expected two canonical a040 ledger records")
    ledger_states = set()
    ledgers = []
    for path in ledger_refs:
        raw = read_bytes(path)
        doc = parse_yaml(raw, str(path))
        require(doc.get("attempt_id") == attempt, "ledger attempt mismatch")
        ledger_states.add((doc.get("attempt_stage"), doc.get("result_state"), doc.get("validator_outcome")))
        relative = path.relative_to(root)
        require(run_git(root, "ls-files", "--", str(relative)) == str(relative),
                "ledger must be tracked")
        require(digest(git_blob_bytes(root, anchor_commit, relative)) == digest(raw),
                "canonical ledger differs from anchored Git history")
        ledgers.append({"repository_relative_path": str(relative),
                        "git_revision": anchor_commit, "sha256": digest(raw)})
    require(ledger_states == {("STARTED", "PENDING", "NOT_RUN"), ("FINISHED", "SUCCEEDED", "PASS")},
            "incorrect ledger pair")

    # Test presence of exact content-addressed reviewed commit.
    declared_paths = decision.get("changed_paths")
    require(isinstance(declared_paths, list) and all(isinstance(x, str) for x in declared_paths),
            "acceptance changed paths missing")
    actual_paths = run_git(root, "diff-tree", "--no-commit-id", "--name-only", "-r",
                           decision["reviewed_commit_sha"]).splitlines()
    require(sorted(actual_paths) == sorted(declared_paths),
            "reviewed commit changed-path set mismatch")

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA,
        "record_role": RECORD_ROLE,
        "attempt_id": attempt,
        "decision_id": decision["decision_id"],
        "decision_repository_path": str(decision_rel),
        "decision_sha256": digest(decision_raw),
        "git_anchor_commit": anchor_commit,
        "reviewed_commit_sha": decision["reviewed_commit_sha"],
        "source_head": decision.get("source_head"),
        "exact_patch_sha256": decision["exact_patch_sha256"],
        "review_binding_sha256": decision["review_binding_sha256"],
        "bound_evidence": mapping,
        "supplemental_inputs": extra_map,
        "canonical_ledger": ledgers,
        "binding_count": len(mapping),
        "portable_verification": "local_paths_not_required_after_persist",
        "record_does_not_grant": ["acceptance", "promotion", "commit", "push", "release"],
        "publication_attested": False,
    }
    manifest_raw = yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False,
                                  width=110).encode("utf-8")
    objects[str(dest_rel / "manifest.yaml")] = manifest_raw
    require(sum(map(len, objects.values())) <= MAX_TOTAL, "persistent evidence payload exceeds limit")
    return dest, objects, manifest


def verify_snapshot(root: Path, decision_rel: Path) -> dict[str, Any]:
    decision, raw = verify_decision(root, decision_rel)
    dest = root / TARGET_BASE / decision["attempt_id"]
    manifest_path = dest / "manifest.yaml"
    manifest = parse_yaml(read_bytes(manifest_path), "persistent evidence manifest")
    require(manifest.get("schema_version") == SCHEMA and manifest.get("record_role") == RECORD_ROLE,
            "snapshot schema/role mismatch")
    anchor = manifest.get("git_anchor_commit")
    require(isinstance(anchor, str) and re.fullmatch(r"[0-9a-f]{40}", anchor) is not None,
            "missing snapshot Git anchor")
    require(manifest.get("decision_repository_path") == str(decision_rel) and
            manifest.get("decision_sha256") == digest(raw), "decision content drift")
    require(git_blob_bytes(root, anchor, decision_rel) == raw,
            "decision not equal to Git-anchored version")
    for key in ("attempt_id", "decision_id", "reviewed_commit_sha", "source_head", "exact_patch_sha256", "review_binding_sha256"):
        require(manifest.get(key) == decision.get(key), f"snapshot decision binding mismatch: {key}")
    bindings = decision.get("evidence_bindings")
    assert isinstance(bindings, dict)
    rows = manifest.get("bound_evidence")
    require(isinstance(rows, list) and len(rows) == len(bindings), "snapshot bindings count mismatch")
    seen: set[str] = set()
    for row in rows:
        key = row["binding"]
        require(key in bindings and key not in seen, f"invalid/duplicate snapshot binding: {key}")
        seen.add(key)
        require(row["sha256"] == bindings[key]["sha256"], f"snapshot hash not bound to decision: {key}")
        rel = Path(row["repository_relative_path"])
        require(not rel.is_absolute() and ".." not in rel.parts and
                child_of((root / rel).resolve(), root), "unsafe snapshot path")
        require(row["storage"] in {"canonical_git_reference", "immutable_snapshot_copy"},
                "invalid storage classification")
        if row["storage"] == "immutable_snapshot_copy":
            require(child_of(rel, TARGET_BASE / decision["attempt_id"]),
                    "snapshot object outside attempt folder")
        else:
            require(row.get("git_revision") == anchor, "canonical revision mismatch")
        data = (git_blob_bytes(root, anchor, rel) if row["storage"] == "canonical_git_reference"
                else read_bytes(root / rel, expected=row["sha256"]))
        require(digest(data) == row["sha256"], f"snapshot content hash mismatch: {key}")
        require(len(data) == row["size_bytes"], f"snapshot size mismatch: {key}")
    for section in ("supplemental_inputs", "canonical_ledger"):
        rows = manifest.get(section)
        require(isinstance(rows, list), f"missing snapshot section {section}")
        for row in rows:
            rel = Path(row["repository_relative_path"])
            require(not rel.is_absolute() and ".." not in rel.parts and
                    child_of((root / rel).resolve(), root), "unsafe supplemental path")
            if section == "canonical_ledger":
                require(row.get("git_revision") == anchor, "ledger Git anchor mismatch")
                require(digest(git_blob_bytes(root, anchor, rel)) == row["sha256"],
                        "historical ledger object hash mismatch")
            else:
                read_bytes(root / rel, expected=row["sha256"])
    require(manifest.get("publication_attested") is False, "snapshot wrongly attests publication")
    return {"attempt_id": decision["attempt_id"], "snapshot": str(dest.relative_to(root)),
            "binding_count": len(bindings), "supplemental_count": len(manifest["supplemental_inputs"]),
            "verification_independent_of_tmp_and_runtime": True}


def persist(root: Path, dest: Path, objects: dict[str, bytes]) -> None:
    require(not dest.exists(), f"snapshot already exists; overwrite forbidden: {dest}")
    require(not subprocess.run(["git", "check-ignore", "-q", str(dest.relative_to(root))],
                               cwd=root).returncode == 0, "snapshot directory is Git-ignored")
    parent = dest.parent
    parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{dest.name}.staging-", dir=parent))
    try:
        for relative, data in objects.items():
            rel = Path(relative).relative_to(TARGET_BASE / dest.name)
            path = stage / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(0o644)
        # One rename after all evidence was verified and written.
        require(not dest.exists(), "concurrent destination creation")
        stage.rename(dest)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--runtime-root", type=Path,
                        default=Path("/srv/software_development/forprint-worker-runtime"))
    parser.add_argument("--decision-record", type=Path, required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true")
    action.add_argument("--persist", action="store_true")
    action.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    require(run_git(root, "rev-parse", "--show-toplevel") == str(root),
            "wrong repository root")
    # Record format is versioned; no refresh of immutable evidence if the record differs.
    if args.verify:
        result = verify_snapshot(root, args.decision_record)
    else:
        require(run_git(root, "diff", "--cached", "--name-only") == "", "staging must be empty")
        dest, objects, manifest = assemble(root, args.runtime_root.resolve(), args.decision_record)
        if args.persist:
            persist(root, dest, objects)
            verify_snapshot(root, args.decision_record)
        result = {"attempt_id": manifest["attempt_id"], "snapshot": str(dest.relative_to(root)),
                  "binding_count": manifest["binding_count"],
                  "supplemental_count": len(manifest["supplemental_inputs"]),
                  "files_to_materialize": len(objects),
                  "payload_size_bytes": sum(len(v) for v in objects.values())}
    result.update({"gate": "CF10_PROJECT_DURABLE_EVIDENCE_V0_1", "result": "PASS",
                   "mode": "VERIFY" if args.verify else ("PERSIST" if args.persist else "CHECK"),
                   "git_staging_performed": False, "commit_performed": False,
                   "push_performed": False, "operator_decision_created": False,
                   "publication_attested": False,
                   "next_boundary": "REVIEW_AND_GIT_TRACK_PROJECT_EVIDENCE"})
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (GateError, OSError, yaml.YAMLError, ValueError, KeyError) as error:
        print(f"CF10_PROJECT_DURABLE_EVIDENCE=BLOCKED reason={error}", file=sys.stderr)
        raise SystemExit(2)
