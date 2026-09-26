from __future__ import annotations

from pathlib import Path

import pytest

from scripts.coordination.continuity import build_source_state
from scripts.coordination.control_plane.context import task_context_adapter as adapter

ROOT = Path(__file__).resolve().parents[4]
TASK_ID = "cf10-zero-stage-dispatch-boundary-regression-v0-1"


def test_internal_task_resolves_exactly_once() -> None:
    path, task, row = adapter.resolve_internal_task(ROOT, TASK_ID)
    assert path.name == "cf10_zero_stage_dispatch_boundary_regression_v0_1.yaml"
    assert task["task_id"] == TASK_ID
    assert row["task_id"] == TASK_ID
    assert row["source_type"] == "MANUAL_INTERNAL"


def test_internal_context_reuses_normalized_task_envelope() -> None:
    context = adapter.build_internal_task_context(
        ROOT,
        task_id=TASK_ID,
        module_root=".",
    )
    envelope = context["task_envelope"]
    assert envelope["source"]["type"] == "MANUAL_INTERNAL"
    assert envelope["authority"] == {
        "execution_authority_source": "WORK_FRONT",
        "task_envelope_grants_authority": False,
        "widening_requested": False,
    }
    assert envelope["work"]["work_front_id"] == (
        "wf-cf10-zero-stage-dispatch-boundary-regression-v0-1"
    )


def test_internal_context_reuses_canonical_continuity_fingerprint() -> None:
    context = adapter.build_internal_task_context(
        ROOT,
        task_id=TASK_ID,
        module_root=".",
    )
    current = build_source_state(ROOT)
    assert context["source_state"]["fingerprint_sha256"] == (
        current["fingerprint_sha256"]
    )
    assert context["source_state"]["provider"] == (
        "scripts.coordination.continuity.build_source_state"
    )


def test_manual_internal_rejects_foreign_module_root(tmp_path: Path) -> None:
    with pytest.raises(adapter.TaskContextAdapterError, match="Blueprint repository root"):
        adapter.build_internal_task_context(
            ROOT,
            task_id=TASK_ID,
            module_root=str(tmp_path),
        )


def test_external_argv_preserves_existing_builder() -> None:
    argv = adapter.build_external_argv(
        ROOT,
        prompt_id="fixture",
        module_root="/tmp/logistics",
        module="logistics_service",
        no_write=True,
        output_dir=None,
        print_bundle=False,
    )
    assert any(
        str(item).endswith("scripts/coordination/build_context_bundle.py")
        for item in argv
    )
    assert argv.count("--task-context") == 1
    assert argv.count("--prompt-id") == 1
    assert "--no-write" in argv
    assert argv[-2:] == ["--module", "logistics_service"] or "--no-write" in argv
