from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "scripts/coordination/control_plane/dispatch_intent.py"
CONTRACT = (
    ROOT / "coordination/standards/automation/control_plane/"
    "central_listener_dispatcher_monitor_v0_1.yaml"
)

spec = importlib.util.spec_from_file_location(
    "_cf09_dispatch_intent_candidate",
    SOURCE,
)
assert spec and spec.loader
dispatch_intent = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dispatch_intent
spec.loader.exec_module(dispatch_intent)


def _cp(
    text: str,
    returncode: int = 0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        [],
        returncode,
        stdout=text,
    )


def _runner(seen):
    def runner(argv, **kwargs):
        seen.append(argv)
        if argv[0] == sys.executable:
            return _cp(
                "WORK_FRONT_VALIDATION=PASS\n"
                "WORK_FRONT_ID=wf-001\n"
                "WORK_FRONT_PATH=coordination/work_fronts/wf-001.yaml\n"
            )
        return _cp(
            "ASSISTANT_HANDOFF_V2_RUNTIME=PASS\n"
            "LAUNCH_MODE=TASK_EXECUTION\n"
            "HANDOFF_MANIFEST_SHA256=" + ("a" * 64) + "\n"
            "EXECUTION_AUTHORITY_GRANTED=false\n"
            "DISPATCH_AUTHORITY_GRANTED=false\n"
            "WORKER_DISPATCH_PERFORMED=false\n"
        )

    return runner


def _stub_work_front_runtime(tmp_path: Path) -> None:
    runtime = tmp_path / "scripts/coordination/work_front_v0_1.py"
    runtime.parent.mkdir(parents=True)
    runtime.write_text(
        "# test stub\n",
        encoding="utf-8",
    )


def test_prepare_task_execution_passes_complete_bindings(
    tmp_path: Path,
) -> None:
    _stub_work_front_runtime(tmp_path)
    seen = []

    result = dispatch_intent.prepare_cf09_task_execution(
        root=tmp_path,
        module="forprint_system_blueprint",
        work_front="wf-001",
        execution_profile="bounded-local@r1",
        task_prompt_id="prompt-cf09-s1",
        task_module_root=".",
        procedure_id="procedure-cf09-s1",
        runner=_runner(seen),
    )

    assert result["state"] == "AWAITING_ASSISTANT_ACK"
    assert result["assistant_ack_validated"] is False
    assert result["authority"]["worker_dispatch_performed"] is False
    assert result["authority"]["dispatch_authority_granted"] is False
    assert result["authority"]["external_dispatch_allowed"] is False
    assert result["next_required_human_boundary"] == "ASSISTANT_ACK_REQUIRED"

    make_argv = next(row for row in seen if row[0] == "make")
    assert "FRONT=wf-001" in make_argv
    assert "EXECUTION_PROFILE=bounded-local@r1" in make_argv
    assert "TASK_PROMPT_ID=prompt-cf09-s1" in make_argv
    assert "TASK_MODULE_ROOT=." in make_argv
    assert "MODULE=forprint_system_blueprint" in make_argv
    assert "PROCEDURE_ID=procedure-cf09-s1" in make_argv


def test_cf10_zero_stage_preflight_preserves_all_non_dispatch_authority_boundaries(
    tmp_path: Path,
) -> None:
    _stub_work_front_runtime(tmp_path)

    result = dispatch_intent.prepare_cf09_task_execution(
        root=tmp_path,
        module="forprint_system_blueprint",
        work_front="coordination/work_fronts/cf10_zero_stage_dispatch_boundary_regression_v0_1.yaml",
        execution_profile="light-maintenance",
        task_prompt_id="cf10-zero-stage-dispatch-boundary-regression-v0-1",
        task_module_root=".",
        procedure_id="governed_canonical_mutation",
        runner=_runner([]),
    )

    assert result["state"] == "AWAITING_ASSISTANT_ACK"
    assert result["authority"] == {
        "execution_authority_granted": False,
        "dispatch_authority_granted": False,
        "worker_dispatch_performed": False,
        "external_dispatch_allowed": False,
        "release_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
    }
    cf10_authority = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))[
        "cf10_internal_zero_stage_exception"
    ]["authority"]
    assert cf10_authority == {
        "execution_authority_granted": False,
        "dispatch_authority_granted": False,
        "worker_launch": False,
        "external_dispatch": False,
        "release": False,
        "push": False,
        "merge": False,
        "foreign_repository_write": False,
        "automatic_accept": False,
    }


def test_prepare_accepts_explicit_no_procedure_reason(
    tmp_path: Path,
) -> None:
    _stub_work_front_runtime(tmp_path)
    seen = []

    result = dispatch_intent.prepare_cf09_task_execution(
        root=tmp_path,
        work_front="wf-001",
        execution_profile="bounded-local@r1",
        task_prompt_id="prompt-cf09-s1",
        task_module_root=".",
        procedure_not_required_reason="bounded-first-slice",
        runner=_runner(seen),
    )

    assert result["procedure_id"] is None
    assert result["procedure_not_required_reason"] == "bounded-first-slice"
    make_argv = next(row for row in seen if row[0] == "make")
    assert "PROCEDURE_NOT_REQUIRED_REASON=bounded-first-slice" in make_argv


def test_prepare_rejects_missing_or_ambiguous_procedure_binding(
    tmp_path: Path,
) -> None:
    _stub_work_front_runtime(tmp_path)

    base = {
        "root": tmp_path,
        "work_front": "wf-001",
        "execution_profile": "bounded-local@r1",
        "task_prompt_id": "prompt-cf09-s1",
        "task_module_root": ".",
        "runner": _runner([]),
    }

    for extra in (
        {},
        {
            "procedure_id": "procedure-cf09-s1",
            "procedure_not_required_reason": "not-needed",
        },
    ):
        try:
            dispatch_intent.prepare_cf09_task_execution(
                **base,
                **extra,
            )
        except ValueError as exc:
            assert "exactly one" in str(exc)
        else:
            raise AssertionError("invalid procedure binding was accepted")


def test_prepare_rejects_handoff_that_claims_dispatch(
    tmp_path: Path,
) -> None:
    _stub_work_front_runtime(tmp_path)

    def runner(argv, **kwargs):
        if argv[0] == sys.executable:
            return _cp("WORK_FRONT_VALIDATION=PASS\nWORK_FRONT_ID=wf-001\n")
        return _cp(
            "ASSISTANT_HANDOFF_V2_RUNTIME=PASS\n"
            "LAUNCH_MODE=TASK_EXECUTION\n"
            "HANDOFF_MANIFEST_SHA256=" + ("b" * 64) + "\n"
            "EXECUTION_AUTHORITY_GRANTED=false\n"
            "DISPATCH_AUTHORITY_GRANTED=true\n"
            "WORKER_DISPATCH_PERFORMED=false\n"
        )

    try:
        dispatch_intent.prepare_cf09_task_execution(
            root=tmp_path,
            work_front="wf-001",
            execution_profile="bounded-local@r1",
            task_prompt_id="prompt-cf09-s1",
            task_module_root=".",
            procedure_not_required_reason="test",
            runner=runner,
        )
    except RuntimeError as exc:
        assert "DISPATCH_AUTHORITY_GRANTED" in str(exc)
    else:
        raise AssertionError("dispatch-authority widening was not rejected")


def test_dry_attempt_envelope_is_tmp_only(
    tmp_path: Path,
) -> None:
    envelope = {
        "schema_version": "forprint_cf09_dispatcher_pre_execution_envelope_v0_1",
        "state": "READY_FOR_EXPLICIT_DISPATCH",
    }
    output = dispatch_intent.write_cf09_dry_attempt_envelope(
        root=tmp_path,
        attempt_id="attempt-cf09-s1-001",
        envelope=envelope,
    )

    assert output.parent == (tmp_path / "tmp/dispatcher_attempts").resolve()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["canonical_execution_attempt_ledger_written"] is False
    assert data["worker_dispatch_performed"] is False
    assert data["fact_authority"] == "none"


def test_contract_declares_complete_explicit_binding_boundary() -> None:
    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    row = data["cf09_task_execution_preflight"]

    assert row["ready_is_dispatch"] is False
    assert row["worker_dispatch_allowed"] is False
    assert row["external_dispatch_allowed"] is False
    assert row["canonical_attempt_ledger_write_in_first_slice"] is False

    binding = row["binding_policy"]
    assert binding["execution_profile"]["required"] is True
    assert binding["task_prompt_id"]["required"] is True
    assert binding["task_module_root"]["required"] is True
    assert binding["procedure"]["exactly_one_required"] == [
        "procedure_id",
        "procedure_not_required_reason",
    ]
