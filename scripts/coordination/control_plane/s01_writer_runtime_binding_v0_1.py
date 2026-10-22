"""Read-only s01 deployment-boundary evidence for CF-10 canonical ledger.

A project-owned runtime binding inventory, NOT the authority-granting
Coverage Gate. It never signs, approves, drains processes, changes permissions,
provisions /etc or /run, launches workers, or writes to the ledger.

Reports facts and *unproven* boundaries; it cannot produce VERIFIED.
The launch preflight deliberately FAILS CLOSED until a separately authorized
runtime binding and external operator attestation are established.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import stat
import subprocess
import sys
from typing import Any

SCHEMA = "cf10_s01_writer_runtime_binding_v0_1"
DEPLOYMENT_PATH = Path("/srv/software_development/forprint-project/forprint_system_blueprint")
GATE_COMMIT = "136088ead1e96624daaf5ef20abf59edf0e6c7ed"
WRITER_COMMIT = "628dd60542c9eefce9db001086ff80fd848e182d"
GATE_REF = "refs/heads/cf10/writer-coverage-indirect-append-v0-4"
WRITER_REF = "refs/heads/cf10/closeout-writer-activation-v0-1"
REMOTE = "git@github.com:Kovalchuk-PrintMaster/Forprint_System_Blueprint.git"
CANONICAL_REL = "coordination/continuity/execution_attempts"
TRACKED_WRITERS = (
    "scripts/coordination/control_plane/governed_worker_cycle.py",
    "scripts/coordination/control_plane/dispatch_intent.py",
    "scripts/coordination/execution_attempt_ledger_v0_1.py",
    "scripts/coordination/execution_attempt_writer_lock_v0_1.py",
)
OUT_OF_SCOPE = (
    "forprint-google-drive-backup.service",
    "forprint-google-drive-backup.timer",
    "forprint-website-preview.service",
)
PROCESS_SCRIPTS = {Path(x).name for x in TRACKED_WRITERS[:3]}
PROCESS_MODULES = {x[:-3].replace("/", ".") for x in TRACKED_WRITERS[:3]}

class InventoryBlocked(RuntimeError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(("git", "-C", str(root), *args), capture_output=True,
                          text=True, timeout=20, check=False)
    if proc.returncode:
        raise InventoryBlocked("GIT_READ_FAILED:" + ":".join(args[:2]))
    return proc.stdout.strip()


def path_status(path: Path) -> dict[str, Any]:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return {"state": "MISSING"}
    except OSError as exc:
        return {"state": "UNREADABLE", "errno": exc.errno}
    if stat.S_ISLNK(info.st_mode):
        kind = "SYMLINK"
    elif stat.S_ISDIR(info.st_mode):
        kind = "DIRECTORY"
    elif stat.S_ISREG(info.st_mode):
        kind = "REGULAR_FILE"
    else:
        kind = "OTHER"
    return {
        "state": kind,
        "uid": info.st_uid,
        "gid": info.st_gid,
        "mode_octal": format(stat.S_IMODE(info.st_mode), "04o"),
        "group_writable": bool(info.st_mode & stat.S_IWGRP),
        "other_writable": bool(info.st_mode & stat.S_IWOTH),
        "device": info.st_dev,
    }


def mount_status(path: Path, mountinfo: Path = Path("/proc/self/mountinfo")) -> dict[str, Any]:
    """Most specific mountpoint. Do not resolve beyond observed deployment path."""
    try:
        lines = mountinfo.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return {"state": "UNKNOWN_MOUNTINFO"}
    resolved_path = path.resolve(strict=False)
    best: tuple[int, dict[str, Any]] | None = None
    for line in lines:
        if " - " not in line:
            continue
        before, after = line.split(" - ", 1)
        left, right = before.split(), after.split()
        if len(left) < 6 or len(right) < 3:
            continue
        point = Path(left[4].replace("\\040", " "))
        try:
            resolved_path.relative_to(point)
        except ValueError:
            continue
        record = {"state": "OBSERVED", "mountpoint": str(point),
                  "filesystem_type": right[0], "mount_options": left[5].split(","),
                  "network_or_fuse_surface": right[0].startswith(("nfs", "cifs", "smb", "fuse", "sshfs", "9p"))}
        score = len(point.parts)
        if best is None or score > best[0]:
            best = (score, record)
    return best[1] if best is not None else {"state": "NOT_FOUND_IN_MOUNTINFO"}


def acl_status(path: Path, executable: str | None = None) -> dict[str, Any]:
    """No ACL means absence of evidence, never proof of exclusive write."""
    program = executable if executable is not None else shutil.which("getfacl")
    if not program:
        return {"state": "NOT_INSPECTED_GETFACL_UNAVAILABLE"}
    if not path.exists() or path.is_symlink():
        return {"state": "NOT_INSPECTED_PATH_UNSAFE_OR_MISSING"}
    try:
        p = subprocess.run((program, "-c", "-p", str(path)), capture_output=True,
                           text=True, timeout=12, check=False)
    except (OSError, subprocess.SubprocessError):
        return {"state": "NOT_INSPECTED_GETFACL_FAILED"}
    if p.returncode:
        return {"state": "NOT_INSPECTED_GETFACL_FAILED", "returncode": p.returncode}
    # Export only ACL grant lines, never file payloads or command lines.
    entries = [s.strip() for s in p.stdout.splitlines()
               if s.strip() and not s.startswith("#")]
    return {"state": "OBSERVED", "entries": entries}


def configured_paths() -> dict[str, dict[str, Any]]:
    paths = {
        "writer_protocol": Path("/etc/forprint/execution_attempt_writer_protocol_v0_1.yaml"),
        "activation_trust_dir": Path("/etc/forprint/execution_attempt_writer_activation"),
        "coverage_attestation": Path("/etc/forprint/execution_attempt_writer_activation/writer_coverage_v0_1.json"),
        "approved_lock_directory": Path("/run/forprint"),
    }
    return {key: path_status(path) for key, path in paths.items()}


def scan_proc(proc_root: Path = Path("/proc")) -> dict[str, Any]:
    observed: list[dict] = []
    unreadable = 0
    try:
        folders = [p for p in proc_root.iterdir() if p.name.isdecimal()]
    except OSError:
        return {"state": "UNREADABLE", "observed": [], "unreadable_count": None}
    for p in folders:
        try:
            argv = [v.decode("utf-8", "replace") for v in
                    (p / "cmdline").read_bytes().split(b"\x00") if v]
        except (FileNotFoundError, ProcessLookupError):
            continue
        except OSError:
            unreadable += 1
            continue
        if not argv:
            continue
        basename = Path(argv[0]).name
        recognized = []
        if basename in PROCESS_SCRIPTS:
            recognized.append(basename)
        if "-m" in argv:
            at = argv.index("-m")
            if at + 1 < len(argv) and argv[at + 1] in PROCESS_MODULES:
                recognized.append(argv[at + 1])
        if basename.startswith(("python", "pypy")):
            for word in argv[1:]:
                if word.startswith("-"):
                    continue
                if Path(word).name in PROCESS_SCRIPTS:
                    recognized.append(Path(word).name)
                break
        if recognized:
            # Never export argv: it may contain sensitive command arguments.
            observed.append({"pid": int(p.name), "entrypoint": sorted(set(recognized))})
    return {"state": "OBSERVED", "observed": sorted(observed, key=lambda x: x["pid"]),
            "unreadable_count": unreadable,
            "absence_of_processes_proven": False}


def check_release(root: Path, commit: str, role: str) -> None:
    if root.is_symlink() or not root.is_dir():
        raise InventoryBlocked(role + "_ROOT_UNSAFE")
    if git(root, "rev-parse", "--show-toplevel") != str(root.resolve()):
        raise InventoryBlocked(role + "_ROOT_NESTED_OR_UNSAFE")
    if git(root, "rev-parse", "HEAD") != commit:
        raise InventoryBlocked(role + "_HEAD_MISMATCH")
    if git(root, "remote", "get-url", "origin") != REMOTE:
        raise InventoryBlocked(role + "_REMOTE_MISMATCH")
    if git(root, "diff", "--name-only") or git(root, "diff", "--cached", "--name-only"):
        raise InventoryBlocked(role + "_CHECKOUT_NOT_CLEAN")
    ref = GATE_REF if role == "GATE" else WRITER_REF
    remote = git(root, "ls-remote", "--exit-code", REMOTE, ref).splitlines()
    if remote != [commit + "\t" + ref]:
        raise InventoryBlocked(role + "_PUBLISHED_REF_DRIFT")


def build_review(*, deployment_root: Path, gate_root: Path, writer_root: Path,
                 coverage_path: Path, expected_evidence_sha: str,
                 hostname: str | None = None, proc_root: Path = Path("/proc"),
                 mountinfo: Path = Path("/proc/self/mountinfo"),
                 check_git: bool = True) -> dict[str, Any]:
    host = (hostname or socket.gethostname()).split(".")[0]
    if host != "s01":
        raise InventoryBlocked("WRONG_HOST_REQUIRES_S01")
    if deployment_root.is_symlink() or not deployment_root.is_dir():
        raise InventoryBlocked("DEPLOYMENT_ROOT_UNSAFE")
    if check_git:
        check_release(gate_root, GATE_COMMIT, "GATE")
        check_release(writer_root, WRITER_COMMIT, "WRITER")
    if not coverage_path.is_file() or coverage_path.is_symlink():
        raise InventoryBlocked("COVERAGE_EVIDENCE_UNAVAILABLE")
    raw = coverage_path.read_bytes()
    evidence_sha = digest(raw)
    if evidence_sha != expected_evidence_sha:
        raise InventoryBlocked("COVERAGE_EVIDENCE_SHA_MISMATCH")
    try:
        coverage = json.loads(raw)
    except (UnicodeError, ValueError) as exc:
        raise InventoryBlocked("COVERAGE_EVIDENCE_INVALID") from exc
    if (coverage_path.parent.resolve() != (gate_root / "tmp").resolve()
            or gate_root.is_symlink()):
        raise InventoryBlocked("COVERAGE_EVIDENCE_NOT_FROM_GATE_TMP")
    if (not isinstance(coverage, dict)
            or coverage.get("gate_publication", {}).get("remote") != REMOTE
            or coverage.get("gate_publication", {}).get("ref") != GATE_REF
            or coverage.get("writer_publication", {}).get("remote") != REMOTE
            or coverage.get("writer_publication", {}).get("ref") != WRITER_REF
            or coverage.get("schema_version") != "forprint_execution_attempt_writer_deployment_evidence_v0_2"
            or coverage.get("status") != "READY_FOR_INDEPENDENT_REVIEW"
            or coverage.get("technical_blockers") != []
            or coverage.get("deployment_coverage_verified") is not False
            or coverage.get("gate_publication", {}).get("commit") != GATE_COMMIT
            or coverage.get("writer_publication", {}).get("commit") != WRITER_COMMIT):
        raise InventoryBlocked("COVERAGE_EVIDENCE_NOT_PINNED_READY")
    deployment_root = deployment_root.absolute()
    canonical = deployment_root / CANONICAL_REL
    canonical_info = path_status(canonical)
    parent_info = path_status(canonical.parent)
    continuity_ancestors = {
        "coordination": path_status(deployment_root / "coordination"),
        "continuity": path_status(deployment_root / "coordination/continuity"),
    }
    writer_digests = {}
    for name in TRACKED_WRITERS:
        live = deployment_root / name
        published = writer_root / name
        pinned = path_status(published)
        observed = path_status(live)
        consistent = (pinned.get("state") == "REGULAR_FILE"
                      and observed.get("state") == "REGULAR_FILE"
                      and digest(live.read_bytes()) == digest(published.read_bytes()))
        writer_digests[name] = {
            "deployment_file": observed,
            "exact_writer_release_sha256_match": consistent,
            "release_sha256": digest(published.read_bytes()) if pinned.get("state") == "REGULAR_FILE" else None,
            "deployment_sha256": digest(live.read_bytes()) if observed.get("state") == "REGULAR_FILE" else None,
        }
    observations = {
        "schema_version": SCHEMA,
        "host": host,
        "operator_declared_boundary": {
            "execution_host": "s01",
            "other_hosts_onboarded": False,
            "remote_hosts_technically_excluded": False,
            "scope_declaration_is_not_access_control_proof": True,
        },
        "coverage_evidence_sha256": evidence_sha,
        "gate_publication_commit": GATE_COMMIT,
        "writer_publication_commit": WRITER_COMMIT,
        "deployment_checkout": str(deployment_root),
        "canonical_ledger": {
            "relative_path": CANONICAL_REL,
            "path": str(canonical),
            "parent_status": parent_info,
            "ancestor_status": continuity_ancestors,
            "status": canonical_info,
            "acl": acl_status(canonical),
            "parent_acl": acl_status(canonical.parent),
            "mount": mount_status(canonical, mountinfo=mountinfo),
        },
        "writer_source_comparison": writer_digests,
        "deployment_git_head": git(deployment_root, "rev-parse", "HEAD") if check_git else "FIXTURE_UNCHECKED",
        "current_writer_process_observation": scan_proc(proc_root),
        "root_controlled_configuration_presence": configured_paths(),
        "excluded_independent_services": list(OUT_OF_SCOPE),
        "verified": False,
        "external_provisioning_performed": False,
        "writer_process_drain_performed": False,
        "process_restart_performed": False,
        "ledger_mutation_performed": False,
        "git_mutation_performed": False,
        "independent_operator_approval_performed": False,
        "unproven_boundaries": [
            "s01_only_is_declared_not_host_acl_or_ssh_exclusivity_proof",
            "short_lived_manual_make_cli_launch_paths_and_other_user_sessions",
            "remote_access_mounts_container_bind_paths_and_indirect_imports",
            "all_writers_enrolled_and_full_drain_restart_not_executed",
            "root_controlled_signed_operator_attestation_not_present_or_unverified",
        ],
    }
    status_issues = []
    if canonical_info["state"] != "DIRECTORY":
        status_issues.append("CANONICAL_LEDGER_NOT_REGULAR_DIRECTORY")
    if parent_info["state"] != "DIRECTORY":
        status_issues.append("CANONICAL_PARENT_NOT_REGULAR_DIRECTORY")
    if any(p["state"] != "DIRECTORY" for p in continuity_ancestors.values()):
        status_issues.append("CANONICAL_ANCESTOR_NOT_REGULAR_DIRECTORY")
    if canonical_info.get("group_writable") or canonical_info.get("other_writable"):
        status_issues.append("CANONICAL_LEDGER_BROAD_DAC_WRITE_SURFACE_REVIEW")
    if any(not row["exact_writer_release_sha256_match"] for row in writer_digests.values()):
        status_issues.append("DEPLOYMENT_WRITER_SOURCE_NOT_EQUAL_PINNED_RELEASE")
    if observations["canonical_ledger"]["mount"].get("network_or_fuse_surface"):
        status_issues.append("CANONICAL_LEDGER_NETWORK_OR_FUSE_MOUNT_REVIEW")
    observations["findings_requiring_operator_action"] = status_issues
    observations["status"] = "OPERATOR_REVIEW_REQUIRED"
    return observations


def write_report(path: Path, deployment_root: Path, doc: dict[str, Any]) -> str:
    expected = deployment_root / "tmp"
    if expected.is_symlink() or not expected.is_dir():
        raise InventoryBlocked("DEPLOYMENT_TMP_UNSAFE_OR_MISSING")
    if path.is_absolute() or path.parent != Path("tmp"):
        raise InventoryBlocked("REPORT_MUST_BE_DIRECT_CHILD_OF_DEPLOYMENT_TMP")
    out = expected / path.name
    if out.exists() or out.is_symlink():
        raise InventoryBlocked("REPORT_EXISTS_CREATE_ONLY")
    raw = (json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(out, flags, 0o600)
    with os.fdopen(fd, "wb") as file:
        file.write(raw)
        file.flush()
        os.fsync(file.fileno())
    return digest(raw)


def binding_summary(doc: dict[str, Any]) -> dict[str, Any]:
    """Actual deployment identity; an observation does not grant run authority."""
    matches = {
        rel: row["exact_writer_release_sha256_match"]
        for rel, row in doc["writer_source_comparison"].items()
    }
    return {
        "schema_version": SCHEMA,
        "host": doc["host"],
        "runtime_root": doc["deployment_checkout"],
        "runtime_git_head": doc["deployment_git_head"],
        "gate_publication_commit": GATE_COMMIT,
        "writer_publication_commit": WRITER_COMMIT,
        "writer_file_matches": matches,
        "all_writer_sources_pinned": all(matches.values()),
        "canonical_ledger_status": doc["canonical_ledger"]["status"],
        "findings": doc["findings_requiring_operator_action"],
        "independent_attestation_verified": False,
        "shared_writer_protocol_enforced": False,
        "runtime_binding_authorized": False,
        "status": "OPERATOR_REVIEW_REQUIRED",
    }


def launch_preflight(doc: dict[str, Any]) -> dict[str, Any]:
    """Operator-facing Make guard; NEVER infer authority from a source scan.

    Until we have explicitly reviewed and integrated an independent trusted
    signed activation readback into this corridor, no launch/ledger-write
    invocation may pass this preflight. Direct Python execution and other
    hosts are OUTSIDE this Make-level control, and remain unproven boundaries.
    """
    summary = binding_summary(doc)
    blockers = ["INDEPENDENT_RUNTIME_BINDING_AND_ACTIVATION_READBACK_NOT_INTEGRATED"]
    if doc["host"] != "s01":
        blockers.append("NOT_S01")
    if not summary["all_writer_sources_pinned"]:
        blockers.append("ACTIVE_WORKTREE_WRITER_SOURCE_DRIFT")
    if doc["canonical_ledger"]["status"].get("uid") != 0:
        blockers.append("CANONICAL_LEDGER_NOT_ROOT_OWNED")
    if doc["canonical_ledger"]["status"].get("state") != "DIRECTORY":
        blockers.append("CANONICAL_LEDGER_NOT_DIRECTORY")
    if doc["findings_requiring_operator_action"]:
        blockers.append("OPERATOR_FINDINGS_PENDING")
    return {
        **summary,
        "status": "BLOCKED",
        "mode": "launch-preflight",
        "launch_allowed": False,
        "ledger_append_allowed": False,
        "blockers": sorted(set(blockers)),
        "external_write_performed": False,
        "worker_launch_performed": False,
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
    parser.add_argument("--report", type=Path, help="Optional, inspect only; create-only direct tmp child")
    args = parser.parse_args(argv)
    try:
        if not re.fullmatch(r"[0-9a-f]{64}", args.coverage_sha256):
            raise InventoryBlocked("INVALID_EXPECTED_EVIDENCE_SHA")
        if args.deployment_root.is_symlink() or args.deployment_root.resolve() != DEPLOYMENT_PATH:
            raise InventoryBlocked("DEPLOYMENT_ROOT_NOT_PINNED_S01_BLUEPRINT")
        doc = build_review(
            deployment_root=args.deployment_root,
            gate_root=args.gate_root,
            writer_root=args.writer_root,
            coverage_path=args.coverage_evidence,
            expected_evidence_sha=args.coverage_sha256,
        )
        result = binding_summary(doc) if args.mode == "inspect" else launch_preflight(doc)
        if args.report is not None:
            if args.mode != "inspect":
                raise InventoryBlocked("PREFLIGHT_CANNOT_WRITE_EVIDENCE")
            result["operator_evidence_sha256"] = write_report(args.report, args.deployment_root, doc)
            result["operator_evidence_path"] = str(args.deployment_root / args.report)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if args.mode == "inspect" else 2
    except (InventoryBlocked, OSError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "runtime_binding_authorized": False,
                          "launch_allowed": False}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
