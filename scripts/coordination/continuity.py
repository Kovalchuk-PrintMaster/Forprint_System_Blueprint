#!/usr/bin/env python3
"""ForPrint continuity event/checkpoint primitives v0.1.

The accepted event ledger is append-only and content-addressed. This module owns:
- deterministic source-state fingerprints;
- atomic checkpoint append;
- chain metadata for immutable continuity events.

It deliberately does not implement generated operational projections, handoff pack
compilation, lifecycle closure, release authority, queue authority, or worker dispatch.
When lifecycle enforcement is enabled, it does enforce canonical checkpoint admission
so CHECKPOINT_RECORDED cannot bypass the ACTIVE state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml


class _IndentedSafeDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


EVENT_SCHEMA = "forprint_continuity_checkpoint_event_v0_1"
SPEC_SCHEMA = "forprint_continuity_checkpoint_spec_v0_1"
STATE_SCHEMA = "forprint_continuity_source_state_v0_1"
EVENT_NAME_RE = re.compile(
    r"^(?P<sequence>[0-9]{6})__(?P<event_id>[a-z0-9][a-z0-9._-]{2,127})__"
    r"(?P<sha>[0-9a-f]{12})\.yaml$"
)
EVENT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,127}$")

RUNTIME_TOP_LEVEL_EXCLUSIONS = {
    ".git",
    ".venv_blueprint",
    "tmp",
}
RUNTIME_EXACT_EXCLUSIONS = {
    "tmp.py",
}
RUNTIME_RECURSIVE_PARTS = {
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".tox",
    ".nox",
    "node_modules",
}
NON_SOURCE_PREFIXES = (
    ("indexes",),
    ("coordination", "continuity", "events"),
    ("coordination", "continuity", "projections"),
    ("coordination", "roadmap_execution", "projections"),
)


class ContinuityError(RuntimeError):
    pass


def _run(
    root: Path,
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(
        list(args),
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if check and cp.returncode:
        raise ContinuityError(f"command failed rc={cp.returncode}: {' '.join(args)}\n{cp.stdout}")
    return cp


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def yaml_bytes(value: dict[str, Any]) -> bytes:
    text = yaml.dump(
        value,
        Dumper=_IndentedSafeDumper,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=120,
    )
    return text.encode("utf-8")


def excluded_from_source_fingerprint(rel: Path) -> bool:
    if not rel.parts:
        return False
    if rel.as_posix() in RUNTIME_EXACT_EXCLUSIONS:
        return True
    if rel.parts[0] in RUNTIME_TOP_LEVEL_EXCLUSIONS:
        return True
    if any(part in RUNTIME_RECURSIVE_PARTS for part in rel.parts):
        return True
    return any(tuple(rel.parts[: len(prefix)]) == prefix for prefix in NON_SOURCE_PREFIXES)


def _path_state(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        return {
            "kind": "symlink",
            "target": os.readlink(path),
        }
    if path.is_file():
        return {
            "kind": "file",
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
    if path.exists():
        return {"kind": "other"}
    return {"kind": "missing"}


def _status_records(root: Path) -> list[dict[str, Any]]:
    cp = subprocess.run(
        [
            "git",
            "-c",
            "core.quotePath=false",
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        ],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if cp.returncode:
        raise ContinuityError("git status failed: " + cp.stderr.decode("utf-8", errors="replace"))

    raw = cp.stdout.decode("utf-8", errors="surrogateescape")
    parts = raw.split("\0")
    if parts and parts[-1] == "":
        parts.pop()

    rows: list[dict[str, Any]] = []
    index = 0
    while index < len(parts):
        token = parts[index]
        index += 1
        if len(token) < 4:
            raise ContinuityError(f"invalid porcelain record: {token!r}")

        status = token[:2]
        path_text = token[3:]
        row: dict[str, Any] = {
            "status": status,
            "path": path_text,
        }

        if "R" in status or "C" in status:
            if index >= len(parts):
                raise ContinuityError(f"rename/copy record missing original path: {token!r}")
            row["original_path"] = parts[index]
            index += 1

        rows.append(row)

    rows.sort(
        key=lambda row: (
            row["path"],
            row.get("original_path", ""),
            row["status"],
        )
    )
    return rows


def _isolated_source_state_baseline(
    root: Path,
    *,
    head: str,
    branch: str,
) -> dict[str, Any] | None:
    if os.environ.get("FORPRINT_NON_MUTATING_CHECK_ISOLATED") != "1":
        return None

    baseline_path_raw = os.environ.get("FORPRINT_CONTINUITY_SOURCE_STATE_BASELINE")
    baseline_root_raw = os.environ.get("FORPRINT_CONTINUITY_SOURCE_STATE_BASELINE_ROOT")
    if baseline_path_raw is None and baseline_root_raw is None:
        return None
    if not baseline_path_raw or not baseline_root_raw:
        raise ContinuityError("isolated continuity baseline requires both path and root")

    baseline_root = Path(baseline_root_raw).resolve()
    if root.resolve() != baseline_root:
        return None

    baseline_path = Path(baseline_path_raw).resolve()
    if not baseline_path.is_file():
        raise ContinuityError(f"isolated continuity baseline missing: {baseline_path}")

    try:
        value = json.loads(baseline_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContinuityError(f"isolated continuity baseline unreadable: {exc}") from exc

    if not isinstance(value, dict):
        raise ContinuityError("isolated continuity baseline must be a mapping")
    if value.get("schema_version") != STATE_SCHEMA:
        raise ContinuityError("isolated continuity baseline schema mismatch")
    if value.get("git_head") != head or value.get("git_branch") != branch:
        raise ContinuityError("isolated continuity baseline Git identity mismatch")

    required = {
        "durable_dirty_paths",
        "dirty_path_status",
        "dirty_path_content_or_symlink_fingerprint",
        "rename_or_copy_origins",
        "exclusion_policy",
    }
    missing = sorted(required - set(value))
    if missing:
        raise ContinuityError("isolated continuity baseline missing fields: " + ",".join(missing))
    return value


def build_source_state(
    root: Path,
    *,
    bounded_final_applied_artifact_hashes: dict[str, str] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    if not (root / ".git").exists():
        raise ContinuityError(f"not a Git worktree root: {root}")

    head = _run(root, "git", "rev-parse", "HEAD").stdout.strip()
    branch = _run(root, "git", "branch", "--show-current").stdout.strip()

    isolated_baseline = _isolated_source_state_baseline(
        root,
        head=head,
        branch=branch,
    )
    if isolated_baseline is not None:
        bounded = dict(sorted((bounded_final_applied_artifact_hashes or {}).items()))
        payload: dict[str, Any] = {
            "schema_version": STATE_SCHEMA,
            "source_mode": "working_tree",
            "git_head": head,
            "git_branch": branch,
            "durable_dirty_paths": list(isolated_baseline["durable_dirty_paths"]),
            "dirty_path_status": dict(isolated_baseline["dirty_path_status"]),
            "dirty_path_content_or_symlink_fingerprint": dict(
                isolated_baseline["dirty_path_content_or_symlink_fingerprint"]
            ),
            "rename_or_copy_origins": dict(isolated_baseline["rename_or_copy_origins"]),
            "bounded_final_applied_artifact_hashes": bounded,
            "exclusion_policy": dict(isolated_baseline["exclusion_policy"]),
        }
        payload["fingerprint_sha256"] = sha256_bytes(_canonical_json_bytes(payload))
        return payload

    status_rows = [
        row
        for row in _status_records(root)
        if not excluded_from_source_fingerprint(Path(row["path"]))
    ]

    dirty_paths = sorted({row["path"] for row in status_rows})
    dirty_status: dict[str, str] = {}
    dirty_state: dict[str, dict[str, Any]] = {}
    rename_origins: dict[str, str] = {}

    for row in status_rows:
        rel = row["path"]
        dirty_status[rel] = row["status"]
        dirty_state[rel] = _path_state(root / rel)
        if "original_path" in row:
            rename_origins[rel] = row["original_path"]

    bounded = dict(sorted((bounded_final_applied_artifact_hashes or {}).items()))

    payload: dict[str, Any] = {
        "schema_version": STATE_SCHEMA,
        "source_mode": "working_tree",
        "git_head": head,
        "git_branch": branch,
        "durable_dirty_paths": dirty_paths,
        "dirty_path_status": dirty_status,
        "dirty_path_content_or_symlink_fingerprint": dirty_state,
        "rename_or_copy_origins": dict(sorted(rename_origins.items())),
        "bounded_final_applied_artifact_hashes": bounded,
        "exclusion_policy": {
            "runtime_top_level": sorted(RUNTIME_TOP_LEVEL_EXCLUSIONS),
            "runtime_exact": sorted(RUNTIME_EXACT_EXCLUSIONS),
            "runtime_recursive_parts": sorted(RUNTIME_RECURSIVE_PARTS),
            "non_source_prefixes": ["/".join(prefix) for prefix in NON_SOURCE_PREFIXES],
            "reports_implicitly_excluded": False,
        },
    }
    payload["fingerprint_sha256"] = sha256_bytes(_canonical_json_bytes(payload))
    return payload


def event_files(event_root: Path) -> list[Path]:
    if not event_root.exists():
        return []
    files = sorted(
        path for path in event_root.iterdir() if path.is_file() and path.suffix == ".yaml"
    )
    return files


def read_event(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ContinuityError(f"event must be a mapping: {path}")
    return value


def _load_spec(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ContinuityError("checkpoint spec must be a mapping")
    if value.get("schema_version") != SPEC_SCHEMA:
        raise ContinuityError(f"checkpoint spec schema must be {SPEC_SCHEMA}")
    return value


def _validate_spec(spec: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "event_id",
        "work_id",
        "occurred_at",
        "actor",
        "summary",
        "what_changed",
        "why",
        "evidence",
        "decision_rationale",
        "rejected_alternative_when_material",
        "blockers",
        "unknowns",
        "next_actions",
        "source_state_before",
        "source_state_after",
        "final_applied_artifact_hashes",
        "external_baseline_preserved",
    }
    missing = sorted(required - set(spec))
    if missing:
        raise ContinuityError("checkpoint spec missing fields: " + ", ".join(missing))

    event_id = str(spec["event_id"])
    if not EVENT_ID_RE.fullmatch(event_id):
        raise ContinuityError(f"invalid event_id: {event_id!r}")

    if not str(spec["work_id"]).strip():
        raise ContinuityError("work_id must be non-empty")
    if not str(spec["summary"]).strip():
        raise ContinuityError("summary must be non-empty")
    if not str(spec["why"]).strip():
        raise ContinuityError("why must be non-empty")
    if not str(spec["decision_rationale"]).strip():
        raise ContinuityError("decision_rationale must be non-empty")

    for key in ("what_changed", "evidence", "blockers", "unknowns"):
        if not isinstance(spec[key], list):
            raise ContinuityError(f"{key} must be a list")

    next_actions = spec["next_actions"]
    if not isinstance(next_actions, list):
        raise ContinuityError("next_actions must be a list")
    if not 5 <= len(next_actions) <= 10:
        raise ContinuityError("next_actions must contain between 5 and 10 actions")

    before = spec["source_state_before"]
    after = spec["source_state_after"]
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise ContinuityError("source_state_before/after must be mappings")
    for label, state in (("before", before), ("after", after)):
        if not state.get("fingerprint_sha256"):
            raise ContinuityError(f"source_state_{label} missing fingerprint_sha256")

    hashes = spec["final_applied_artifact_hashes"]
    if not isinstance(hashes, dict) or not hashes:
        raise ContinuityError("final_applied_artifact_hashes must be a non-empty mapping")
    for rel, digest in hashes.items():
        if (
            not isinstance(rel, str)
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
        ):
            raise ContinuityError("invalid final applied artifact hash entry")

    if spec["external_baseline_preserved"] is not True:
        raise ContinuityError("checkpoint requires external_baseline_preserved=true")


def _enforce_checkpoint_lifecycle_transition(
    *,
    root: Path,
    event_root: Path,
    work_id: str,
) -> None:
    canonical_event_root = (root / "coordination/continuity/events").resolve()
    if event_root.resolve() != canonical_event_root:
        return

    contract_path = root / "coordination/standards/automation/continuity_contract_v0_1.yaml"
    if not contract_path.is_file():
        return
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    if not isinstance(contract, dict):
        raise ContinuityError("continuity contract must be a mapping")
    lifecycle = contract.get("lifecycle")
    enforcement = lifecycle.get("enforcement") if isinstance(lifecycle, dict) else None
    if not isinstance(enforcement, dict) or enforcement.get("enabled") is not True:
        return

    state_by_event_type = {
        "WORK_PLANNED": "PLANNED",
        "WORK_ACTIVATED": "ACTIVE",
        "CHECKPOINT_RECORDED": "CHECKPOINTED",
        "VALIDATION_PASSED": "VALIDATED",
        "VALIDATION_FAILED": "ACTIVE",
        "WORK_CLOSED": "CLOSED",
        "WORK_SUPERSEDED": "CLOSED",
    }
    state: str | None = None
    for path in event_files(event_root):
        event = read_event(path)
        if event.get("work_id") != work_id:
            continue
        mapped = state_by_event_type.get(event.get("event_type"))
        if mapped is not None:
            state = mapped
    if state != "ACTIVE":
        raise ContinuityError(f"CHECKPOINT_RECORDED requires ACTIVE; current={state}")


def append_checkpoint(
    *,
    root: Path,
    spec_path: Path,
    event_root: Path | None = None,
) -> Path:
    root = root.resolve()
    spec = _load_spec(spec_path)
    _validate_spec(spec)

    events = (
        event_root.resolve() if event_root is not None else root / "coordination/continuity/events"
    )
    events.mkdir(parents=True, exist_ok=True)

    _enforce_checkpoint_lifecycle_transition(
        root=root,
        event_root=events,
        work_id=str(spec["work_id"]),
    )

    existing_files = event_files(events)
    existing_ids = {str(read_event(path).get("event_id")) for path in existing_files}
    if spec["event_id"] in existing_ids:
        raise ContinuityError(f"duplicate event_id: {spec['event_id']}")

    sequence = len(existing_files) + 1
    previous_event_id = None
    previous_event_sha256 = None
    if existing_files:
        previous = existing_files[-1]
        previous_event = read_event(previous)
        previous_event_id = previous_event.get("event_id")
        previous_event_sha256 = sha256_file(previous)

    event: dict[str, Any] = {
        "schema_version": EVENT_SCHEMA,
        "event_id": spec["event_id"],
        "event_type": "CHECKPOINT_RECORDED",
        "sequence": sequence,
        "previous_event_id": previous_event_id,
        "previous_event_sha256": previous_event_sha256,
        "work_id": spec["work_id"],
        "occurred_at": spec["occurred_at"],
        "actor": spec["actor"],
        "summary": spec["summary"],
        "source_state_ref": spec["source_state_after"]["fingerprint_sha256"],
        "bootstrap_historical_import": bool(spec.get("bootstrap_historical_import", False)),
        "checkpoint": {
            "what_changed": spec["what_changed"],
            "why": spec["why"],
            "evidence": spec["evidence"],
            "decision_rationale": spec["decision_rationale"],
            "rejected_alternative_when_material": spec["rejected_alternative_when_material"],
            "blockers": spec["blockers"],
            "unknowns": spec["unknowns"],
            "next_actions": spec["next_actions"],
            "source_state_before": spec["source_state_before"],
            "source_state_after": spec["source_state_after"],
            "final_applied_artifact_hashes": dict(
                sorted(spec["final_applied_artifact_hashes"].items())
            ),
            "external_baseline_preserved": True,
            "historical_import_scope": spec.get(
                "historical_import_scope",
                [],
            ),
            "deferred_backlog": spec.get("deferred_backlog", []),
        },
    }

    payload = yaml_bytes(event)
    digest = sha256_bytes(payload)
    filename = f"{sequence:06d}__{spec['event_id']}__{digest[:12]}.yaml"
    target = events / filename

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(target, flags, 0o644)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            target.unlink()
        except FileNotFoundError:
            pass
        raise

    return target


def _load_hashes(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ContinuityError("bounded hashes JSON must be an object")
    return {str(key): str(item) for key, item in value.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    fingerprint_parser = subparsers.add_parser("fingerprint")
    fingerprint_parser.add_argument("--root", default=".")
    fingerprint_parser.add_argument(
        "--bounded-hashes-json",
        type=Path,
        default=None,
    )
    fingerprint_parser.add_argument("--output", type=Path, default=None)

    checkpoint_parser = subparsers.add_parser("checkpoint")
    checkpoint_parser.add_argument("--root", default=".")
    checkpoint_parser.add_argument("--spec", type=Path, required=True)
    checkpoint_parser.add_argument(
        "--event-root",
        type=Path,
        default=None,
    )

    args = parser.parse_args()

    try:
        if args.command == "fingerprint":
            root = Path(args.root).resolve()
            state = build_source_state(
                root,
                bounded_final_applied_artifact_hashes=_load_hashes(args.bounded_hashes_json),
            )
            output = (
                json.dumps(
                    state,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=False,
                )
                + "\n"
            )
            if args.output is not None:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(output, encoding="utf-8")
            print(output, end="")
            return 0

        if args.command == "checkpoint":
            target = append_checkpoint(
                root=Path(args.root),
                spec_path=args.spec,
                event_root=args.event_root,
            )
            print("CONTINUITY_CHECKPOINT_APPEND=PASS")
            print(f"EVENT_PATH={target}")
            print(f"EVENT_SHA256={sha256_file(target)}")
            return 0

        raise ContinuityError(f"unsupported command: {args.command}")
    except (OSError, ValueError, yaml.YAMLError, ContinuityError) as exc:
        print(f"CONTINUITY_COMMAND=FAIL {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
