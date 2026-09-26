# Validate CF-10 Worker Runtime Foundation Slice 1.

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.coordination.control_plane.tasking import compile_task_envelope
from scripts.coordination.control_plane.tasking.sources import (
    external_prompt_queue_source,
    manual_internal_source,
)
from scripts.coordination.control_plane.workspace import (
    build_workspace_layout,
    workspace_manifest,
)

ROOT = Path(__file__).resolve().parents[2]


def load(relative: str) -> dict:
    data = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{relative}: root must be mapping")
    return data


def main() -> int:
    try:
        task = load("coordination/standards/automation/worker_task_envelope_contract_v0_1.yaml")
        workspace = load("coordination/standards/automation/worker_workspace_contract_v0_1.yaml")
        promotion = load(
            "coordination/standards/automation/worker_candidate_promotion_contract_v0_1.yaml"
        )
        index = load("coordination/standards/automation/index.yaml")

        auth = task["authority_semantics"]
        assert auth["task_envelope_grants_authority"] is False
        assert auth["execution_authority_source"] == "WORK_FRONT"
        assert auth["authority_widening_allowed"] is False
        assert set(task["reuse"].values()) == {"REUSE"}
        assert set(task["source_types"]) == {"MANUAL_INTERNAL", "EXTERNAL_PROMPT_QUEUE"}

        common = dict(
            work_id="u180j",
            work_front_id="wf-cf10-fixture",
            objective="Validate normalization.",
            instructions=["Perform one bounded fixture action."],
            acceptance=["Fixture evidence passes."],
            stop_conditions=["Stop on authority widening."],
            execution_profile_id="light-maintenance",
            execution_profile_revision="r1",
            procedure_id="governed_canonical_mutation",
            procedure_revision="0.1.0",
        )
        manual = compile_task_envelope(
            task_id="fixture-manual",
            module_id="forprint_system_blueprint",
            source=manual_internal_source(
                artifact_ref="coordination/internal_work/blueprint/worker_tasks/cf10_fixture.yaml"
            ),
            **common,
        )
        external = compile_task_envelope(
            task_id="fixture-external",
            module_id="logistics_service",
            source=external_prompt_queue_source(
                queue_ref="coordination/outgoing_prompts/logistics_service/index.yaml",
                prompt_id="fixture_prompt",
                approved_prompt_ref=(
                    "coordination/outgoing_prompts/logistics_service/approved/fixture.md"
                ),
            ),
            **common,
        )
        assert manual["authority"] == external["authority"]
        assert manual["work"] == external["work"]

        workspace_auth = workspace["authority_semantics"]
        assert workspace_auth["workspace_grants_authority"] is False
        assert workspace_auth["worker_direct_canonical_write_allowed"] is False

        layout = build_workspace_layout(
            runtime_root="/srv/software_development/forprint-worker-runtime",
            canonical_repo=ROOT,
            module_id="forprint_system_blueprint",
            worker_id="worker-01",
            attempt_id="attempt-fixture",
        )
        manifest = workspace_manifest(
            layout=layout,
            canonical_repo=ROOT,
            source_head="fixture-head",
            module_id="forprint_system_blueprint",
            worker_id="worker-01",
            attempt_id="attempt-fixture",
        )
        assert manifest["canonical_write_allowed"] is False
        assert manifest["provisioning_performed"] is False

        promo = promotion["authority_semantics"]
        assert promo["worker_can_promote"] is False
        assert promo["worker_can_commit_canonical"] is False
        assert promo["worker_can_push"] is False
        assert promo["worker_can_merge"] is False
        assert promo["worker_can_release"] is False
        assert promo["worker_can_auto_accept"] is False
        assert promo["promotion_authority"] == "OPERATOR_CONTROLLED_CF10"

        docs = index["standards_group"]["documents"]
        names = {
            item if isinstance(item, str) else item.get("file")
            for item in docs
            if isinstance(item, (str, dict))
        }
        required = {
            "worker_task_envelope_contract_v0_1.yaml",
            "worker_workspace_contract_v0_1.yaml",
            "worker_candidate_promotion_contract_v0_1.yaml",
        }
        assert required.issubset(names)

        print("WORKER_RUNTIME_FOUNDATION_VALIDATION=PASS")
        print("TASK_SOURCE_TYPES=EXTERNAL_PROMPT_QUEUE,MANUAL_INTERNAL")
        print("EXECUTION_AUTHORITY_SOURCE=WORK_FRONT")
        print("DUPLICATED_EXECUTION_FRAMEWORK=false")
        print("WORKSPACE_PROVISIONING_PERFORMED=false")
        print("WORKER_DISPATCH_PERFORMED=false")
        print("PROMOTION_AUTHORITY=OPERATOR_CONTROLLED_CF10")
        return 0
    except Exception as exc:
        print(f"ERROR={type(exc).__name__}: {exc}")
        print("WORKER_RUNTIME_FOUNDATION_VALIDATION=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
