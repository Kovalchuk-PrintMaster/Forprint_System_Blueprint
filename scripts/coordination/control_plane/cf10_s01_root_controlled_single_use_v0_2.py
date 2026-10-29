"""CF10 S01 persistent single-use state primitive candidate v0.2.

NO live authority. The CLI cannot write a claim or start a Worker. An eventual
independently reviewed launch corridor must first authenticate activation,
release, pilot scope and evidence itself; it may then consume an immutable
root-owned one-shot record before any spawn. This module does NOT turn a caller-
supplied predicate into trusted authority.

All source-level tests use temporary owner-private directories, never /var/lib,
/etc, /run, a canonical ledger, or a real Worker. No automatic reset/retry.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Any

SCHEMA = "cf10_s01_root_controlled_single_use_state_v0_2"
STATE_PATH = Path("/var/lib/forprint/cf10_s01_single_use")
MARKER = "bounded_pilot_consumed_v0_2.json"
FIELDS = frozenset({"receipt_sha256", "publication_commit", "worker_id", "task_prompt_id", "attempt_id"})
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA64 = re.compile(r"[0-9a-f]{64}\Z")
TASK_ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,159}\Z")
ATTEMPT_ID = re.compile(r"cf10-[a-zA-Z0-9][a-zA-Z0-9_.-]{1,159}\Z")
DIR_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
CREATE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)


class RootStateError(ValueError):
    pass


def canonical(document: dict) -> bytes:
    return (json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _result(state: str, blocker: str = "", *, wrote: bool = False) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA, "status": state, "blockers": [blocker] if blocker else [],
        "claim_record_written": wrote, "permission_consumed": wrote,
        "launch_allowed": False, "authority_granted": False,
        "worker_launched": False, "live_make_wired": False,
        "canonical_ledger_modified": False, "production_claim_cli_enabled": False,
    }


def validate_binding(binding: dict[str, Any]) -> list[str]:
    """Structural input validation only. NOT a signature or authority check."""
    if not isinstance(binding, dict) or set(binding) != FIELDS:
        return ["EXACT_SIGNED_BINDING_FIELDS_REQUIRED"]
    errors: list[str] = []
    if not isinstance(binding["receipt_sha256"], str) or not SHA64.fullmatch(binding["receipt_sha256"]):
        errors.append("RECEIPT_DIGEST_INVALID")
    if not isinstance(binding["publication_commit"], str) or not SHA40.fullmatch(binding["publication_commit"]):
        errors.append("PUBLICATION_COMMIT_INVALID")
    if binding["worker_id"] != "worker-01":
        errors.append("WORKER_ID_INVALID")
    if not isinstance(binding["task_prompt_id"], str) or not TASK_ID.fullmatch(binding["task_prompt_id"]):
        errors.append("TASK_PROMPT_ID_INVALID")
    if not isinstance(binding["attempt_id"], str) or not ATTEMPT_ID.fullmatch(binding["attempt_id"]):
        errors.append("ATTEMPT_ID_INVALID")
    return sorted(errors)


def _check_dir_fd(dfd: int, *, owner_uid: int) -> None:
    st = os.fstat(dfd)
    if (not stat.S_ISDIR(st.st_mode) or st.st_uid != owner_uid or
            stat.S_IMODE(st.st_mode) != 0o700):
        raise RootStateError("PRIVATE_STATE_DESCRIPTOR_UNSAFE")


def open_root_owned_state_dir() -> int:
    """Production-only primitive. Does not provision; never called by CLI.

    A separate independent operator must review durable mount persistence,
    filesystem security and provision this root-owned directory. Keeping this
    as an opt-in library primitive is NOT live wiring or launch authority.
    """
    if os.geteuid() != 0:
        raise RootStateError("ROOT_ONLY_STATE_ACCESS")
    for directory in [Path("/var"), Path("/var/lib"), Path("/var/lib/forprint"), STATE_PATH]:
        st = directory.lstat()
        if (not stat.S_ISDIR(st.st_mode) or st.st_uid != 0 or
                (stat.S_IMODE(st.st_mode) & 0o022)):
            raise RootStateError("ROOT_STATE_PATH_UNTRUSTED")
    st = STATE_PATH.lstat()
    if stat.S_IMODE(st.st_mode) != 0o700:
        raise RootStateError("ROOT_STATE_DIRECTORY_NOT_0700")
    fd = os.open(STATE_PATH, DIR_FLAGS)
    try:
        actual = os.fstat(fd)
        if (actual.st_dev, actual.st_ino) != (st.st_dev, st.st_ino):
            raise RootStateError("ROOT_STATE_DIRECTORY_REPLACED")
        _check_dir_fd(fd, owner_uid=0)
        return fd
    except BaseException:
        os.close(fd)
        raise


def consume_once_fd(dfd: int, binding: dict[str, Any], *, owner_uid: int = 0,
                    now: datetime | None = None) -> dict[str, Any]:
    """Permanently consume *one state-store slot* across process/reboot.

    Untrusted callers can at most consume a slot; they receive NO launch authority.
    The future privileged launch corridor MUST validate real v0.2 receipts,
    signatures, proofs, source, approval, current process state and exact scope
    immediately beforehand and keep claim+spawn within a controlled corridor.

    owner_uid argument is for isolated unit tests only; production callers MUST
    use the fixed root-owned opener above and its owner_uid=0 default.
    """
    errors = validate_binding(binding)
    if errors:
        return _result("BLOCKED_NON_AUTHORIZING", errors[0])
    try:
        _check_dir_fd(dfd, owner_uid=owner_uid)
    except (OSError, RootStateError):
        return _result("BLOCKED_NON_AUTHORIZING", "PRIVATE_STATE_DESCRIPTOR_UNSAFE")
    try:
        fd = os.open(MARKER, CREATE_FLAGS, 0o600, dir_fd=dfd)
    except FileExistsError:
        return _result("BLOCKED_NON_AUTHORIZING", "SINGLE_USE_PERMANENTLY_CONSUMED")
    except OSError:
        return _result("BLOCKED_NON_AUTHORIZING", "ROOT_STATE_CLAIM_OPEN_FAILED")
    try:
        moment = now or datetime.now(timezone.utc)
        if moment.tzinfo is None:
            return _result("BLOCKED_NON_AUTHORIZING", "CLAIM_TIMESTAMP_INDETERMINATE_NO_RETRY")
        payload = canonical({
            "schema_version": SCHEMA,
            "state": "CONSUMED_BEFORE_SPAWN_NO_RETRY",
            "binding": binding,
            "binding_sha256": digest(canonical(binding)),
            "recorded_at": moment.astimezone(timezone.utc).isoformat(),
            "automatic_retry": False,
            "authority_granted_by_claim": False,
        })
        pos = 0
        while pos < len(payload):
            count = os.write(fd, payload[pos:])
            if count <= 0:
                raise OSError(errno.EIO, "incomplete claim write")
            pos += count
        os.fsync(fd)
        os.fsync(dfd)
        return _result("CONSUMED_NO_LAUNCH_NON_AUTHORIZING", wrote=True)
    except OSError:
        # No deletion: even a partially created claim permanently blocks retry.
        return _result("BLOCKED_NON_AUTHORIZING", "CLAIM_DURABILITY_UNKNOWN_NO_RETRY")
    finally:
        os.close(fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inspect", "launch-preflight"))
    args = parser.parse_args(argv)
    print(json.dumps(_result("BLOCKED_NON_AUTHORIZING", "ROOT_CLAIM_NOT_LIVE_WIRED"),
                     ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if args.mode == "inspect" else 2


if __name__ == "__main__":
    raise SystemExit(main())
