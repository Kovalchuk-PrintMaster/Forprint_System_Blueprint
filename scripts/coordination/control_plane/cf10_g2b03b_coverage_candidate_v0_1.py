"""CF10 G2b-03B: explicitly pinned coverage candidate, NON-AUTHORIZING.

The operator must supply source, canonical source SHA, stable source-root,
external destination, and destination-root from LIVE G2b audit evidence.
No guessing or fallback to historical filenames/paths is permitted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from typing import Any

CONFIRM = "PROVISION_CF10_G2B03B_COVERAGE_V01"
HEAD_AT_PACKAGE = "b81cc641e69eb3c73265cc621424f3ce25d7a603"
EXTERNAL_RELEASES_ROOT = Path("/srv/software_development/forprint-releases/cf10")
MAX_COVERAGE_BYTES = 64 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


class Blocked(Exception):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise Blocked(code)


def absolute_path(raw: str, label: str) -> Path:
    require(bool(raw) and raw.startswith("/"), label + "_MUST_BE_ABSOLUTE")
    path = Path(raw)
    require(str(path) == os.path.normpath(raw), label + "_NOT_NORMALIZED")
    require(path.suffix.lower() == ".json" or label.endswith("ROOT"), label + "_NOT_JSON")
    return path


def no_symlink_components(path: Path, *, require_final: bool) -> None:
    chain = [path, *path.parents]
    for i, part in enumerate(chain):
        try:
            st = part.lstat()
        except FileNotFoundError:
            if i == 0 and not require_final:
                continue
            raise Blocked(f"MISSING_PATH_COMPONENT:{part}")
        require(not stat.S_ISLNK(st.st_mode), f"SYMLINK_PATH_COMPONENT:{part}")


def under(path: Path, ancestor: Path) -> bool:
    return path != ancestor and ancestor in path.parents


def secure_root(path: Path, *, required_uid: int | None) -> None:
    no_symlink_components(path, require_final=True)
    st = path.stat(follow_symlinks=False)
    require(stat.S_ISDIR(st.st_mode), "ROOT_NOT_DIRECTORY")
    if required_uid is not None:
        require(st.st_uid == required_uid, "ROOT_OWNER_MISMATCH")
    require(st.st_mode & 0o022 == 0, "ROOT_WRITABLE_BY_GROUP_OR_OTHER")


def validate_paths(
    source: Path,
    target: Path,
    source_root: Path,
    target_root: Path,
    *,
    required_uid: int | None,
    external_prefix: Path | None,
) -> None:
    require(source != target, "SOURCE_EQUALS_TARGET")
    require(under(source, source_root), "SOURCE_NOT_IN_TRUSTED_SOURCE_ROOT")
    require(under(target, target_root), "TARGET_NOT_IN_DECLARED_TARGET_ROOT")
    require(source_root != target_root, "SOURCE_AND_TARGET_ROOTS_EQUAL")
    if external_prefix is not None:
        require(under(target_root, external_prefix), "TARGET_ROOT_OUTSIDE_EXTERNAL_CF10")
        require(target_root.parts[len(external_prefix.parts)] not in ("gate", "writer"), "TARGET_ROOT_IS_PINNED_RELEASE_AREA")
    secure_root(source_root, required_uid=required_uid)
    secure_root(target_root, required_uid=required_uid)
    no_symlink_components(source, require_final=True)
    no_symlink_components(target.parent, require_final=True)
    no_symlink_components(target, require_final=False)
    for parent in (source.parent, target.parent):
        st = parent.stat(follow_symlinks=False)
        require(stat.S_ISDIR(st.st_mode), "PARENT_NOT_DIRECTORY")
        if required_uid is not None:
            require(st.st_uid == required_uid, "PARENT_OWNER_MISMATCH")
        require(st.st_mode & 0o022 == 0, "PARENT_WRITABLE_BY_GROUP_OR_OTHER")
    if target.exists() or target.is_symlink():
        require(not target.is_symlink(), "TARGET_IS_SYMLINK")
        require(stat.S_ISREG(target.stat(follow_symlinks=False).st_mode), "TARGET_NOT_REGULAR")


def sha256_stream_fd(fd: int) -> tuple[str, int]:
    dig = hashlib.sha256()
    count = 0
    while True:
        block = os.read(fd, CHUNK_SIZE)
        if not block:
            break
        count += len(block)
        require(count <= MAX_COVERAGE_BYTES, "COVERAGE_TOO_LARGE")
        dig.update(block)
    return dig.hexdigest(), count


def fingerprint(st: os.stat_result) -> tuple[int, ...]:
    return st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns


def verify_source(source: Path, digest: str, *, required_uid: int | None) -> dict[str, Any]:
    fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode), "SOURCE_NOT_REGULAR")
        if required_uid is not None:
            require(before.st_uid == required_uid, "SOURCE_OWNER_MISMATCH")
        require(before.st_mode & 0o022 == 0, "SOURCE_WRITABLE_BY_GROUP_OR_OTHER")
        observed, size = sha256_stream_fd(fd)
        after = os.fstat(fd)
        require(fingerprint(before) == fingerprint(after), "SOURCE_CHANGED_DURING_HASH")
        require(fingerprint(source.stat(follow_symlinks=False)) == fingerprint(before), "SOURCE_PATH_REPLACED")
        require(observed == digest, "HISTORICAL_SHA256_MISMATCH")
        return {"sha256": observed, "size": size, "fingerprint": fingerprint(before)}
    finally:
        os.close(fd)


def verify_target(target: Path, digest: str, *, required_uid: int | None) -> str:
    if not os.path.lexists(target):
        return "MISSING"
    no_symlink_components(target, require_final=True)
    fd = os.open(target, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode), "TARGET_NOT_REGULAR")
        if required_uid is not None:
            require(before.st_uid == required_uid, "TARGET_OWNER_MISMATCH")
        observed, _ = sha256_stream_fd(fd)
        require(fingerprint(before) == fingerprint(os.fstat(fd)), "TARGET_CHANGED_DURING_HASH")
        require(observed == digest, "TARGET_SHA256_MISMATCH")
        return "PRESENT_SHA256_MATCH_NON_AUTHORIZING"
    finally:
        os.close(fd)


def check_head(root: Path, expected_head: str) -> str:
    require(bool(re.fullmatch(r"[0-9a-f]{40}", expected_head)), "EXPECTED_HEAD_INVALID")
    result = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    require(result.returncode == 0, "GIT_HEAD_UNAVAILABLE")
    observed = result.stdout.strip()
    require(observed == expected_head, "SOURCE_HEAD_DRIFT")
    return observed


def provision(
    source: Path,
    target: Path,
    digest: str,
    *,
    required_uid: int | None,
) -> str:
    """Atomic, no-overwrite link publication from a same-directory temp file."""
    current = verify_target(target, digest, required_uid=required_uid)
    if current != "MISSING":
        return "ALREADY_PRESENT_MATCHING_NON_AUTHORIZING"
    src_fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    tmp_path: Path | None = None
    try:
        start = os.fstat(src_fd)
        require(stat.S_ISREG(start.st_mode), "SOURCE_NOT_REGULAR")
        if required_uid is not None:
            require(start.st_uid == required_uid, "SOURCE_OWNER_MISMATCH")
        require(start.st_mode & 0o022 == 0, "SOURCE_WRITABLE_BY_GROUP_OR_OTHER")
        require(start.st_size <= MAX_COVERAGE_BYTES, "COVERAGE_TOO_LARGE")
        fd, name = tempfile.mkstemp(prefix=".cf10_g2b03b_pending_", dir=str(target.parent))
        tmp_path = Path(name)
        try:
            os.fchmod(fd, 0o600)
            count = 0
            h = hashlib.sha256()
            while True:
                block = os.read(src_fd, CHUNK_SIZE)
                if not block:
                    break
                count += len(block)
                require(count <= MAX_COVERAGE_BYTES, "COVERAGE_TOO_LARGE")
                h.update(block)
                view = memoryview(block)
                while view:
                    written = os.write(fd, view)
                    require(written > 0, "SHORT_WRITE")
                    view = view[written:]
            os.fsync(fd)
        finally:
            os.close(fd)
        require(h.hexdigest() == digest, "COPY_SHA256_MISMATCH")
        require(fingerprint(start) == fingerprint(os.fstat(src_fd)), "SOURCE_CHANGED_DURING_COPY")
        require(fingerprint(start) == fingerprint(source.stat(follow_symlinks=False)), "SOURCE_PATH_REPLACED_DURING_COPY")
        # link() is atomic with EEXIST on conflict. os.replace() is forbidden.
        try:
            os.link(tmp_path, target, follow_symlinks=False)
        except FileExistsError as exc:
            raise Blocked("TARGET_APPEARED_CONCURRENTLY_NOT_OVERWRITTEN") from exc
        dir_fd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
        require(verify_target(target, digest, required_uid=required_uid) != "MISSING", "TARGET_POST_VERIFY_FAILED")
        return "PROVISIONED_SHA256_MATCH_NON_AUTHORIZING"
    finally:
        os.close(src_fd)
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


def action(
    *,
    mode: str,
    source: Path,
    target: Path,
    source_root: Path,
    target_root: Path,
    digest: str,
    root: Path | None = None,
    expected_head: str | None = None,
    confirm: str | None = None,
    required_uid: int | None = 0,
    external_prefix: Path | None = EXTERNAL_RELEASES_ROOT,
) -> dict[str, Any]:
    require(mode in ("inspect", "provision", "verify"), "UNKNOWN_MODE")
    require(bool(re.fullmatch(r"[0-9a-f]{64}", digest)), "EXPECTED_SHA256_INVALID")
    if root is not None:
        require(expected_head is not None, "EXPECTED_HEAD_REQUIRED")
        check_head(root, expected_head)
    validate_paths(source, target, source_root, target_root, required_uid=required_uid, external_prefix=external_prefix)
    source_info = verify_source(source, digest, required_uid=required_uid)
    target_before = verify_target(target, digest, required_uid=required_uid)
    state = "INSPECTED_NON_AUTHORIZING"
    if mode == "provision":
        require(confirm == CONFIRM, "EXPLICIT_PROVISION_CONFIRMATION_REQUIRED")
        require(os.geteuid() == required_uid if required_uid is not None else True, "OPERATOR_UID_MISMATCH")
        state = provision(source, target, digest, required_uid=required_uid)
    elif mode == "verify":
        require(target_before != "MISSING", "EXTERNAL_CANDIDATE_MISSING")
        state = "VERIFIED_SHA256_MATCH_NON_AUTHORIZING"
    target_after = verify_target(target, digest, required_uid=required_uid)
    return {
        "schema_version": "cf10_g2b03b_candidate_result_v0_1",
        "state": state,
        "source": str(source),
        "source_root": str(source_root),
        "source_sha256": source_info["sha256"],
        "source_bytes": source_info["size"],
        "external_candidate": str(target),
        "target_root": str(target_root),
        "candidate_state_before": target_before,
        "candidate_state_after": target_after,
        "expected_head": expected_head,
        "authority_granted": False,
        "worker_launched": False,
        "writer_gate_unquarantined": False,
        "signed_renewal_performed": False,
        "dynamic_coverage_verified": False,
        "external_independent_attestation": False,
        "historical_evidence_mutated": False,
        "evidence_vault_mutated": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inspect", "provision", "verify"))
    parser.add_argument("--root", required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--target-root", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--confirm", default="")
    args = parser.parse_args(argv)
    result: dict[str, Any]
    try:
        result = action(
            mode=args.mode,
            root=Path(args.root),
            expected_head=args.expected_head,
            source=absolute_path(args.source, "SOURCE"),
            target=absolute_path(args.target, "TARGET"),
            source_root=absolute_path(args.source_root, "SOURCE_ROOT"),
            target_root=absolute_path(args.target_root, "TARGET_ROOT"),
            digest=args.sha256,
            confirm=args.confirm,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        print("CF10_G2B03B_STATUS=" + result["state"])
        print("AUTHORITY_GRANTED=false")
        return 0
    except (Blocked, OSError) as exc:
        print("CF10_G2B03B_STATUS=BLOCKED_NON_AUTHORIZING", file=sys.stderr)
        print("BLOCKER=" + str(exc), file=sys.stderr)
        print("AUTHORITY_GRANTED=false", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
