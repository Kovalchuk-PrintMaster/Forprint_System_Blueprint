from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[4]
SOURCE = (
    ROOT
    / "scripts/coordination/control_plane/worker_runtime/"
    "worker_result_return.py"
)
INVOCATION_ADAPTER = (
    ROOT
    / "scripts/coordination/control_plane/worker_runtime/"
    "invocation_adapter.py"
)
MAKEFILE = ROOT / "Makefile"

FRAME_BEGIN = "FORPRINT_HANDOFF_V2_RESULT_BEGIN"
FRAME_END = "FORPRINT_HANDOFF_V2_RESULT_END"


def _load_result_return():
    assert SOURCE.is_file(), (
        "worker_result_return.py is missing; RED proves the frozen "
        "result-return capability does not exist yet"
    )
    spec = importlib.util.spec_from_file_location(
        "_cf10_worker_result_return_test",
        SOURCE,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _valid_result(
    *,
    attempt_id: str = "cf10-u180j-a034",
    manifest_hash: str = "a" * 64,
) -> dict:
    return {
        "schema_version": "forprint_assistant_handoff_v2_result_v0_1",
        "handoff_manifest_sha256": manifest_hash,
        "attempt_id": attempt_id,
        "status": "PASS",
        "changed_paths": [
            "Makefile",
            "scripts/validation/run_validation_suite_v0_1.py",
            "tests/validation/test_validation_suite_runner_v0_1.py",
        ],
        "validation_evidence": [
            {
                "name": "cf10-worker-pipeline-profiled",
                "result": "PASS",
            }
        ],
        "self_repair_attempts": [],
        "resume_coordinates": {
            "attempt_id": attempt_id,
            "step": "return-result",
        },
        "unresolved_findings": [],
    }


def _frame(payload: dict) -> str:
    body = yaml.safe_dump(
        payload,
        sort_keys=False,
        allow_unicode=True,
    ).rstrip()
    return f"{FRAME_BEGIN}\n{body}\n{FRAME_END}\n"


def test_module_exports_exact_framing_contract() -> None:
    module = _load_result_return()

    assert module.FRAME_BEGIN == FRAME_BEGIN
    assert module.FRAME_END == FRAME_END
    assert issubclass(module.WorkerResultReturnError, RuntimeError)
    assert callable(module.extract_framed_result)
    assert callable(module.materialize_worker_result)


def test_extract_accepts_exactly_one_yaml_mapping_frame() -> None:
    module = _load_result_return()
    expected = _valid_result()

    actual = module.extract_framed_result(_frame(expected))

    assert actual == expected


@pytest.mark.parametrize(
    "stdout_text, expected",
    [
        ("", "missing"),
        ("plain provider prose\n", "missing"),
        (
            f"{FRAME_BEGIN}\nfoo: bar\n",
            "unterminated",
        ),
        (
            f"{FRAME_END}\n",
            "unexpected",
        ),
        (
            _frame(_valid_result()) + _frame(_valid_result()),
            "exactly one",
        ),
        (
            "provider prose\n" + _frame(_valid_result()),
            "outside",
        ),
        (
            _frame(_valid_result()) + "provider prose\n",
            "outside",
        ),
        (
            f"{FRAME_BEGIN}\n- not\n- a\n- mapping\n{FRAME_END}\n",
            "mapping",
        ),
    ],
)
def test_extract_rejects_non_exact_result_transport(
    stdout_text: str,
    expected: str,
) -> None:
    module = _load_result_return()

    with pytest.raises(module.WorkerResultReturnError, match=expected):
        module.extract_framed_result(stdout_text)


def test_materialize_reuses_existing_handoff_validator_and_is_create_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = _load_result_return()

    root = tmp_path / "canonical"
    root.mkdir()
    attempt = tmp_path / "runtime" / "cf10-u180j-a034"
    logs = attempt / "logs"
    logs.mkdir(parents=True)

    manifest_hash = "b" * 64
    manifest = {"handoff_manifest_sha256": manifest_hash}
    payload = _valid_result(
        attempt_id="cf10-u180j-a034",
        manifest_hash=manifest_hash,
    )
    stdout = logs / "stdout.log"
    stdout.write_text(_frame(payload), encoding="utf-8")

    observed: dict = {}

    def fake_validate(result, origin_manifest, *, root):
        observed["result"] = result
        observed["manifest"] = origin_manifest
        observed["root"] = root
        return []

    monkeypatch.setattr(
        module,
        "validate_result_envelope",
        fake_validate,
    )

    materialized = module.materialize_worker_result(
        root=root,
        attempt_root=attempt,
        stdout_path=stdout,
        origin_manifest=manifest,
        expected_attempt_id="cf10-u180j-a034",
    )

    result_path = attempt / "result" / "worker_result.yaml"
    assert result_path.is_file()
    assert materialized["result_path"] == str(result_path)
    assert materialized["result"] == payload
    assert materialized["validation_passed"] is True
    assert observed == {
        "result": payload,
        "manifest": manifest,
        "root": root.resolve(),
    }

    with pytest.raises(
        module.WorkerResultReturnError,
        match="already exists|overwrite",
    ):
        module.materialize_worker_result(
            root=root,
            attempt_root=attempt,
            stdout_path=stdout,
            origin_manifest=manifest,
            expected_attempt_id="cf10-u180j-a034",
        )


def test_materialize_rejects_attempt_binding_mismatch(
    tmp_path: Path,
) -> None:
    module = _load_result_return()

    root = tmp_path / "canonical"
    root.mkdir()
    attempt = tmp_path / "runtime" / "cf10-u180j-a034"
    logs = attempt / "logs"
    logs.mkdir(parents=True)

    manifest_hash = "c" * 64
    stdout = logs / "stdout.log"
    stdout.write_text(
        _frame(
            _valid_result(
                attempt_id="cf10-u180j-other",
                manifest_hash=manifest_hash,
            )
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        module.WorkerResultReturnError,
        match="attempt",
    ):
        module.materialize_worker_result(
            root=root,
            attempt_root=attempt,
            stdout_path=stdout,
            origin_manifest={"handoff_manifest_sha256": manifest_hash},
            expected_attempt_id="cf10-u180j-a034",
        )


def test_materialize_rejects_invalid_handoff_envelope(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = _load_result_return()

    root = tmp_path / "canonical"
    root.mkdir()
    attempt = tmp_path / "runtime" / "cf10-u180j-a034"
    logs = attempt / "logs"
    logs.mkdir(parents=True)

    stdout = logs / "stdout.log"
    stdout.write_text(
        _frame(_valid_result()),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module,
        "validate_result_envelope",
        lambda result, manifest, *, root: [
            {
                "code": "PROOF_INVALID",
                "field": "$",
                "message": "invalid",
            }
        ],
    )

    with pytest.raises(
        module.WorkerResultReturnError,
        match="Handoff v2|validation",
    ):
        module.materialize_worker_result(
            root=root,
            attempt_root=attempt,
            stdout_path=stdout,
            origin_manifest={"handoff_manifest_sha256": "a" * 64},
            expected_attempt_id="cf10-u180j-a034",
        )

    assert not (attempt / "result" / "worker_result.yaml").exists()


def test_materialize_rejects_symlinked_result_directory(
    tmp_path: Path,
) -> None:
    module = _load_result_return()

    root = tmp_path / "canonical"
    root.mkdir()
    attempt = tmp_path / "runtime" / "cf10-u180j-a034"
    logs = attempt / "logs"
    logs.mkdir(parents=True)

    outside = tmp_path / "outside"
    outside.mkdir()
    (attempt / "result").symlink_to(outside, target_is_directory=True)

    stdout = logs / "stdout.log"
    stdout.write_text(
        _frame(_valid_result()),
        encoding="utf-8",
    )

    with pytest.raises(
        module.WorkerResultReturnError,
        match="symlink",
    ):
        module.materialize_worker_result(
            root=root,
            attempt_root=attempt,
            stdout_path=stdout,
            origin_manifest={"handoff_manifest_sha256": "a" * 64},
            expected_attempt_id="cf10-u180j-a034",
        )


def test_invocation_prompt_contains_exact_machine_readable_return_protocol() -> None:
    spec = importlib.util.spec_from_file_location(
        "_cf10_result_return_invocation_adapter_test",
        INVOCATION_ADAPTER,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    prompt = module.render_worker_prompt(
        task_context={
            "task_envelope": {
                "source": {"artifact_ref": "task.yaml"},
            }
        },
        explicit_dispatch_decision={
            "binding": {
                "work_front_ref": "front.yaml",
            }
        },
    )

    assert FRAME_BEGIN in prompt
    assert FRAME_END in prompt
    assert "exactly one" in prompt.lower()
    assert "yaml" in prompt.lower()
    assert "no non-whitespace" in prompt.lower()
    assert "forprint_assistant_handoff_v2_result_v0_1" in prompt
    assert "do not synthesize" in prompt.lower() or "do not invent" in prompt.lower()


def test_makefile_exposes_short_result_return_operator_surface() -> None:
    text = MAKEFILE.read_text(encoding="utf-8")

    assert ".PHONY: cf10-worker-result-return-check" in text
    assert "cf10-worker-result-return-check:" in text
    assert (
        "tests/coordination/control_plane/worker_runtime/"
        "test_cf10_worker_result_return_v0_1.py"
    ) in text

    assert ".PHONY: governed-worker-cycle-reconcile-result-return" in text
    assert "governed-worker-cycle-reconcile-result-return:" in text
    assert "reconcile-result-return" in text
    assert "CONFIRM_RESULT_RETURN_RECONCILIATION" in text
