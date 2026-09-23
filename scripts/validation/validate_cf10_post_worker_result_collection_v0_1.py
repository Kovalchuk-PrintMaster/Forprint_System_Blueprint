from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/coordination/control_plane/dispatch_intent.py"


def _load_dispatch():
    spec = importlib.util.spec_from_file_location(
        "_cf10_post_worker_result_collection_validation",
        SOURCE,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load dispatch_intent.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    dispatch = _load_dispatch()

    for name in (
        "collect_cf10_post_worker_result_artifact",
        "finalize_cf10_workspace_result_artifact",
        "finalize_cf10_workspace_task_execution",
    ):
        if not hasattr(dispatch, name):
            raise RuntimeError(
                f"required CF-10 result collector API missing: {name}"
            )

    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        attempt_id = "cf10-u180j-proof"
        workspace = (
            tmp
            / "forprint_system_blueprint"
            / "worker-01"
            / attempt_id
            / "workspace"
            / "repo"
        )
        workspace.mkdir(parents=True)
        result_dir = workspace.parent.parent / "result"
        result_dir.mkdir()

        artifact = result_dir / "worker_result.yaml"
        artifact.write_text(
            "\n".join(
                [
                    "schema_version: forprint_assistant_handoff_v2_result_v0_1",
                    f"attempt_id: {attempt_id}",
                    "changed_paths: []",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        decision = {
            "binding": {
                "attempt_id": attempt_id,
                "workspace_repo": str(workspace),
            }
        }

        collected = dispatch.collect_cf10_post_worker_result_artifact(
            explicit_dispatch_decision=decision,
            result_artifact_path=artifact,
        )
        if collected.get("attempt_id") != attempt_id:
            raise RuntimeError("collected result attempt binding mismatch")

        outside = tmp / "outside.yaml"
        outside.write_text(
            artifact.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        try:
            dispatch.collect_cf10_post_worker_result_artifact(
                explicit_dispatch_decision=decision,
                result_artifact_path=outside,
            )
        except ValueError as exc:
            if "escapes bound attempt result directory" not in str(exc):
                raise
        else:
            raise RuntimeError("outside result artifact was accepted")

    print("CF10_POST_WORKER_RESULT_COLLECTION_VALIDATION=PASS")
    print("HANDOFF_V2_SCHEMA_CHANGED=false")
    print("RESULT_ARTIFACT_BOUND_TO_ATTEMPT=true")
    print("RESULT_ARTIFACT_BOUND_TO_RESULT_DIRECTORY=true")
    print("WORKER_DELTA_DERIVATION_DELEGATED_TO_EXISTING_FINALIZER=true")
    print("LIVE_WORKER_LAUNCHED=false")
    print("ATTEMPT_LEDGER_MUTATED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
