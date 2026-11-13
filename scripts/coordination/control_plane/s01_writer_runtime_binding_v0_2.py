"""s01 operator Make preflight bound to existing signed Writer Activation Gate.

READ ONLY. The only positive authority comes from a root-controlled, independently
signed *existing* Activation Gate decision extended with s01 runtime source hashes.
Never signs/installs/trusts itself, never launches a worker, never mutates ledger.
Direct Python and non-Make paths remain beyond this operator Make prerequisite.
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
from typing import Any

from scripts.coordination.control_plane import s01_writer_runtime_binding_v0_1 as inventory

SCHEMA = "cf10_s01_writer_runtime_binding_v0_2"
SIGNED_EXTENSION_KEY = "s01_runtime_binding_v0_2"
SIGNED_EXTENSION_SCHEMA = "cf10_s01_operator_runtime_binding_approval_v0_2"
OPERATOR_DECISION = "AUTHORIZE_S01_OPERATOR_MAKE_CORRIDOR"
# Stable cryptographic requirements: this code and Makefile must also be signed.
RUNTIME_SOURCE_SET = (*inventory.TRACKED_WRITERS,
    "scripts/coordination/control_plane/s01_writer_runtime_binding_v0_1.py",
    "scripts/coordination/control_plane/s01_writer_runtime_binding_v0_2.py",
    "Makefile")
ALLOWED_LEGACY_FINDING = "DEPLOYMENT_WRITER_SOURCE_NOT_EQUAL_PINNED_RELEASE"
ATTESTATION_FILE = Path("/etc/forprint/execution_attempt_writer_activation/signed_decision_v0_1.json")
MAX_TRUST_BYTES = 1024 * 1024

class PreflightBlocked(RuntimeError):
    pass


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(doc: Any) -> bytes:
    return (json.dumps(doc, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def signed_source_digests(root: Path) -> dict[str, str]:
    """Live hashes include uncommitted main changes; no HEAD-only shortcut."""
    result = {}
    for rel in RUNTIME_SOURCE_SET:
        path = root / rel
        try:
            st = path.lstat()
        except OSError as exc:
            raise PreflightBlocked("RUNTIME_SOURCE_MISSING:" + rel) from exc
        if not stat.S_ISREG(st.st_mode) or st.st_mode & 0o022:
            raise PreflightBlocked("RUNTIME_SOURCE_UNSAFE:" + rel)
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                     | getattr(os, "O_CLOEXEC", 0))
        try:
            actual = os.fstat(fd)
            if ((actual.st_dev, actual.st_ino) != (st.st_dev, st.st_ino)
                    or not stat.S_ISREG(actual.st_mode)):
                raise PreflightBlocked("RUNTIME_SOURCE_REPLACED:" + rel)
            with os.fdopen(fd, "rb", closefd=False) as stream:
                payload = stream.read()
        finally:
            os.close(fd)
        result[rel] = digest(payload)
    return result


def trusted_decision_snapshot(path: Path = ATTESTATION_FILE) -> tuple[dict, str]:
    """Independent Activation Gate will verify the Ed25519 signature separately."""
    parent = path.parent
    if parent.is_symlink() or not parent.is_dir():
        raise PreflightBlocked("TRUST_DIRECTORY_MISSING_OR_SYMLINK")
    ps = parent.lstat()
    if ps.st_uid != 0 or ps.st_mode & 0o022:
        raise PreflightBlocked("TRUST_DIRECTORY_UNSAFE")
    try:
        ls = path.lstat()
    except OSError as exc:
        raise PreflightBlocked("SIGNED_DECISION_MISSING") from exc
    if not stat.S_ISREG(ls.st_mode) or ls.st_uid != 0 or ls.st_mode & 0o022:
        raise PreflightBlocked("SIGNED_DECISION_UNSAFE")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0))
    try:
        fs = os.fstat(fd)
        if fs.st_ino != ls.st_ino or fs.st_dev != ls.st_dev or fs.st_size > MAX_TRUST_BYTES:
            raise PreflightBlocked("SIGNED_DECISION_REPLACED_OR_OVERSIZE")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            raw = stream.read(MAX_TRUST_BYTES + 1)
    finally:
        os.close(fd)
    if len(raw) > MAX_TRUST_BYTES:
        raise PreflightBlocked("SIGNED_DECISION_TOO_LARGE")
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise PreflightBlocked("SIGNED_DECISION_INVALID_JSON") from exc
    if not isinstance(data, dict) or canonical(data) != raw:
        raise PreflightBlocked("SIGNED_DECISION_NONCANONICAL")
    return data, digest(raw)


def _verified_process(*, root: Path, module: str, argv: tuple[str, ...],
                      expected_stage: str, allowed_status: str) -> dict[str, Any]:
    """Execute existing published readback, NOT main's potentially dirty copy.

    cwd plus PYTHONPATH pins -m to its approved isolated checkout. Both
    published checkouts are already independently verified by inventory.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [sys.executable, "-B", "-m", module, *argv]
    try:
        p = subprocess.run(command, cwd=root, env=env, capture_output=True,
                           text=True, check=False, timeout=65)
    except (OSError, subprocess.SubprocessError) as exc:
        raise PreflightBlocked("INDEPENDENT_GATE_EXECUTION_FAILED:" + expected_stage) from exc
    if p.returncode != 0:
        raise PreflightBlocked("INDEPENDENT_GATE_BLOCKED:" + expected_stage)
    try:
        result = json.loads(p.stdout)
    except (ValueError, TypeError) as exc:
        raise PreflightBlocked("INDEPENDENT_GATE_NONJSON:" + expected_stage) from exc
    if (not isinstance(result, dict) or result.get("stage") != expected_stage
            or result.get("status") != allowed_status or result.get("blockers") != []):
        raise PreflightBlocked("INDEPENDENT_GATE_NOT_APPROVED:" + expected_stage)
    if expected_stage == "verify" and module.endswith("writer_coverage_v0_1"):
        if result.get("activation_authorized") is not False:
            raise PreflightBlocked("COVERAGE_CLAIMS_ACTIVATION")
    if expected_stage == "verify" and module.endswith("writer_activation_v0_1"):
        checks = result.get("checks", {})
        if (checks.get("external_approval") != "SIGNED_PASS"
                or checks.get("deployment_coverage") != "ATTESTED"
                or checks.get("publication") != "REMOTE_REF_AND_BLOBS_PASS"
                or checks.get("external_protocol") != "ENFORCED"):
            raise PreflightBlocked("ACTIVATION_GATE_CHECKS_INCOMPLETE")
    return result


def independent_readback(*, gate_root: Path, writer_root: Path,
                         evidence: Path, expected_evidence_sha: str,
                         decision_path: Path = ATTESTATION_FILE) -> dict[str, Any]:
    decision, before = trusted_decision_snapshot(decision_path)
    coverage_result = _verified_process(root=gate_root,
        module="scripts.coordination.execution_attempt_writer_coverage_v0_1",
        argv=("verify", "--root", ".", "--writer-release-root", str(writer_root),
              "--report", str(evidence)),
        expected_stage="verify", allowed_status="INDEPENDENTLY_ATTESTED_NON_AUTHORIZING")
    if coverage_result.get("evidence_sha256") != expected_evidence_sha:
        raise PreflightBlocked("INDEPENDENT_COVERAGE_EVIDENCE_SHA_DRIFT")
    _verified_process(root=writer_root,
        module="scripts.coordination.execution_attempt_writer_activation_v0_1",
        argv=("verify", "--root", "."),
        expected_stage="verify", allowed_status="PASS")
    # Re-read after *both* verifier invocations; avoid accepting a swapped
    # decision from between independent signature validation and our binding.
    _, after = trusted_decision_snapshot(decision_path)
    if after != before:
        raise PreflightBlocked("SIGNED_DECISION_CHANGED_DURING_READBACK")
    return decision


def attested_runtime_binding(doc: dict[str, Any], decision: dict,
                             *, runtime_sources: dict[str, str]) -> dict[str, Any]:
    """Pure policy evaluator; signer authenticity must be proved by readback."""
    signed = decision.get(SIGNED_EXTENSION_KEY)
    if not isinstance(signed, dict):
        raise PreflightBlocked("SIGNED_RUNTIME_EXTENSION_MISSING")
    expected = {
        "schema_version": SIGNED_EXTENSION_SCHEMA,
        "decision": OPERATOR_DECISION,
        "host": "s01",
        "deployment_root": str(inventory.DEPLOYMENT_PATH),
        "canonical_ledger": inventory.CANONICAL_REL,
        "deployment_git_head": doc["deployment_git_head"],
        "gate_publication_commit": inventory.GATE_COMMIT,
        "writer_publication_commit": inventory.WRITER_COMMIT,
        "technical_coverage_evidence_sha256": doc["coverage_evidence_sha256"],
        "runtime_source_sha256": runtime_sources,
    }
    for field, value in expected.items():
        if signed.get(field) != value:
            raise PreflightBlocked("SIGNED_RUNTIME_BINDING_DRIFT:" + field)
    if (not isinstance(signed.get("independent_operator_review_ref"), str)
            or not signed["independent_operator_review_ref"].strip()):
        raise PreflightBlocked("SIGNED_RUNTIME_REVIEW_REFERENCE_MISSING")
    return signed


def launch_preflight_v0_2(doc: dict[str, Any], decision: dict | None,
                           runtime_sources: dict[str, str] | None,
                           *, independently_verified: bool) -> dict[str, Any]:
    """Allow only after independent release/coverage/signature/lock verification."""
    blockers: list[str] = []
    if not independently_verified:
        blockers.append("INDEPENDENT_GATE_READBACK_NOT_VERIFIED")
    if doc.get("host") != "s01" or doc.get("deployment_checkout") != str(inventory.DEPLOYMENT_PATH):
        blockers.append("DEPLOYMENT_IDENTITY_NOT_S01")
    canonical = doc.get("canonical_ledger", {})
    state = canonical.get("status", {})
    if (state.get("state") != "DIRECTORY" or state.get("uid") != 0
            or state.get("group_writable") or state.get("other_writable")):
        blockers.append("CANONICAL_LEDGER_DAC_NOT_SAFE")
    mount = canonical.get("mount", {})
    if mount.get("network_or_fuse_surface") or mount.get("state") != "OBSERVED":
        blockers.append("CANONICAL_MOUNT_UNVERIFIED")
    proc = doc.get("current_writer_process_observation", {})
    if proc.get("state") != "OBSERVED" or proc.get("unreadable_count") != 0:
        blockers.append("PROCESS_INVENTORY_UNRELIABLE")
    findings = doc.get("findings_requiring_operator_action", [])
    if not isinstance(findings, list) or any(f != ALLOWED_LEGACY_FINDING for f in findings):
        blockers.append("UNREVIEWED_OPERATOR_FINDINGS")
    matches = doc.get("writer_source_comparison", {})
    for path in inventory.TRACKED_WRITERS[-2:]:
        if matches.get(path, {}).get("exact_writer_release_sha256_match") is not True:
            blockers.append("CANONICAL_LEDGER_OR_LOCK_SOURCE_DRIFT:" + path)
    if doc.get("operator_declared_boundary", {}).get("other_hosts_onboarded") is not False:
        blockers.append("REMOTE_HOSTS_SCOPE_CHANGED")
    if decision is None or runtime_sources is None or not independently_verified:
        blockers.append("SIGNED_ACTIVE_RUNTIME_BINDING_REQUIRED")
    else:
        try:
            attested_runtime_binding(doc, decision, runtime_sources=runtime_sources)
        except PreflightBlocked as exc:
            blockers.append(str(exc))
    return {
        "schema_version": SCHEMA,
        "mode": "launch-preflight",
        "status": "BLOCKED" if blockers else "READY_FOR_OPERATOR_MAKE",
        "launch_allowed": not blockers,
        "ledger_append_allowed": not blockers,
        "independent_attestation_verified": bool(independently_verified and decision is not None and not blockers),
        "runtime_binding_authorized": not blockers,
        "blockers": sorted(set(blockers)),
        "external_provisioning_performed": False,
        "worker_launch_performed": False,
        "canonical_ledger_mutation_performed": False,
        "git_commit_push_performed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inspect", "launch-preflight"))
    parser.add_argument("--deployment-root", required=True, type=Path)
    parser.add_argument("--gate-root", required=True, type=Path)
    parser.add_argument("--writer-root", required=True, type=Path)
    parser.add_argument("--coverage-evidence", required=True, type=Path)
    parser.add_argument("--coverage-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        if not re.fullmatch(r"[0-9a-f]{64}", args.coverage_sha256):
            raise PreflightBlocked("COVERAGE_SHA_INVALID")
        if (args.deployment_root.is_symlink()
                or args.deployment_root.resolve() != inventory.DEPLOYMENT_PATH):
            raise PreflightBlocked("DEPLOYMENT_ROOT_NOT_PINNED")
        if Path(__file__).resolve() != (args.deployment_root.resolve() /
                "scripts/coordination/control_plane/s01_writer_runtime_binding_v0_2.py"):
            raise PreflightBlocked("RUNTIME_PREFLIGHT_CODE_NOT_FROM_DEPLOYMENT")
        doc = inventory.build_review(
            deployment_root=args.deployment_root, gate_root=args.gate_root,
            writer_root=args.writer_root, coverage_path=args.coverage_evidence,
            expected_evidence_sha=args.coverage_sha256)
        if args.mode == "inspect":
            result = inventory.binding_summary(doc)
            result["schema_version"] = SCHEMA
            result["runtime_v0_2_readback"] = "NOT_EXECUTED"
            result["runtime_binding_authorized"] = False
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        sources = signed_source_digests(args.deployment_root)
        decision = independent_readback(gate_root=args.gate_root.resolve(),
                                        writer_root=args.writer_root.resolve(),
                                        evidence=args.coverage_evidence.resolve(),
                                        expected_evidence_sha=doc["coverage_evidence_sha256"])
        result = launch_preflight_v0_2(doc, decision, sources, independently_verified=True)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["launch_allowed"] else 2
    except (PreflightBlocked, inventory.InventoryBlocked, OSError, ValueError,
            subprocess.SubprocessError) as exc:
        print(json.dumps({"schema_version": SCHEMA, "mode": args.mode,
            "status": "BLOCKED", "launch_allowed": False,
            "runtime_binding_authorized": False, "blockers": [str(exc)],
            "worker_launch_performed": False}, indent=2, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
