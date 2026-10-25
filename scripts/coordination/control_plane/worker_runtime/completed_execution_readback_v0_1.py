#!/usr/bin/env python3
"""Read-only, non-authorizing CF-10 durable structured-execution evidence check.

This is an OPERATOR DIAGNOSTIC, not an MCP capability or a Worker Result,
and cannot authorize reuse, skip validation, acceptance, resume or promotion.
It never starts a process or writes any runtime/canonical artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

SCHEMA = "forprint_structured_execution_result_v0_1"
EXEC_ID = re.compile(r"structured-exec-[0-9a-f]{20}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
MAX_RESULT_BYTES = 2 * 1024 * 1024
FALSE_AUTHORITY = (
    "executor_grants_authority", "canonical_write_allowed", "safe_write_allowed",
    "commit_allowed", "push_allowed", "merge_allowed", "release_allowed",
    "promotion_allowed", "arbitrary_shell_allowed",
)


class ReadbackBlocked(ValueError):
    pass


def _require(test: bool, reason: str) -> None:
    if not test:
        raise ReadbackBlocked(reason)


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _json_sha(value: Any) -> str:
    # Same canonical encoding as structured_command_executor._sha.
    return _sha_bytes(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8"))


def _exact_directory(raw: str, label: str) -> Path:
    p = Path(raw).expanduser()
    _require(p.is_absolute(), label + " must be an absolute path")
    _require(str(p.resolve()) == str(p), label + " must be canonical")
    _require(p.is_dir() and not p.is_symlink(), label + " directory missing/unsafe")
    return p


def _safe_file(path: Path) -> bytes:
    _require(path.is_file() and not path.is_symlink() and path.resolve() == path, "missing/unsafe evidence file: " + str(path))
    _require(path.stat().st_size <= MAX_RESULT_BYTES, "evidence exceeds bounded read size")
    return path.read_bytes()


def verify_completed_execution(
    *, attempt_root: str, execution_id: str, expected_task_id: str,
    expected_work_front_id: str, expected_decision_id: str,
    expected_workspace: str, expected_request_id: str | None = None,
) -> dict[str, Any]:
    """Verify a historical attempt-bound result, without granting its acceptance."""
    _require(bool(EXEC_ID.fullmatch(execution_id)), "execution_id syntax invalid")
    attempt = _exact_directory(attempt_root, "attempt_root")
    workspace = _exact_directory(expected_workspace, "expected_workspace")
    _require(workspace == attempt / "workspace" / "repo", "workspace outside attempt")
    _require(all(isinstance(x, str) and x.strip() for x in (
        expected_task_id, expected_work_front_id, expected_decision_id,
    )), "explicit identity incomplete")
    _require(bool(SHA.fullmatch(expected_decision_id)), "decision digest invalid")

    evidence_root = attempt / "evidence" / "structured_command"
    directory = evidence_root / execution_id
    _require(directory.is_dir() and not directory.is_symlink() and directory.resolve() == directory, "execution evidence missing/unsafe")
    result_path = directory / "execution_result_v0_1.yaml"
    raw = _safe_file(result_path)

    # Reject duplicate YAML keys instead of silently overwriting evidence identity.
    class StrictLoader(yaml.SafeLoader):
        pass

    def mapping(loader: yaml.SafeLoader, node: yaml.MappingNode) -> dict:
        value: dict = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=True)
            _require(isinstance(key, str) and key not in value, "duplicate/invalid YAML key")
            value[key] = loader.construct_object(value_node, deep=True)
        return value

    StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    result = yaml.load(raw, Loader=StrictLoader)
    _require(isinstance(result, dict), "result must be a mapping")
    _require(result.get("schema_version") == SCHEMA, "result schema mismatch")
    _require(result.get("execution_id") == execution_id, "execution ID mismatch")
    _require(result.get("result_evidence_path") == str(result_path), "result path binding mismatch")
    _require(result.get("consumer_id") == "cf10_worker_validation_mcp", "consumer mismatch")
    _require(result.get("capability_id") == "validation_suite", "capability mismatch")
    _require(result.get("capability_version") == "0.2.0", "capability version mismatch")
    _require(result.get("exact_cwd") == str(workspace), "workspace binding mismatch")
    _require(result.get("shell") is False, "shell boundary violated")
    _require(result.get("outcome") == "completed", "execution did not complete")
    _require(type(result.get("return_code")) is int and result["return_code"] == 0, "execution return code not PASS")
    _require(result.get("timed_out") is False, "execution timed out")
    _require(type(result.get("elapsed_seconds")) in (int, float)
             and 0 <= result["elapsed_seconds"] <= 1200, "elapsed duration invalid")
    _require(isinstance(result.get("request_id"), str)
             and result["request_id"].startswith(attempt.name + ":validation:")
             and re.fullmatch(re.escape(attempt.name) + r":validation:[0-9]{4}", result["request_id"]),
             "request identity mismatch")
    if expected_request_id is not None:
        _require(result["request_id"] == expected_request_id, "expected request mismatch")
    identity = result.get("execution_identity")
    _require(isinstance(identity, dict) and identity == {
        "attempt_id": attempt.name,
        "task_id": expected_task_id,
        "work_front_id": expected_work_front_id,
        "explicit_dispatch_decision_id": expected_decision_id,
    }, "execution identity mismatch")
    _require(isinstance(result.get("argv_digest"), str)
             and SHA.fullmatch(result["argv_digest"]) is not None, "argv digest invalid")
    auth = result.get("authority")
    _require(isinstance(auth, dict) and all(auth.get(k) is False for k in FALSE_AUTHORITY),
             "execution authority widened")
    policy = result.get("execution_policy_result")
    _require(isinstance(policy, dict)
             and policy.get("decision") == "ALLOW"
             and policy.get("consumer_policy_validated") is True
             and policy.get("authorization_envelope_verified") is True
             and policy.get("authority_originated_by_executor") is False,
             "execution policy proof invalid")

    digest = result.get("evidence_digest")
    _require(isinstance(digest, str) and SHA.fullmatch(digest) is not None,
             "evidence digest missing")
    payload = {k: v for k, v in result.items() if k != "evidence_digest"}
    _require(_json_sha(payload) == digest, "evidence digest mismatch")

    stream_digests: dict[str, str] = {}
    for stream in ("stdout", "stderr"):
        item = result.get(stream + "_evidence")
        _require(isinstance(item, dict), stream + " evidence missing")
        path = directory / (stream + ".log")
        _require(item.get("path") == str(path), stream + " evidence path mismatch")
        _require(type(item.get("size_bytes")) is int and item["size_bytes"] >= 0,
                 stream + " evidence size invalid")
        _require(isinstance(item.get("sha256"), str), stream + " digest missing")
        # Stream may be large; hash in bounded chunks, with no modification.
        _require(path.is_file() and not path.is_symlink() and path.resolve() == path, stream + " missing/unsafe")
        _require(path.stat().st_size == item["size_bytes"], stream + " byte size mismatch")
        h = hashlib.sha256()
        with path.open("rb") as stream_file:
            for block in iter(lambda: stream_file.read(1024 * 1024), b""):
                h.update(block)
        _require(h.hexdigest() == item["sha256"], stream + " digest mismatch")
        stream_digests[stream] = h.hexdigest()

    return {
        "schema_version": "forprint_cf10_execution_evidence_readback_v0_1",
        "status": "PASS_NON_AUTHORIZING",
        "attempt_id": attempt.name,
        "request_id": result["request_id"],
        "execution_id": execution_id,
        "capability_id": "validation_suite",
        "result_sha256": _sha_bytes(raw),
        "evidence_digest": digest,
        "stdout_sha256": stream_digests["stdout"],
        "stderr_sha256": stream_digests["stderr"],
        "execution_completed": True,
        "historical_source_fingerprint_verified": False,
        "worker_result_validated": False,
        "acceptance_granted": False,
        "replay_skip_authorized": False,
        "canonical_write_performed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-root", required=True)
    parser.add_argument("--execution-id", required=True)
    parser.add_argument("--expected-task-id", required=True)
    parser.add_argument("--expected-work-front-id", required=True)
    parser.add_argument("--expected-decision-id", required=True)
    parser.add_argument("--expected-workspace", required=True)
    parser.add_argument("--expected-request-id")
    args = parser.parse_args(argv)
    try:
        output = verify_completed_execution(
            attempt_root=args.attempt_root,
            execution_id=args.execution_id,
            expected_task_id=args.expected_task_id,
            expected_work_front_id=args.expected_work_front_id,
            expected_decision_id=args.expected_decision_id,
            expected_workspace=args.expected_workspace,
            expected_request_id=args.expected_request_id,
        )
    except (ReadbackBlocked, OSError, yaml.YAMLError, ValueError, TypeError) as exc:
        print("CF10_EXECUTION_EVIDENCE_READBACK=BLOCKED", file=sys.stderr)
        print(f"REASON={exc}", file=sys.stderr)
        return 2
    print("CF10_EXECUTION_EVIDENCE_READBACK=PASS_NON_AUTHORIZING")
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
