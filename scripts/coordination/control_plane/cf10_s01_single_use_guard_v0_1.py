"""CF10 S01 single-use *fixture* claim candidate v0.1.

This is NOT a launch guard: it never validates external authority, provisions
root-owned state, acquires production locks, or invokes any Worker. Only a
private, existing, owner-only directory beneath a tmp component may be used.
The exercise demonstrates atomic, durable, no-retry claim semantics. A later
independently reviewed live corridor must own the secure state and join claim
with launch inside one controlled operation.
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

SCHEMA = "cf10_s01_single_use_fixture_claim_v0_1"
CLAIM_NAME = "single_use_claim_v0_1.json"
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA64 = re.compile(r"[0-9a-f]{64}\Z")
TASK = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,159}\Z")
ATTEMPT = re.compile(r"cf10-[A-Za-z0-9][A-Za-z0-9_.-]{1,159}\Z")
FIELDS = frozenset({"receipt_sha256", "publication_commit", "worker_id", "task_prompt_id", "attempt_id"})


def _digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _encoded(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _result(status: str, code: str, *, wrote: bool = False, path: str | None = None) -> dict[str, Any]:
    return {"schema_version": SCHEMA, "status": status, "blockers": [] if wrote else [code],
            "claim_record_written": wrote, "claim_path": path if wrote else None,
            "fixture_only": True, "single_use_production_enforced": False,
            "authority_granted": False, "launch_allowed": False,
            "worker_launched": False, "canonical_ledger_modified": False,
            "live_make_wired": False}


def binding_blockers(binding: dict[str, Any], predicate: dict[str, Any]) -> list[str]:
    """Necessary input consistency checks, NOT proof of cryptographic authority."""
    bad: list[str] = []
    if not isinstance(binding, dict) or set(binding) != FIELDS:
        return ["EXACT_BINDING_REQUIRED"]
    if (not isinstance(binding["receipt_sha256"], str) or not SHA64.fullmatch(binding["receipt_sha256"])):
        bad.append("RECEIPT_DIGEST_INVALID")
    if (not isinstance(binding["publication_commit"], str) or not SHA40.fullmatch(binding["publication_commit"])):
        bad.append("PUBLICATION_COMMIT_INVALID")
    if binding["worker_id"] != "worker-01":
        bad.append("WORKER_NOT_SUPPORTED")
    if not isinstance(binding["task_prompt_id"], str) or not TASK.fullmatch(binding["task_prompt_id"]):
        bad.append("TASK_ID_INVALID")
    if not isinstance(binding["attempt_id"], str) or not ATTEMPT.fullmatch(binding["attempt_id"]):
        bad.append("ATTEMPT_ID_INVALID")
    if not isinstance(predicate, dict):
        return bad + ["PREDICATE_INVALID"]
    if predicate.get("predicate_pass") is not True or predicate.get("status") != "PREDICATE_PASS_NON_AUTHORIZING":
        bad.append("PREDICATE_NOT_VERIFIED")
    if predicate.get("blockers") != []:
        bad.append("PREDICATE_HAS_BLOCKERS")
    for key in ("worker_id", "task_prompt_id", "attempt_id"):
        if predicate.get(key) != binding[key]:
            bad.append("PREDICATE_BINDING_MISMATCH:" + key)
    checks = predicate.get("checks")
    if not isinstance(checks, dict) or (checks.get("baseline") != "PASS"
            or checks.get("pilot_scope") != "SIGNED_MATCH"
            or type(checks.get("proof_files_verified")) is not int
            or checks["proof_files_verified"] != 8
            or checks.get("head_stable") is not True):
        bad.append("PREDICATE_CHECKS_INCOMPLETE")
    for key in ("launch_allowed", "authority_granted", "single_use_enforced", "worker_launched", "live_make_wired"):
        if predicate.get(key) is not False:
            bad.append("PREDICATE_PRETENDS_AUTHORITY:" + key)
    # A dict from a caller is ALWAYS untrusted. These checks are for fixture logic.
    return sorted(set(bad))


def _private_fixture_dir(directory: Path) -> tuple[int, str]:
    """Return open directory fd; refuse symlinks and non-private/non-tmp paths."""
    p = Path(directory).absolute()
    if (p.name.startswith("cf10_s01_single_use_") is False or
            "tmp" not in p.parts[1:] or p.resolve() != p):
        raise ValueError("FIXTURE_ROOT_NOT_PRIVATE_TMP")
    st = p.lstat()
    if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or (stat.S_IMODE(st.st_mode) & 0o077):
        raise ValueError("FIXTURE_ROOT_UNTRUSTED")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    fd = os.open(p, flags)
    actual = os.fstat(fd)
    if ((actual.st_dev, actual.st_ino) != (st.st_dev, st.st_ino) or
            not stat.S_ISDIR(actual.st_mode) or actual.st_uid != os.getuid()):
        os.close(fd)
        raise ValueError("FIXTURE_ROOT_REPLACED")
    return fd, str(p)


def consume_once_fixture(directory: Path, *, binding: dict[str, Any],
                         predicate: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    """Atomically mark one simulation as consumed; NEVER authorize/launch.

    CREATE|EXCL serializes concurrent processes. A crash before fsync leaves an
    incomplete marker; every subsequent call fails closed, never auto-retries.
    No mutation outside the supplied pre-existing private tmp fixture directory.
    """
    bad = binding_blockers(binding, predicate)
    if bad:
        return _result("BLOCKED_NON_AUTHORIZING", bad[0])
    try:
        dfd, p = _private_fixture_dir(directory)
    except (OSError, ValueError):
        return _result("BLOCKED_NON_AUTHORIZING", "FIXTURE_DIRECTORY_NOT_SAFE")
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
        try:
            fd = os.open(CLAIM_NAME, flags, 0o600, dir_fd=dfd)
        except FileExistsError:
            return _result("BLOCKED_NON_AUTHORIZING", "SINGLE_USE_ALREADY_CONSUMED")
        except OSError:
            return _result("BLOCKED_NON_AUTHORIZING", "SINGLE_USE_CLAIM_OPEN_FAILED")
        try:
            at = (now or datetime.now(timezone.utc))
            if at.tzinfo is None:
                at = at.replace(tzinfo=timezone.utc)
            record = {"schema_version": SCHEMA, "state": "CONSUMED_TEST_FIXTURE_ONLY",
                      "binding": binding, "binding_sha256": _digest(_encoded(binding)),
                      "recorded_at": at.astimezone(timezone.utc).isoformat()}
            payload = _encoded(record)
            sent = 0
            while sent < len(payload):
                n = os.write(fd, payload[sent:])
                if n <= 0:
                    raise OSError(errno.EIO, "short write")
                sent += n
            os.fsync(fd)
            os.fsync(dfd)
            return _result("CONSUMED_TEST_FIXTURE_NON_AUTHORIZING", "", wrote=True,
                           path=str(Path(p) / CLAIM_NAME))
        except OSError:
            # Marker exists now: intentionally NOT deleted. Ambiguous state is
            # permanently consumed and must be reviewed by an operator.
            return _result("BLOCKED_NON_AUTHORIZING", "CLAIM_WRITE_INDETERMINATE_NO_RETRY")
        finally:
            os.close(fd)
    finally:
        os.close(dfd)


def inspect() -> dict[str, Any]:
    return _result("BLOCKED_NON_AUTHORIZING", "SINGLE_USE_NOT_LIVE_WIRED")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("inspect", "launch-preflight"))
    args = p.parse_args(argv)
    print(json.dumps(inspect(), ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if args.mode == "inspect" else 2


if __name__ == "__main__":
    raise SystemExit(main())
