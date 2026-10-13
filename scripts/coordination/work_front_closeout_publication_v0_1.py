"""Verify exact implementation file contents at a live observed remote ref."""
from __future__ import annotations
import hashlib
from pathlib import Path
import re
import subprocess
from typing import Any

class PublicationError(RuntimeError):
    pass

def git(root: Path, *args: str) -> bytes:
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, timeout=30)
    if p.returncode:
        raise PublicationError("GIT_VERIFICATION_FAILED:" + " ".join(args[:2]))
    return p.stdout

def verify_publication(root: Path, request: dict, decision: dict, policy: dict, manifest: dict) -> dict:
    commit = decision.get("publication_commit")
    ref = decision.get("publication_ref")
    remote = decision.get("publication_remote")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40,64}", commit):
        raise PublicationError("COMMIT_INVALID")
    if not all(isinstance(x, str) and x for x in (ref, remote)):
        raise PublicationError("PUBLICATION_TARGET_MISSING")
    if (remote, ref) != (policy.get("publication_remote"), policy.get("publication_ref")):
        raise PublicationError("PUBLICATION_POLICY_MISMATCH")
    if git(root, "cat-file", "-t", commit).strip() != b"commit":
        raise PublicationError("NOT_A_COMMIT")
    # A mutable Git remote alias is NOT a trust anchor. Pin its actual URL to
    # the independently approved operator-controlled policy before fetching.
    approved_url = policy.get("publication_remote_url")
    if not isinstance(approved_url, str) or not approved_url:
        raise PublicationError("APPROVED_REMOTE_URL_MISSING")
    observed_url = git(root, "remote", "get-url", remote).decode().strip()
    if observed_url != approved_url:
        raise PublicationError("REMOTE_URL_DRIFT")
    remote_lines = git(root, "ls-remote", "--exit-code", approved_url, ref).decode().splitlines()
    if len(remote_lines) != 1 or remote_lines[0].split() != [commit, ref]:
        raise PublicationError("REMOTE_REF_COMMIT_DRIFT")
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "forprint_closeout_publication_manifest_v0_1":
        raise PublicationError("MANIFEST_SCHEMA_INVALID")
    import json
    data = (json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
    if hashlib.sha256(data).hexdigest() != decision.get("publication_manifest_sha256"):
        raise PublicationError("MANIFEST_HASH_DRIFT")
    if manifest.get("commit") != commit:
        raise PublicationError("MANIFEST_COMMIT_MISMATCH")
    paths = manifest.get("implementation_sha256")
    if not isinstance(paths, dict) or not paths:
        raise PublicationError("MANIFEST_EMPTY")
    # Publication paths must be exactly those frozen in Stage 1 plan.
    plan_paths = manifest.get("frozen_prepublication_file_sha256")
    if not isinstance(plan_paths, dict) or plan_paths != paths:
        raise PublicationError("FROZEN_IMPLEMENTATION_BINDING_MISMATCH")
    for path, sha in sorted(paths.items()):
        if (not isinstance(path, str) or path.startswith("/") or ".." in Path(path).parts
                or not re.fullmatch(r"[0-9a-f]{64}", sha)):
            raise PublicationError("IMPLEMENTATION_PATH_OR_SHA_INVALID")
        blob = git(root, "show", f"{commit}:{path}")
        if hashlib.sha256(blob).hexdigest() != sha:
            raise PublicationError("PUBLISHED_BLOB_MISMATCH:" + path)
    return {"commit": commit, "remote": remote, "ref": ref, "blob_count": len(paths)}
