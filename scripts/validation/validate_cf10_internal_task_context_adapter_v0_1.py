#!/usr/bin/env python3
"""Validate CF-10 internal task context adapter integration."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.coordination.control_plane.context import task_context_adapter as adapter  # noqa: E402

TASK_ID = "cf10-zero-stage-dispatch-boundary-regression-v0-1"
RUNTIME = ROOT / "scripts/coordination/assistant_handoff_v2_runtime_v0_1.py"
RUNTIME_CONTRACT = ROOT / (
    "coordination/standards/automation/"
    "assistant_handoff_v2_runtime_contract_v0_1.yaml"
)
LEGACY_SELF_PROMPT_ROOT = ROOT / (
    "coordination/outgoing_prompts/forprint_system_blueprint"
)


def main() -> int:
    try:
        context = adapter.build_internal_task_context(
            ROOT,
            task_id=TASK_ID,
            module_root=".",
        )
        if context.get("schema_version") != "forprint_blueprint_internal_task_context_v0_1":
            raise RuntimeError("internal task-context schema mismatch")
        if context.get("source_type") != "MANUAL_INTERNAL":
            raise RuntimeError("internal task source type mismatch")
        if len(str(context.get("task_context_id") or "")) != 64:
            raise RuntimeError("task_context_id must be sha256")

        envelope = context.get("task_envelope")
        if not isinstance(envelope, dict):
            raise RuntimeError("task envelope missing")
        if envelope.get("work", {}).get("work_front_id") != (
            "wf-cf10-zero-stage-dispatch-boundary-regression-v0-1"
        ):
            raise RuntimeError("first-worker Work Front binding mismatch")
        if envelope.get("execution_profile") != {
            "profile_id": "light-maintenance",
            "revision": "r1",
        }:
            raise RuntimeError("Execution Profile binding mismatch")
        if envelope.get("procedure") != {
            "procedure_id": "governed_canonical_mutation",
            "revision": "0.1.0",
        }:
            raise RuntimeError("Governed Procedure binding mismatch")

        authority = context.get("authority")
        if not isinstance(authority, dict):
            raise RuntimeError("context authority mapping missing")
        if authority.get("context_grants_authority") is not False:
            raise RuntimeError("context must not grant authority")
        if authority.get("execution_authority_source") != "WORK_FRONT":
            raise RuntimeError("Work Front must remain execution authority")

        source_state = context.get("source_state")
        if not isinstance(source_state, dict):
            raise RuntimeError("source_state missing")
        if source_state.get("provider") != (
            "scripts.coordination.continuity.build_source_state"
        ):
            raise RuntimeError("canonical continuity source-state not reused")
        if len(str(source_state.get("fingerprint_sha256") or "")) != 64:
            raise RuntimeError("source-state fingerprint missing")

        runtime_text = RUNTIME.read_text(encoding="utf-8")
        adapter_path = (
            'TASK_CONTEXT_RUNTIME = Path('
            '"scripts/coordination/control_plane/context/task_context_adapter.py"'
            ')'
        )
        if adapter_path not in runtime_text:
            raise RuntimeError("Handoff v2 does not delegate to context adapter")
        if "build_context_bundle.py --task-context" not in runtime_text:
            raise RuntimeError(
                "Handoff v2 lost external Task Context compatibility marker"
            )
        if (
            '"delegate": '
            '"scripts/coordination/control_plane/context/'
            'task_context_adapter.py --task-context"'
        ) not in runtime_text:
            raise RuntimeError("Handoff v2 evidence delegate label is stale")

        contract = yaml.safe_load(RUNTIME_CONTRACT.read_text(encoding="utf-8"))
        delegate = contract.get("architecture", {}).get("task_execution_delegate")
        if delegate != (
            "scripts/coordination/control_plane/context/"
            "task_context_adapter.py --task-context"
        ):
            raise RuntimeError("Handoff runtime contract delegate mismatch")

        argv = adapter.build_external_argv(
            ROOT,
            prompt_id="external-fixture",
            module_root="/tmp/module-fixture",
            module="logistics_service",
            no_write=True,
            output_dir=None,
            print_bundle=False,
        )
        if not any(
            str(item).endswith("scripts/coordination/build_context_bundle.py")
            for item in argv
        ):
            raise RuntimeError("external flow no longer delegates old Task Context builder")
        if "--task-context" not in argv or "--no-write" not in argv:
            raise RuntimeError("external Task Context delegation flags changed")

        print("CF10_INTERNAL_TASK_CONTEXT_ADAPTER_VALIDATION=PASS")
        print("INTERNAL_TASK_SOURCE=MANUAL_INTERNAL")
        print("EXTERNAL_TASK_SOURCE=EXTERNAL_PROMPT_QUEUE")
        print("EXTERNAL_BUILDER_REUSED=true")
        print("CANONICAL_CONTINUITY_SOURCE_STATE_REUSED=true")
        print("EXECUTION_AUTHORITY_SOURCE=WORK_FRONT")
        print("HANDOFF_V2_DELEGATE=CONTROL_PLANE_CONTEXT_ADAPTER")
        print("EXTERNAL_TASK_CONTEXT_COMPATIBILITY_MARKER=true")
        print(
            "LEGACY_SELF_PROMPT_SURFACE_PRESENT="
            + str(LEGACY_SELF_PROMPT_ROOT.exists()).lower()
        )
        print("LEGACY_SELF_PROMPT_SURFACE_USED_AS_CF10_SOURCE=false")
        print("WORKER_DISPATCH_PERFORMED=false")
        return 0
    except Exception as exc:
        print(f"ERROR={type(exc).__name__}: {exc}")
        print("CF10_INTERNAL_TASK_CONTEXT_ADAPTER_VALIDATION=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
