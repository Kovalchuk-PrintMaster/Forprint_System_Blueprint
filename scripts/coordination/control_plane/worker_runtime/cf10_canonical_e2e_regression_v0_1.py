#!/usr/bin/env python3
"""Non-authorizing source/regression guard for the EXISTING CF10 Worker E2E.

A single operator/CI check for the real canonical chain. This is intentionally
NOT a dispatcher, runner, broker, state store, admission controller or adapter.
Its only output is read-only, machine-readable evidence. No historical result
or fixture may close G1-G5. Live production and credentials remain untouched.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Callable

SCHEMA = "forprint_cf10_canonical_e2e_regression_v0_1"
GATES = ("G1", "G2", "G3", "G4", "G5")
COMPONENTS = {
    "cycle": "scripts/coordination/control_plane/governed_worker_cycle.py",
    "dispatch": "scripts/coordination/control_plane/dispatch_intent.py",
    "adapter": "scripts/coordination/control_plane/worker_runtime/invocation_adapter.py",
    "registry": "scripts/coordination/control_plane/worker_runtime/registry.py",
    "result": "scripts/coordination/control_plane/worker_runtime/worker_result_return.py",
    "systemd_route": "scripts/coordination/control_plane/cf10_r030_canonical_systemd_route_v0_1.py",
    "systemd_backend": "scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py",
    "critical_review": "scripts/coordination/control_plane/worker_runtime/cf10_first_worker_critical_path_v0_1.py",
    "crossplane_review": "scripts/coordination/control_plane/worker_runtime/cf10_first_worker_crossplane_gate_v0_1.py",
    "inference_review": "scripts/coordination/control_plane/worker_runtime/cf10_inference_cutover_readiness_v0_1.py",
    "ai_pre_admission": "scripts/coordination/control_plane/worker_runtime/cf10_ai_pre_admission_contract_v0_1.py",
}
# These are function-level dependencies, not opaque textual presence tests.
REQUIRED_CALLS = {
    ("cycle", "launch_cycle"): (
        "launch_authorized_worker_cycle", "_assert_frozen_source_state_current",
    ),
    ("cycle", "launch_authorized_worker_cycle"): (
        "require_bounded_s01_launch_authority", "modern_route.run_once",
        "execution_attempt_ledger_v0_1.validate_record_data",
    ),
    ("cycle", "advance_cycle"): (
        "dispatch_intent.finalize_cf10_workspace_result_artifact",
        "root_terminal_gate.review_pending_success",
    ),
    ("adapter", "build_launch_invocation"): (
        "registry.resolve_default_runtime", "_validate_authority",
    ),
    ("systemd_route", "run_once"): (
        "assert_cutover_ready", "backend.launch_after_owner_claim",
        "terminal.witnessed_terminal", "durable.record_terminal",
        "handoff.review_success",
    ),
    ("systemd_backend", "launch_after_owner_claim"): (
        "once.open_root_owned_state_dir", "_core",
    ),
}
REQUIRED_FUNCTIONS = {
    "registry": ("resolve_default_runtime",),
    "result": ("materialize_worker_result",),
    "dispatch": ("finalize_cf10_workspace_result_artifact",),
    "critical_review": ("source_check",),
    "crossplane_review": ("current_readonly",),
    "inference_review": ("source_check",),
    "ai_pre_admission": ("source_check",),
}
PROBES = (
    (
        "canonical_crossplane",
        "scripts.coordination.control_plane.worker_runtime.cf10_first_worker_crossplane_gate_v0_1",
        "CF10_AB=PASS_CANONICAL_CROSSPLANE_READONLY",
        True,
    ),
    (
        "first_worker_source_review",
        "scripts.coordination.control_plane.worker_runtime.cf10_first_worker_critical_path_v0_1",
        "CF10_Y=PASS_FIRST_WORKER_GOVERNED_PRELAUNCH_REVIEW_ONLY",
        False,
    ),
    (
        "inference_cutover_review",
        "scripts.coordination.control_plane.worker_runtime.cf10_inference_cutover_readiness_v0_1",
        "CF10_U=PASS_FAIL_CLOSED_CUTOVER_REVIEW_ONLY",
        False,
    ),
)
REQUIRED_PROBE_CLOSURES = (
    "CF10_AB_G1_G5=OPEN_NO_LIVE_WORKER",
    "CF10_Y_G1_G5=OPEN_NO_RELEASE",
    "CF10_U_G1_G5=OPEN_NO_LIVE_AUTHORITY",
)
_SHA40 = re.compile(r"[a-f0-9]{40}\Z")


class RegressionHold(RuntimeError):
    """An observational contract failed; never fall back to live work."""


def _qualified_call(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        root = _qualified_call(node.value)
        return root + "." + node.attr if root else None
    return None


def _calls(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    return {
        name
        for node in ast.walk(fn)
        if isinstance(node, ast.Call)
        if (name := _qualified_call(node.func)) is not None
    }


def _function(tree: ast.Module, name: str):
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _top_level_bool(tree: ast.Module, name: str):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
                return node.value.value if isinstance(node.value, ast.Constant) else None
    return None


def _pin_and_parse(root: Path, rel: str) -> tuple[ast.Module, str]:
    # A symlink at any parent can redirect an otherwise canonical path.
    parent = root
    for part in Path(rel).parts:
        parent = parent / part
        if parent.is_symlink():
            raise RegressionHold("SYMLINK_COMPONENT_PATH")
    if not parent.is_file():
        raise RegressionHold("MISSING_CANONICAL_COMPONENT")
    if parent.stat().st_size > 2_000_000:
        raise RegressionHold("CANONICAL_COMPONENT_OVERSIZE")
    data = parent.read_bytes()
    try:
        tree = ast.parse(data, filename=rel)
    except (SyntaxError, UnicodeError, ValueError) as exc:
        raise RegressionHold("CANONICAL_COMPONENT_PARSE_ERROR") from exc
    return tree, hashlib.sha256(data).hexdigest()


def inspect_graph(root: Path | str) -> dict:
    """Confirm exact E2E reuse seams through Python AST, without imports."""
    root = Path(root).absolute()
    if root.is_symlink() or not root.is_dir():
        raise RegressionHold("BAD_REPOSITORY_ROOT")
    trees = {}
    hashes = {}
    for key, rel in COMPONENTS.items():
        tree, digest = _pin_and_parse(root, rel)
        trees[key], hashes[key] = tree, digest

    checks = {}
    for (key, function), needed in REQUIRED_CALLS.items():
        fn = _function(trees[key], function)
        missing = sorted(set(needed) - (_calls(fn) if fn else set()))
        checks[f"{key}.{function}"] = {"valid": not missing, "missing_calls": missing}
    for key, names in REQUIRED_FUNCTIONS.items():
        absent = sorted(name for name in names if _function(trees[key], name) is None)
        checks[f"{key}.entrypoints"] = {"valid": not absent, "missing_functions": absent}

    launch = _function(trees["cycle"], "launch_authorized_worker_cycle")
    # The existing subprocess launcher remains for historical proofs, never as
    # a privileged/canonical production fallback.
    no_legacy = bool(launch) and "launcher.launch_process" not in _calls(launch)
    checks["no_legacy_production_fallback"] = {"valid": no_legacy}
    backend_closed = _top_level_bool(trees["systemd_backend"], "LIVE_CUTOVER_ENABLED") is False
    checks["production_backend_cutover_source_sealed"] = {"valid": backend_closed}
    valid = all(row["valid"] for row in checks.values())
    return {
        "status": "PASS_CANONICAL_E2E_REUSE_GRAPH" if valid else "HOLD_CANONICAL_E2E_REUSE_GRAPH",
        "graph_valid": valid,
        "checks": checks,
        "component_sha256": hashes,
        "canonical_production_cutover_closed": backend_closed,
        "source_analysis_only": True,
    }


def _safe_git_head(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["/usr/bin/git", "-C", str(root), "rev-parse", "HEAD"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL, timeout=10, check=False,
            env={"PATH": "/usr/bin:/bin", "LANG": "C"},
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode:
        return None
    sha = result.stdout.decode("ascii", errors="ignore").strip()
    return sha if _SHA40.fullmatch(sha) else None


def probe_existing_source_checks(
    root: Path | str,
    runner: Callable | None = None,
) -> dict:
    """Invoke only existing *non-authorizing* source-check CLIs, never launch."""
    root = Path(root).absolute()
    run = subprocess.run if runner is None else runner
    rows: dict[str, dict] = {}
    env = {
        "PATH": "/usr/bin:/bin", "LANG": "C", "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(root), "HOME": "/nonexistent",
    }
    for index, (label, module, marker, with_root) in enumerate(PROBES):
        argv = [sys.executable, "-m", module, "--mode", "source-check"]
        if with_root:
            argv.extend(("--root", str(root)))
        try:
            done = run(
                argv, cwd=str(root), env=env, check=False,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL, timeout=35,
            )
            raw = done.stdout.decode("utf-8", errors="replace")[:4096]
            lines = raw.splitlines()
            passed = done.returncode == 0 and marker in lines and REQUIRED_PROBE_CLOSURES[index] in lines
            rows[label] = {
                "status": "PASS_READONLY_CANONICAL_SOURCE" if passed else "HOLD_SOURCE_CHECK",
                "exit_code": done.returncode,
                "positive_marker_found": marker in lines,
                "gates_still_open_marker_found": REQUIRED_PROBE_CLOSURES[index] in lines,
            }
        except (OSError, subprocess.SubprocessError, TypeError, AttributeError):
            rows[label] = {
                "status": "HOLD_SOURCE_CHECK_RUNNER",
                "exit_code": None,
                "positive_marker_found": False,
                "gates_still_open_marker_found": False,
            }
    return {
        "all_existing_checks_pass": all(v["status"] == "PASS_READONLY_CANONICAL_SOURCE" for v in rows.values()),
        "checks": rows,
    }


def build_report(root: Path | str, mode: str = "source-only", runner: Callable | None = None) -> dict:
    if mode not in ("source-only", "crossplane"):
        raise RegressionHold("UNSUPPORTED_MODE")
    root = Path(root).absolute()
    report = {
        "schema": SCHEMA,
        "authority": "OBSERVATIONAL_ONLY_NO_LAUNCH_OR_APPROVAL",
        "mode": mode,
        "repository_head": _safe_git_head(root),
        "gates_open": list(GATES),
        "real_authenticated_inference_proven": False,
        "root_owned_credential_delegation_proven": False,
        "production_claim_consumed": False,
        "automatic_retry": False,
        "git_commit_performed": False,
        "git_push_performed": False,
        "live_worker_authorized": False,
        "graph": {},
        "canonical_source_checks": {"not_run": True},
        "blockers": [
            "G1_REAL_WORKER_PROVIDER_EGRESS_NOT_ATTESTED",
            "G2_SECRET_NONEXPOSURE_AND_AUTH_DELEGATION_NOT_ATTESTED",
            "G3_REAL_MODEL_INFERENCE_NOT_ATTESTED",
            "G4_CANONICAL_DISPATCHER_LIVE_RELEASE_NOT_ATTESTED",
            "G5_REAL_WORKER_TERMINAL_LEDGER_AND_RECOVERY_NOT_ATTESTED",
        ],
    }
    try:
        report["graph"] = inspect_graph(root)
    except (RegressionHold, OSError) as exc:
        report["graph"] = {"status": "HOLD_GRAPH_INSPECTION", "failure_class": type(exc).__name__}
    valid = report["graph"].get("graph_valid") is True
    if mode == "crossplane" and valid:
        report["canonical_source_checks"] = probe_existing_source_checks(root, runner=runner)
        valid = report["canonical_source_checks"]["all_existing_checks_pass"] is True
    report["status"] = (
        "PASS_SOURCE_INTEGRATION_ONLY_NO_LIVE_AUTHORITY" if valid
        else "HOLD_CANONICAL_E2E_SOURCE_INTEGRATION"
    )
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--mode", choices=("source-only", "crossplane"), default="source-only")
    args = parser.parse_args(argv)
    # Output contains only summary checks, safe digests and symbolic blockers.
    report = build_report(args.root, args.mode)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if report["status"] == "PASS_SOURCE_INTEGRATION_ONLY_NO_LIVE_AUTHORITY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
