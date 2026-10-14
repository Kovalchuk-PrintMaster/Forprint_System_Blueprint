"""Non-authorizing technical evidence for shared execution-ledger writer coverage.

Only project tmp evidence is writable. This module does not create root-owned
coverage attestations, sign, deploy, drain Workers, change Git or activate ENFORCED.
A scan of this host can never prove the absence of remote or short-lived writers.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
from typing import Callable

from scripts.coordination import execution_attempt_writer_activation_v0_1 as gate

SCHEMA = "forprint_execution_attempt_writer_deployment_evidence_v0_2"
CONTRACT = "coordination/standards/automation/control_plane/execution_attempt_writer_deployment_coverage_contract_v0_1.yaml"
PUBLISHED_COMMIT = "628dd60542c9eefce9db001086ff80fd848e182d"
PUBLISHED_REMOTE = "git@github.com:Kovalchuk-PrintMaster/Forprint_System_Blueprint.git"
PUBLISHED_REF = "refs/heads/cf10/closeout-writer-activation-v0-1"
# This ref must be independently published before a real plan can be READY.
# Its commit is read from BOTH the gate checkout and this exact remote ref;
# independent attestation must pin the resulting immutable commit SHA.
GATE_REF = "refs/heads/cf10/writer-coverage-dual-release-v0-3"
GATE_SOURCE_FILES = (
    "scripts/coordination/execution_attempt_writer_coverage_v0_1.py",
    "scripts/coordination/execution_attempt_writer_activation_v0_1.py",
    "scripts/coordination/execution_attempt_writer_lock_v0_1.py",
    "tests/coordination/test_execution_attempt_writer_coverage_v0_1.py",
    "coordination/standards/automation/control_plane/execution_attempt_writer_deployment_coverage_contract_v0_1.yaml",
    "coordination/work_fronts/blueprint_shared_execution_attempt_writer_deployment_coverage_v0_1.yaml",
    "Makefile",
)
REQUIRED = (
    "scripts/coordination/control_plane/governed_worker_cycle.py",
    "scripts/coordination/control_plane/dispatch_intent.py",
    "scripts/coordination/execution_attempt_ledger_v0_1.py",
)
SCRIPT_ROOT = Path("scripts/coordination")
SCHEDULE_ROOTS = (
    Path("/etc/crontab"), Path("/etc/cron.d"),
    Path("/var/spool/cron/crontabs"), Path("/etc/systemd/system"),
    Path("/lib/systemd/system"), Path("/usr/lib/systemd/system"),
)
TRIGGER_TERMS = (
    "execution_attempt_ledger", "governed_worker_cycle", "dispatch_intent",
    "cf10_training_dispatch", "forprint_system_blueprint",
)
MAX_FILES = 15000
MAX_BYTES = 2 * 1024 * 1024

# Executable writer entrypoints only. Do not use TRIGGER_TERMS here: it also
# includes the repository name, which appears in every venv Python path and
# would make plan/check observe their own short-lived control processes.
PROCESS_WRITER_MODULES = {
    "scripts.coordination.control_plane.governed_worker_cycle": "governed_worker_cycle",
    "scripts.coordination.control_plane.dispatch_intent": "dispatch_intent",
    "scripts.coordination.control_plane.cf10_training_dispatch": "cf10_training_dispatch",
    "scripts.coordination.execution_attempt_ledger_v0_1": "execution_attempt_ledger",
}
PROCESS_WRITER_SCRIPTS = {
    "governed_worker_cycle.py": "governed_worker_cycle",
    "dispatch_intent.py": "dispatch_intent",
    "cf10_training_dispatch.py": "cf10_training_dispatch",
    "execution_attempt_ledger_v0_1.py": "execution_attempt_ledger",
}


def process_writer_terms(argv: list[str]) -> list[str]:
    """Recognize direct Python entrypoints, not incidental arguments/paths.

    Shell/Make/remote wrappers and dynamic imports are NOT proven safe here;
    they remain explicit boundaries for independent deployment attestation.
    """
    if not argv:
        return []
    program = Path(argv[0]).name.lower()
    # Allow a directly executable Python script (shebang invocation).
    if program in PROCESS_WRITER_SCRIPTS:
        return [PROCESS_WRITER_SCRIPTS[program]]
    if not re.fullmatch(r"(?:python(?:[0-9]+(?:\.[0-9]+)?)?|pypy[0-9]*)", program):
        return []
    args = argv[1:]
    if "-c" in args:
        return []
    if "-m" in args:
        pos = args.index("-m")
        return [PROCESS_WRITER_MODULES[args[pos + 1]]] if pos + 1 < len(args) and args[pos + 1] in PROCESS_WRITER_MODULES else []
    # The first non-option argument is the script; further args are data and
    # must never count as executed writer code.
    for arg in args:
        if arg.startswith("-"):
            continue
        name = Path(arg).name
        return [PROCESS_WRITER_SCRIPTS[name]] if name in PROCESS_WRITER_SCRIPTS else []
    return []


class CoverageBlocked(RuntimeError):
    pass


def canon(value: dict) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_bytes(root: Path, *args: str) -> bytes:
    try:
        completed = subprocess.run(["git", *args], cwd=root, capture_output=True, check=True,
                                   timeout=20)
    except (OSError, subprocess.SubprocessError) as error:
        raise CoverageBlocked("GIT_PROBE_FAILED:" + " ".join(args[:2])) from error
    return completed.stdout


def git(root: Path, *args: str) -> str:
    return git_bytes(root, *args).decode().strip()


def _pinned_root(root: Path, role: str) -> None:
    if root.is_symlink() or not root.is_dir() or git(root, "rev-parse", "--show-toplevel") != str(root.resolve()):
        raise CoverageBlocked("UNSAFE_OR_NESTED_" + role + "_CHECKOUT")


def _remote_commit(root: Path, remote: str, ref: str,
                   probe: Callable[[str, str], str] | None) -> str:
    if probe is not None:
        result = probe(remote, ref)
    else:
        lines = git(root, "ls-remote", "--exit-code", remote, ref).splitlines()
        parts = lines[0].split("\t") if len(lines) == 1 else []
        result = parts[0] if len(parts) == 2 and parts[1] == ref else ""
    if not isinstance(result, str) or not re.fullmatch(r"[a-f0-9]{40}", result):
        raise CoverageBlocked("REMOTE_REF_UNTRUSTED_OR_UNAVAILABLE:" + ref)
    return result


def publication_bindings(gate_root: Path, writer_release_root: Path) -> dict:
    """Local identities; release_checks independently verifies remotes and blobs."""
    def digests(root: Path, paths) -> dict[str, str]:
        result = {}
        for rel in sorted(set(paths)):
            file = root / rel
            if not file.is_file() or file.is_symlink():
                raise CoverageBlocked("PUBLICATION_SOURCE_UNSAFE_OR_MISSING:" + rel)
            result[rel] = sha(file.read_bytes())
        return result
    return {
        "gate_publication": {
            "commit": git(gate_root, "rev-parse", "HEAD"),
            "remote": PUBLISHED_REMOTE, "ref": GATE_REF,
            "source_sha256": digests(gate_root, GATE_SOURCE_FILES),
        },
        "writer_publication": {
            "commit": PUBLISHED_COMMIT,
            "remote": PUBLISHED_REMOTE, "ref": PUBLISHED_REF,
            "source_sha256": digests(writer_release_root, (*REQUIRED, *gate.SOURCES)),
        },
    }


def release_checks(gate_root: Path, writer_release_root: Path,
                   remote_probe: Callable[[str, str], str] | None = None) -> list[str]:
    """Independently verify two checkouts. Never equate local HEAD with publication.

    The coverage checker and its tests must match a *published* Git tree on
    its own gate ref, while writer sources are pinned to the immutable 628dd...
    release. No mutable status flag can substitute for either comparison.
    """
    errors = []
    try:
        _pinned_root(gate_root, "GATE")
        _pinned_root(writer_release_root, "WRITER")
        if gate_root.resolve() == writer_release_root.resolve():
            errors.append("GATE_AND_WRITER_ROOT_MUST_DIFFER")
        if git(gate_root, "remote", "get-url", "origin") != PUBLISHED_REMOTE:
            errors.append("GATE_REMOTE_URL_NOT_PINNED")
        if git(writer_release_root, "remote", "get-url", "origin") != PUBLISHED_REMOTE:
            errors.append("WRITER_REMOTE_URL_NOT_PINNED")
        gate_commit = git(gate_root, "rev-parse", "HEAD")
        if _remote_commit(gate_root, PUBLISHED_REMOTE, GATE_REF, remote_probe) != gate_commit:
            errors.append("GATE_REF_NOT_EQUAL_CHECKOUT_HEAD")
        if git(writer_release_root, "rev-parse", "HEAD") != PUBLISHED_COMMIT:
            errors.append("WRITER_CHECKOUT_NOT_PINNED_RELEASE")
        if _remote_commit(writer_release_root, PUBLISHED_REMOTE, PUBLISHED_REF, remote_probe) != PUBLISHED_COMMIT:
            errors.append("WRITER_PUBLISHED_REF_DRIFT")
        for rel in GATE_SOURCE_FILES:
            live = gate_root / rel
            if not live.is_file() or live.is_symlink():
                errors.append("GATE_SOURCE_MISSING_OR_SYMLINK:" + rel)
                continue
            if sha(live.read_bytes()) != sha(git_bytes(gate_root, "show", f"{gate_commit}:{rel}")):
                errors.append("GATE_SOURCE_NOT_PUBLISHED:" + rel)
        for rel, expected in gate.SOURCES.items():
            path = writer_release_root / rel
            if not path.is_file() or path.is_symlink() or sha(path.read_bytes()) != expected:
                errors.append("PINNED_WRITER_SOURCE_DRIFT:" + rel)
            if sha(git_bytes(writer_release_root, "show", f"{PUBLISHED_COMMIT}:{rel}")) != expected:
                errors.append("WRITER_PUBLISHED_BLOB_DRIFT:" + rel)
        for rel in REQUIRED:
            path = writer_release_root / rel
            if not path.is_file() or path.is_symlink():
                errors.append("WRITER_ENTRYPOINT_MISSING:" + rel)
            elif sha(path.read_bytes()) != sha(git_bytes(writer_release_root, "show", f"{PUBLISHED_COMMIT}:{rel}")):
                errors.append("WRITER_ENTRYPOINT_WORKTREE_DRIFT:" + rel)
    except (CoverageBlocked, OSError, UnicodeError) as exc:
        errors.append("DUAL_PUBLICATION_PROBE_INCOMPLETE:" + str(exc))
    return sorted(set(errors))


LEDGER_MODULE = "scripts.coordination.execution_attempt_ledger_v0_1"
HISTORY_MODULE = "scripts.coordination.workfront_history_v0_1"


def append_call_binding(tree: ast.Module, call: ast.Call, rel: str,
                        shadowed: set[str]) -> str | None:
    """Classify the obvious bindings; unresolved calls remain operator-review candidates.

    AST inspection is intentionally conservative. It is not a proof about
    dynamic imports, monkeypatching, nested shadowing, or runtime dispatch.
    """
    imports: dict[str, str] = {}
    for statement in tree.body:
        if isinstance(statement, ast.Import):
            for item in statement.names:
                if item.name in (LEDGER_MODULE, HISTORY_MODULE):
                    # `import pkg.submodule` binds `pkg`; an alias binds module.
                    imports[item.asname or item.name.split('.')[0]] = item.name if item.asname else item.name.split('.')[0]
        elif isinstance(statement, ast.ImportFrom):
            module = statement.module or ''
            for item in statement.names:
                name = item.asname or item.name
                if module == 'scripts.coordination' and item.name in (
                    'execution_attempt_ledger_v0_1', 'workfront_history_v0_1'
                ):
                    imports[name] = module + '.' + item.name
                elif module in (LEDGER_MODULE, HISTORY_MODULE) and item.name == 'append_record':
                    imports[name] = module + '.append_record'
    target = call.func
    is_ledger_file = rel == LEDGER_MODULE.replace('.', '/') + '.py'
    is_history_file = rel == HISTORY_MODULE.replace('.', '/') + '.py'
    if isinstance(target, ast.Name):
        binding = imports.get(target.id)
        if binding == LEDGER_MODULE + '.append_record':
            return 'EXECUTION_LEDGER_IMPORTED_APPEND'
        if binding == HISTORY_MODULE + '.append_record':
            return 'STATIC_CALLSITE_REQUIRES_REVIEW' if target.id in shadowed else None
        if target.id != 'append_record':
            return None
        if is_ledger_file:
            return 'EXECUTION_LEDGER_LOCAL_APPEND'
        # Confirm the locally defined method is the Work Front History API.
        if is_history_file and 'append_record' not in shadowed and any(
            isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) and stmt.name == 'append_record'
            for stmt in tree.body
        ) and not any(
            isinstance(stmt, ast.ImportFrom) and any(
                (item.asname or item.name) == 'append_record' for item in stmt.names
            ) for stmt in tree.body
        ):
            return None
        return 'STATIC_CALLSITE_REQUIRES_REVIEW'
    if isinstance(target, ast.Attribute) and target.attr == 'append_record':
        value = target.value
        if isinstance(value, ast.Name) and imports.get(value.id) == LEDGER_MODULE:
            return 'EXECUTION_LEDGER_IMPORT_BOUND'
        if isinstance(value, ast.Name) and imports.get(value.id) == HISTORY_MODULE:
            return 'STATIC_CALLSITE_REQUIRES_REVIEW' if value.id in shadowed else None
        if isinstance(value, ast.Attribute) and value.attr == 'execution_attempt_ledger_v0_1':
            return 'STATIC_CALLSITE_REQUIRES_REVIEW'
        return 'STATIC_CALLSITE_REQUIRES_REVIEW'
    return None


def scan_call_sites(root: Path) -> tuple[list[dict], list[str]]:
    """Import-aware AST candidates, never an exhaustive dynamic writer proof."""
    directory = root / SCRIPT_ROOT
    if not directory.is_dir() or directory.is_symlink():
        return [], ['SCRIPT_ROOT_UNSAFE_OR_MISSING']
    candidates, problems = [], []
    files = sorted(directory.rglob('*.py'))
    if len(files) > MAX_FILES:
        return [], ['SCRIPT_INVENTORY_TOO_LARGE']
    for path in files:
        rel = path.relative_to(root).as_posix()
        if path.is_symlink() or path.stat().st_size > MAX_BYTES:
            problems.append('SOURCE_NOT_SCANNED:' + rel)
            continue
        try:
            tree = ast.parse(path.read_text(encoding='utf-8'), filename=rel)
        except (SyntaxError, UnicodeError, OSError):
            problems.append('SOURCE_PARSE_FAILED:' + rel)
            continue
        nodes = list(ast.walk(tree))
        # Even a normally known history import is not safe to exclude if any
        # function argument, local assignment or nested import can rebind it.
        shadowed = {node.id for node in nodes if isinstance(node, ast.Name)
                    and isinstance(node.ctx, ast.Store)}
        shadowed.update(node.arg for node in nodes if isinstance(node, ast.arg))
        for node in nodes:
            if node is not tree and node not in tree.body and isinstance(node, (ast.Import, ast.ImportFrom)):
                shadowed.update(item.asname or item.name.split('.')[0] for item in node.names)
        for node in nodes:
            if isinstance(node, ast.Call):
                classification = append_call_binding(tree, node, rel, shadowed)
                if classification is not None:
                    candidates.append({'file': rel, 'line': node.lineno,
                                       'classification': classification})
    return sorted(candidates, key=lambda row: (row['file'], row['line'])), sorted(problems)


def scan_processes(proc: Path = Path("/proc")) -> tuple[list[dict], list[str]]:
    observed, errors = [], []
    try:
        pids = sorted((p for p in proc.iterdir() if p.name.isdecimal()), key=lambda p: int(p.name))
    except OSError:
        return [], ["PROC_UNREADABLE"]
    for folder in pids:
        if proc == Path("/proc") and folder.name == str(os.getpid()):
            continue
        try:
            raw = (folder / "cmdline").read_bytes()
        except (FileNotFoundError, ProcessLookupError):
            continue
        except (PermissionError, OSError):
            errors.append("PROCESS_NOT_INSPECTABLE:" + folder.name)
            continue
        argv = [arg.decode("utf-8", "replace") for arg in raw.split(b"\x00") if arg]
        matched = process_writer_terms(argv)
        if matched:
            # Never export raw command lines: arguments may contain secrets.
            observed.append({"pid": int(folder.name), "matching_terms": matched})
    return observed, errors


def scan_schedules(roots: tuple[Path, ...] = SCHEDULE_ROOTS) -> tuple[list[dict], list[str]]:
    """Inspect resolved in-scope units once; do not silently trust unsafe links.

    Files reached through /lib -> /usr/lib or systemd alias symlinks are
    identified by their canonical target, avoiding duplicate warnings/results.
    A missing, cyclic or out-of-scope symlink remains explicit review evidence.
    """
    matches: list[dict] = []
    errors: list[str] = []
    scanned: set[Path] = set()
    count = 0
    allowed: list[Path] = []
    for root in roots:
        try:
            if root.exists():
                allowed.append(root.resolve(strict=True))
        except (OSError, RuntimeError):
            pass

    def in_scope(target: Path) -> bool:
        return any(target == base or (base.is_dir() and target.is_relative_to(base))
                   for base in allowed)

    for root in roots:
        if not root.exists() and not root.is_symlink():
            continue
        try:
            base = root.resolve(strict=True)
        except (OSError, RuntimeError):
            errors.append('SCHEDULE_SYMLINK_UNREVIEWED:' + str(root))
            continue
        if not in_scope(base):
            errors.append('SCHEDULE_SYMLINK_UNREVIEWED:' + str(root))
            continue
        try:
            paths = [root] if base.is_file() else list(root.rglob('*')) if base.is_dir() else []
        except (OSError, RuntimeError):
            errors.append('SCHEDULE_UNREADABLE:' + str(root))
            continue
        for path in paths:
            count += 1
            if count > MAX_FILES:
                errors.append('SCHEDULE_SCAN_LIMIT_EXCEEDED')
                return sorted(matches, key=lambda r: r['path']), sorted(set(errors))
            try:
                canonical = path.resolve(strict=True)
            except (OSError, RuntimeError):
                if path.is_symlink():
                    errors.append('SCHEDULE_SYMLINK_UNREVIEWED:' + str(path))
                else:
                    errors.append('SCHEDULE_UNREADABLE:' + str(path))
                continue
            if not in_scope(canonical):
                errors.append('SCHEDULE_SYMLINK_UNREVIEWED:' + str(path))
                continue
            if canonical.is_dir():
                continue
            if canonical in scanned:
                continue
            scanned.add(canonical)
            try:
                if not canonical.is_file() or canonical.stat().st_size > MAX_BYTES:
                    errors.append('SCHEDULE_FILE_UNREVIEWED:' + str(canonical))
                    continue
                content = canonical.read_text(encoding='utf-8', errors='replace').lower()
                hits = sorted(term for term in TRIGGER_TERMS if term in content)
                if hits:
                    matches.append({'path': str(canonical), 'matching_terms': hits})
            except (PermissionError, OSError):
                errors.append('SCHEDULE_UNREADABLE:' + str(canonical))
    return sorted(matches, key=lambda x: x['path']), sorted(set(errors))


def build_plan(root: Path, *, writer_release_root: Path,
               remote_probe=None,
               process_root: Path = Path("/proc"),
               schedule_roots: tuple[Path, ...] = SCHEDULE_ROOTS) -> dict:
    root = root.absolute()
    writer_release_root = writer_release_root.absolute()
    try:
        bindings = publication_bindings(root, writer_release_root)
    except (CoverageBlocked, OSError) as exc:
        bindings = {"gate_publication": None, "writer_publication": None}
        identity_errors = ["PUBLICATION_IDENTITY_UNAVAILABLE:" + str(exc)]
    else:
        identity_errors = []
    errors = identity_errors + release_checks(root, writer_release_root, remote_probe)
    # Inspect writer code, not the independently published verifier implementation.
    callsites, code_errors = scan_call_sites(writer_release_root)
    processes, process_errors = scan_processes(process_root)
    schedules, schedule_errors = scan_schedules(schedule_roots)
    # Symlinked systemd aliases are not proof of an executable writer; keep them
    # visible for independent review, but do not make technical readiness
    # permanently impossible on a normal Debian installation.
    schedule_review = sorted(e for e in schedule_errors if e.startswith("SCHEDULE_SYMLINK_UNREVIEWED:"))
    schedule_blockers = [e for e in schedule_errors if e not in schedule_review]
    blockers = sorted(set(errors + code_errors + process_errors + schedule_blockers))
    return {
        "schema_version": SCHEMA,
        "status": "BLOCKED" if blockers else "READY_FOR_INDEPENDENT_REVIEW",
        **bindings,
        "known_writer_entrypoints": list(REQUIRED),
        "static_callsite_candidates": callsites,
        "observed_writer_processes": processes,
        "observed_scheduler_references": schedules,
        "unreviewed_scheduler_symlinks": schedule_review,
        "technical_blockers": blockers,
        "unproven_boundaries": [
            "short_lived_cli_and_manual_Make_invocations",
            "user_systemd_and_remote_or_other_host_writers",
            "dynamic_import_or_indirect_writer_paths",
            "complete_process_drain_restart_and_lock_eligibility",
        ],
        "independent_operator_review_required": True,
        "deployment_coverage_verified": False,
        "external_provisioning_performed": False,
        "git_mutation_performed": False,
    }


def safe_tmp_destination(root: Path, requested: Path) -> Path:
    root = root.resolve()
    tmp = root / "tmp"
    if not tmp.exists() and not tmp.is_symlink():
        tmp.mkdir(mode=0o700)
    if tmp.is_symlink() or not tmp.is_dir():
        raise CoverageBlocked("PROJECT_TMP_UNSAFE")
    target = requested if requested.is_absolute() else root / requested
    # No path tricks, nested symlinks or writes outside tmp. Review artifacts only.
    if target.parent.resolve() != tmp.resolve() or target.name in ("", ".", ".."):
        raise CoverageBlocked("OUTPUT_MUST_BE_DIRECT_CHILD_OF_PROJECT_TMP")
    if target.exists() or target.is_symlink():
        raise CoverageBlocked("OUTPUT_EXISTS_CREATE_ONLY")
    return target


def write_plan(root: Path, path: Path, doc: dict) -> tuple[Path, str]:
    out = safe_tmp_destination(root, path)
    content = canon(doc)
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "wb") as file:
        file.write(content)
        file.flush()
        os.fsync(file.fileno())
    return out, sha(content)


def check_plan(root: Path, path: Path, *, writer_release_root: Path, remote_probe=None) -> dict:
    file = path if path.is_absolute() else root / path
    expected_parent = (root / "tmp").resolve()
    if file.is_symlink() or file.parent.resolve() != expected_parent or not file.is_file():
        raise CoverageBlocked("PLAN_MUST_BE_REGULAR_PROJECT_TMP_FILE")
    # A plan is untrusted evidence: never let it set external authority.
    try:
        raw = file.read_bytes()
        doc = json.loads(raw)
    except (OSError, ValueError) as exc:
        raise CoverageBlocked("PLAN_UNREADABLE_OR_INVALID") from exc
    if not isinstance(doc, dict) or canon(doc) != raw or doc.get("schema_version") != SCHEMA:
        raise CoverageBlocked("PLAN_NOT_CANONICAL")
    try:
        bindings = publication_bindings(root, writer_release_root)
    except (CoverageBlocked, OSError) as exc:
        raise CoverageBlocked("DUAL_PUBLICATION_IDENTITY_UNAVAILABLE") from exc
    if doc.get("gate_publication") != bindings["gate_publication"]:
        raise CoverageBlocked("PLAN_GATE_PUBLICATION_BINDING_DRIFT")
    if doc.get("writer_publication") != bindings["writer_publication"]:
        raise CoverageBlocked("PLAN_WRITER_PUBLICATION_BINDING_DRIFT")
    if doc.get("known_writer_entrypoints") != list(REQUIRED):
        raise CoverageBlocked("PLAN_WRITER_SET_DRIFT")
    if doc.get("deployment_coverage_verified") is not False or doc.get("independent_operator_review_required") is not True:
        raise CoverageBlocked("PLAN_FALSE_AUTHORITY")
    if doc.get("external_provisioning_performed") is not False or doc.get("git_mutation_performed") is not False:
        raise CoverageBlocked("PLAN_FALSE_MUTATION_CLAIM")
    blockers = release_checks(root, writer_release_root, remote_probe)
    # Dynamic observations are evidence, not a one-time permission token.
    current_callsites, source_errors = scan_call_sites(writer_release_root)
    current_processes, process_errors = scan_processes()
    current_schedules, schedule_errors = scan_schedules()
    if doc.get("static_callsite_candidates") != current_callsites:
        blockers.append("STATIC_WRITER_CALLSITE_DRIFT_REGENERATE_PLAN")
    if doc.get("observed_writer_processes") != current_processes:
        blockers.append("PROCESS_INVENTORY_CHANGED_REGENERATE_PLAN")
    if doc.get("observed_scheduler_references") != current_schedules:
        blockers.append("SCHEDULE_INVENTORY_CHANGED_REGENERATE_PLAN")
    current_symlinks = sorted(e for e in schedule_errors if e.startswith("SCHEDULE_SYMLINK_UNREVIEWED:"))
    if doc.get("unreviewed_scheduler_symlinks") != current_symlinks:
        blockers.append("SCHEDULE_SYMLINK_INVENTORY_CHANGED_REGENERATE_PLAN")
    blockers.extend(source_errors + process_errors + [e for e in schedule_errors if e not in current_symlinks])
    if doc.get("technical_blockers"):
        blockers.append("PLAN_HAS_UNRESOLVED_TECHNICAL_BLOCKERS")
    return {
        "stage": "check", "status": "BLOCKED" if blockers else "READY_FOR_INDEPENDENT_REVIEW",
        "blockers": sorted(set(blockers)), "evidence_sha256": sha(raw),
        "deployment_coverage_verified": False, "independent_operator_review_required": True,
        "canonical_closeout_performed": False, "external_provisioning_performed": False,
    }


def verify_coverage(root: Path, path: Path, *, writer_release_root: Path, remote_probe=None) -> dict:
    checked = check_plan(root, path, writer_release_root=writer_release_root, remote_probe=remote_probe)
    errors = list(checked["blockers"])
    if checked["status"] != "READY_FOR_INDEPENDENT_REVIEW":
        errors.append("TECHNICAL_PLAN_NOT_READY")
    try:
        doc, _ = gate.trusted_json(gate.COVERAGE_FILE)
        gate.validate_coverage(doc)
        required_bindings = {
            # Older writer-publication bindings remain required by Activation Gate.
            "gate_publication_commit": git(root, "rev-parse", "HEAD"),
            "gate_publication_remote": PUBLISHED_REMOTE,
            "gate_publication_ref": GATE_REF,
            "publication_commit": PUBLISHED_COMMIT,
            "publication_remote": PUBLISHED_REMOTE,
            "publication_ref": PUBLISHED_REF,
            "technical_evidence_sha256": checked["evidence_sha256"],
        }
        for name, expected in required_bindings.items():
            if doc.get(name) != expected:
                errors.append("EXTERNAL_COVERAGE_BINDING_DRIFT:" + name)
        if not set(REQUIRED).issubset(set(doc.get("writer_entrypoints", []))):
            errors.append("EXTERNAL_COVERAGE_MISSING_WRITER")
    except (gate.ActivationBlocked, CoverageBlocked, OSError) as exc:
        errors.append("INDEPENDENT_COVERAGE_UNAVAILABLE:" + str(exc))
    return {
        "stage": "verify", "status": "BLOCKED" if errors else "INDEPENDENTLY_ATTESTED_NON_AUTHORIZING",
        "blockers": sorted(set(errors)), "evidence_sha256": checked["evidence_sha256"],
        "independent_operator_review_required": True,
        "activation_authorized": False,
        "external_provisioning_performed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("plan", "check", "verify"))
    parser.add_argument("--root", type=Path, default=Path("."), help="Coverage Gate checkout")
    parser.add_argument("--writer-release-root", type=Path, required=True,
                        help="Separate checkout of pinned published writer release")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    # An empty Make variable must fail closed, never silently resolve to cwd.
    if str(args.writer_release_root) in ("", ".") or not str(args.writer_release_root).strip():
        print(json.dumps({"status": "BLOCKED", "reason": "WRITER_RELEASE_ROOT_REQUIRED"}))
        return 2
    writer_root = args.writer_release_root.resolve()
    if writer_root == root:
        print(json.dumps({"status": "BLOCKED", "reason": "GATE_AND_WRITER_ROOT_MUST_DIFFER"}))
        return 2
    if Path(__file__).resolve() != (root / "scripts/coordination/execution_attempt_writer_coverage_v0_1.py").resolve():
        print(json.dumps({"status": "BLOCKED", "reason": "COVERAGE_CODE_NOT_FROM_GATE_ROOT"}))
        return 2
    try:
        if args.stage == "plan":
            result = build_plan(root, writer_release_root=writer_root)
            path, checksum = write_plan(root, args.report, result)
            print(json.dumps({"stage": "plan", "status": result["status"],
                              "evidence_path": str(path), "evidence_sha256": checksum,
                              "technical_blockers": result["technical_blockers"],
                              "deployment_coverage_verified": False}, indent=2, sort_keys=True))
        elif args.stage == "check":
            result = check_plan(root, args.report, writer_release_root=writer_root)
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            result = verify_coverage(root, args.report, writer_release_root=writer_root)
            print(json.dumps(result, indent=2, sort_keys=True))
        # plan is exploratory, not an operational authorization.
        return 0 if args.stage == "plan" or result["status"] in (
            "READY_FOR_INDEPENDENT_REVIEW", "INDEPENDENTLY_ATTESTED_NON_AUTHORIZING"
        ) else 2
    except CoverageBlocked as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
