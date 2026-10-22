"""Isolated behavioral contracts for CF-10 post-worker advancement.

All attempt evidence in these tests belongs to pytest tmp_path.
No real Worker, canonical attempt or operator authorization is modified.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.coordination.control_plane import (
    governed_worker_cycle as cycle,
)

from scripts.coordination.control_plane import candidate_promotion


ATTEMPT_ID = "cf10-u180j-a998"
TASK_PROMPT_ID = (
    "cf10-validation-check-pipeline-profile-and-optimization-v0-1"
)
WORKER_ID = "worker-01"


@pytest.fixture
def isolated_cycle(tmp_path):
    root = tmp_path / "canonical"
    root.mkdir()

    runtime = tmp_path / "runtime"
    runtime.mkdir()

    attempt = (
        runtime
        / "forprint_system_blueprint"
        / WORKER_ID
        / ATTEMPT_ID
    )

    return {
        "root": root,
        "runtime": runtime,
        "attempt": attempt,
    }


def invoke_advance(environment):
    return cycle.advance_cycle(
        root=environment["root"],
        runtime_root=environment["runtime"],
        task_prompt_id=TASK_PROMPT_ID,
        attempt_id=ATTEMPT_ID,
        worker_id=WORKER_ID,
    )


def write_yaml(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            value,
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def file_snapshot(root):
    if not root.exists():
        return {}

    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def assert_blocked(result):
    assert isinstance(result, dict)
    assert result.get("state") == "BLOCKED"

    assert result.get("candidate_promoted") is not True
    assert result.get("automatic_accept") is not True
    assert result.get("commit_performed") is not True
    assert result.get("push_performed") is not True
    assert result.get("release_performed") is not True


def process_finished_fixture(environment):
    path = (
        environment["attempt"]
        / "evidence"
        / "governed_worker_cycle_worker_process_result_v0_1.yaml"
    )

    write_yaml(
        path,
        {
            "schema_version": (
                "forprint_governed_worker_cycle_worker_process_result_v0_1"
            ),
            "attempt_id": ATTEMPT_ID,
            "task_prompt_id": TASK_PROMPT_ID,
            "worker_id": WORKER_ID,
            "process": {
                "return_code": 0,
                "timed_out": False,
            },
            "candidate_promotion_allowed": False,
            "automatic_accept_allowed": False,
            "commit_allowed": False,
            "push_allowed": False,
            "release_allowed": False,
        },
    )


def contradictory_result_fixture(environment):
    """Deliberately invalid evidence, used only to test fail-closed."""

    attempt = environment["attempt"]
    result_path = attempt / "result" / "worker_result.yaml"

    write_yaml(
        result_path,
        {
            "schema_version": (
                "forprint_assistant_handoff_v2_result_v0_1"
            ),
            "handoff_manifest_sha256": "a" * 64,
            "attempt_id": "cf10-u180j-a999",
            "status": "COMPLETED",
            "changed_paths": ["Makefile"],
            "validation_evidence": [],
            "self_repair_attempts": [],
            "resume_coordinates": {},
            "unresolved_findings": [],
        },
    )

    # This PASS marker is intentionally contradictory.
    # It is test input, NOT accepted evidence.
    write_yaml(
        attempt
        / "evidence"
        / "governed_worker_cycle_result_return_v0_1.yaml",
        {
            "schema_version": (
                "forprint_governed_worker_cycle_result_return_v0_1"
            ),
            "attempt_id": ATTEMPT_ID,
            "task_prompt_id": TASK_PROMPT_ID,
            "worker_id": WORKER_ID,
            "result": "PASS",
            "validation_passed": True,
            "result_path": str(result_path),
            "blocked": False,
            "candidate_validation_allowed": True,
            "candidate_promotion_allowed": False,
            "automatic_accept_allowed": False,
        },
    )


def test_advance_entrypoint_exists():
    assert callable(cycle.advance_cycle)


def test_missing_attempt_fails_closed_without_creating_runtime(
    isolated_cycle,
):
    environment = isolated_cycle
    before = file_snapshot(environment["root"])

    result = invoke_advance(environment)

    assert_blocked(result)
    assert not environment["attempt"].exists()
    assert file_snapshot(environment["root"]) == before


def test_missing_result_return_evidence_fails_closed(
    isolated_cycle,
):
    environment = isolated_cycle
    process_finished_fixture(environment)

    before = file_snapshot(environment["attempt"])
    result = invoke_advance(environment)

    assert_blocked(result)

    assert file_snapshot(environment["attempt"]) == before
    assert not (
        environment["attempt"] / "result" / "worker_result.yaml"
    ).exists()


def test_contradictory_result_attempt_binding_fails_closed(
    isolated_cycle,
):
    environment = isolated_cycle
    process_finished_fixture(environment)
    contradictory_result_fixture(environment)

    before = file_snapshot(environment["attempt"])

    result = invoke_advance(environment)

    assert_blocked(result)
    assert file_snapshot(environment["attempt"]) == before

    ledger_dir = (
        environment["root"]
        / "coordination"
        / "continuity"
        / "execution_attempts"
    )

    assert not ledger_dir.exists()


def test_blocked_reentry_does_not_duplicate_evidence(
    isolated_cycle,
):
    environment = isolated_cycle
    process_finished_fixture(environment)

    original = file_snapshot(environment["attempt"])

    first = invoke_advance(environment)
    second = invoke_advance(environment)

    assert_blocked(first)
    assert_blocked(second)

    assert file_snapshot(environment["attempt"]) == original

    ledger_dir = (
        environment["root"]
        / "coordination"
        / "continuity"
        / "execution_attempts"
    )

    assert not ledger_dir.exists()


def test_advance_without_operator_review_never_promotes(
    isolated_cycle,
    monkeypatch,
):
    environment = isolated_cycle
    process_finished_fixture(environment)

    def forbidden_promotion(*args, **kwargs):
        raise AssertionError(
            "advance invoked operator-controlled promotion"
        )

    monkeypatch.setattr(
        candidate_promotion,
        "apply_candidate_promotion",
        forbidden_promotion,
    )

    result = invoke_advance(environment)

    assert_blocked(result)


def test_cli_exposes_advance_action():
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.coordination.control_plane.governed_worker_cycle",
            "--help",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0
    assert "advance" in proc.stdout


def test_makefile_exposes_project_native_advance_target():
    root = Path(__file__).resolve().parents[3]
    makefile = (root / "Makefile").read_text(encoding="utf-8")

    assert "governed-worker-cycle-advance:" in makefile



def test_authorized_positive_delegates_to_canonical_finalizer_and_is_idempotent(
    isolated_cycle, monkeypatch,
):
    """Integration wiring with a test double for the *full* Handoff gate.

    The ledger append is real and immutable; the full S3/S4/freshness gate
    requires a separate canonical end-to-end proof with a genuine manifest.
    """
    from scripts.coordination import execution_attempt_ledger_v0_1 as ledger
    from scripts.coordination import work_front_v0_1
    from scripts.coordination.control_plane import dispatch_intent
    from scripts.coordination.control_plane.workspace import provision as workspace

    environment = isolated_cycle
    canonical, attempt = environment["root"], environment["attempt"]
    repo = Path(__file__).resolve().parents[3]
    for contract_name in (
        "execution_attempt_ledger_contract_v0_1.yaml",
        "work_front_contract_v0_1.yaml",
    ):
        source = repo / "coordination/standards/automation" / contract_name
        destination = canonical / "coordination/standards/automation" / contract_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())

    front_ref = "coordination/work_fronts/test_advance_front.yaml"
    sample = yaml.safe_load((repo / (
        "coordination/work_fronts/"
        "cf10_generic_post_worker_closeout_v0_1.yaml"
    )).read_text(encoding="utf-8"))
    sample["work_front_id"] = "wf-cf10-advance-isolated"
    sample["scope"] = ["a.txt"]
    write_yaml(canonical / front_ref, sample)

    process_finished_fixture(environment)
    result_path = attempt / "result/worker_result.yaml"
    write_yaml(result_path, {
        "schema_version": "forprint_assistant_handoff_v2_result_v0_1",
        "handoff_manifest_sha256": "a" * 64,
        "attempt_id": ATTEMPT_ID,
        "status": "COMPLETED",
        "changed_paths": ["a.txt"],
        "validation_evidence": [{"name": "pytest", "result": "PASS"}],
        "self_repair_attempts": [],
        "resume_coordinates": {"attempt_id": ATTEMPT_ID, "step": "done"},
        "unresolved_findings": [],
    })
    write_yaml(attempt / "evidence/governed_worker_cycle_result_return_v0_1.yaml", {
        "schema_version": "forprint_governed_worker_cycle_result_return_v0_1",
        "attempt_id": ATTEMPT_ID,
        "task_prompt_id": TASK_PROMPT_ID,
        "worker_id": WORKER_ID,
        "result": "PASS", "validation_passed": True, "blocked": False,
        "worker_result_synthesized": False,
        "candidate_validation_allowed": True,
        "result_path": str(result_path),
    })
    write_yaml(attempt / "input/governed_worker_cycle_source_state_v0_1.yaml", {
        "fingerprint_sha256": "f" * 64,
    })
    write_yaml(attempt / "input/governed_worker_cycle_prepared_execution_v0_1.yaml", {
        "handoff_manifest_sha256": "a" * 64,
    })
    write_yaml(attempt / "input/governed_worker_cycle_origin_handoff_manifest_v0_1.yaml", {
        "handoff_manifest_sha256": "a" * 64,
        "launch_mode": "TASK_EXECUTION",
    })
    workspace_path = attempt / "workspace/repo"
    workspace_path.mkdir(parents=True)
    decision = {
        "binding": {
            "attempt_id": ATTEMPT_ID,
            "task_prompt_id": TASK_PROMPT_ID,
            "worker_id": WORKER_ID,
            "work_front_id": "wf-cf10-advance-isolated",
            "workspace_repo": str(workspace_path),
        },
        "explicit_dispatch_decision_recorded": True,
        "worker_process_launch_allowed": True,
        "canonical_attempt_ledger_append_allowed": True,
        "external_dispatch_allowed": False,
        "release_allowed": False,
        "push_allowed": False,
        "merge_allowed": False,
        "foreign_repository_write_allowed": False,
        "automatic_accept_allowed": False,
    }
    write_yaml(
        attempt / "input/governed_worker_cycle_explicit_dispatch_decision_v0_1.yaml",
        decision,
    )
    started = {
        "schema_version": "forprint_execution_attempt_record_v0_1",
        "attempt_id": ATTEMPT_ID,
        "work_front_id": "wf-cf10-advance-isolated",
        "recorded_at": "2026-10-08T12:00:00Z",
        "actor_or_worker_ref": WORKER_ID,
        "where": str(workspace_path),
        "why": "isolated test of canonical ledger append",
        "source_fingerprint": "f" * 64,
        "profile_ref_or_revision": "light-maintenance@r1",
        "pack_hash_or_context_hash": "a" * 64,
        "launch_or_invocation_ref": str(attempt / "input/decision.yaml"),
        "attempt_stage": "STARTED", "result_state": "PENDING",
        "result_refs": [], "validator_outcome": "NOT_RUN",
        "validator_evidence_refs": [], "failure_or_retry_ref": None,
        "resume": {"latest_accepted_ref": None, "resume_coordinates": [],
                   "replay_forbidden_refs": []},
    }
    ledger.append_record(canonical, started)
    binding = {"work_front_id": "wf-cf10-advance-isolated", "work_front_ref": front_ref}
    monkeypatch.setattr(cycle.training, "resolve_training_task", lambda **kwargs: binding)
    monkeypatch.setattr(cycle, "_assert_frozen_source_state_current", lambda *a, **k: {})
    # This existing test isolates ledger orchestration. Real origin hashing is
    # exercised separately below, without replacing the canonical extractor.
    monkeypatch.setattr(
        cycle, "_load_verified_original_handoff_manifest",
        lambda **kwargs: yaml.safe_load((attempt / "input" /
            "governed_worker_cycle_origin_handoff_manifest_v0_1.yaml").read_text(
            encoding="utf-8")),
    )
    monkeypatch.setattr(
        cycle, "_validated_project_native_governed_worker_context",
        lambda **kwargs: {"handoff_manifest_sha256": "a" * 64},
    )
    monkeypatch.setattr(
        cycle.worker_result_return, "_s4_resume_origin", lambda **kwargs: {},
    )
    monkeypatch.setattr(
        cycle.worker_result_return, "validate_resume", lambda *a, **k: [],
    )
    monkeypatch.setattr(
        cycle.worker_result_return, "validate_result_envelope",
        lambda *a, **k: [],
    )
    delta = {
        "schema_version": "forprint_worker_workspace_delta_v0_1",
        "attempt_id": ATTEMPT_ID, "workspace_repo": str(workspace_path),
        "source_head": "b" * 40,
        "baseline_fingerprint_sha256": "f" * 64,
        "changed_paths": ["a.txt"],
        "worker_delta_exact": True, "authority_granted": False,
        "candidate_promoted": False, "canonical_write_performed": False,
    }
    monkeypatch.setattr(
        workspace, "derive_worker_delta_from_manifest", lambda manifest: delta,
    )
    finalizer_calls = []

    def canonical_finalizer_double(**kwargs):
        finalizer_calls.append(kwargs)
        assert kwargs["origin_manifest"]["handoff_manifest_sha256"] == "a" * 64
        assert kwargs["result_artifact_path"] == result_path
        record = kwargs["attempt_record"]
        assert record["attempt_stage"] == "FINISHED"
        assert record["result_state"] == "SUCCEEDED"
        saved = ledger.append_record(canonical, record)
        return {
            "state": "ATTEMPT_RECORDED",
            "canonical_attempt_record_written": True,
            "canonical_attempt_record_path": str(saved),
            "result_validation": {"valid": True},
            "worker_delta_verification": {"valid": True},
        }

    monkeypatch.setattr(
        dispatch_intent,
        "finalize_cf10_workspace_result_artifact",
        canonical_finalizer_double,
    )
    monkeypatch.setattr(
        candidate_promotion,
        "apply_candidate_promotion",
        lambda *args, **kwargs: pytest.fail("PROMOTION_MUST_NOT_BE_CALLED"),
    )

    first = invoke_advance(environment)
    assert first["state"] == "AWAITING_OPERATOR_REVIEW", first
    store = ledger.store_root(canonical, ledger.load_contract(canonical), None)
    assert len(ledger.records_for_attempt(store, ATTEMPT_ID)) == 2
    snapshot = file_snapshot(attempt)

    second = invoke_advance(environment)
    assert second["state"] == "AWAITING_OPERATOR_REVIEW", second
    assert len(ledger.records_for_attempt(store, ATTEMPT_ID)) == 2
    assert len(finalizer_calls) == 1
    assert file_snapshot(attempt) == snapshot


# CF10_GENUINE_ORIGIN_PROVENANCE_TESTS_V0_1_START

def _real_origin_source_fixture(tmp_path):
    """Use the canonical CF-09 manifest digest and extractor, not a fake PASS."""
    from scripts.coordination.control_plane import dispatch_intent

    root = tmp_path / "canonical"
    root.mkdir()
    fingerprint = "c" * 64  # Handoff fingerprint (NOT continuity fingerprint)
    head = "b" * 40
    origin = {
        "schema_version": "forprint_assistant_handoff_v2_runtime_manifest_v0_1",
        "launch_mode": "TASK_EXECUTION",
        "authority": {
            "execution_authority_granted": False,
            "dispatch_authority_granted": False,
            "release_authority_granted": False,
            "cross_repository_write_authority_granted": False,
        },
        "source_state_fingerprint": fingerprint,
        "dependency_health_slice": {"dependency": "ok"},
        "lifecycle_roadmap_cursor": {"open_work": {}},
        "resume_coordinates": {"git_head": head, "work_id": "u180j"},
        "expected_result_schema_revision": "v0_1",
        "work_front_or_project_onboard_not_applicable_reason": {},
        "execution_profile_revision_for_task_execution": {},
        "governed_procedure_revision_or_not_required_reason": {},
    }
    digest = dispatch_intent._cf09_handoff_manifest_sha256(origin)
    origin["handoff_manifest_sha256"] = digest
    ref = "tmp/assistant_handoff_v2_runtime/test/origin_manifest.yaml"
    producer = root / ref
    write_yaml(producer, origin)
    context, context_sha = dispatch_intent._cf09_extract_governed_worker_context(
        root=root, runtime_manifest_ref=ref, expected_manifest_sha256=digest,
    )
    attempt = tmp_path / "runtime/forprint_system_blueprint/worker-01/cf10-u180j-a998"
    (attempt / "input").mkdir(parents=True)
    prepared = {
        "handoff_manifest_sha256": digest,
        "origin_handoff_runtime_manifest_ref": ref,
        "governed_worker_context": context,
        "governed_worker_context_sha256": context_sha,
    }
    source = {"git_head": head, "fingerprint_sha256": "d" * 64}
    return root, attempt, producer, origin, prepared, source


def test_genuine_cf09_origin_is_snapshotted_before_dispatch(tmp_path):
    root, attempt, producer, origin, prepared, source = _real_origin_source_fixture(tmp_path)
    destination = cycle._persist_original_handoff_manifest(
        canonical=root, attempt=attempt,
        prepared_execution=prepared, source_state=source,
    )
    assert destination.is_file()
    assert destination.read_bytes() == producer.read_bytes()
    assert yaml.safe_load(destination.read_text(encoding="utf-8")) == origin
    assert cycle._load_verified_original_handoff_manifest(
        attempt=attempt, prepared_execution=prepared, source_state=source,
    ) == origin
    assert source["fingerprint_sha256"] != origin["source_state_fingerprint"]
    producer.unlink()
    assert cycle._load_verified_original_handoff_manifest(
        attempt=attempt, prepared_execution=prepared, source_state=source,
    ) == origin


def test_origin_producer_hash_tampering_fails_before_snapshot(tmp_path):
    root, attempt, producer, origin, prepared, source = _real_origin_source_fixture(tmp_path)
    origin["dependency_health_slice"] = {"tampered": True}
    write_yaml(producer, origin)
    with pytest.raises(Exception, match="hash|drift|mismatch"):
        cycle._persist_original_handoff_manifest(
            canonical=root, attempt=attempt,
            prepared_execution=prepared, source_state=source,
        )
    assert not (attempt / "input" / cycle._ORIGINAL_HANDOFF_INPUT_NAME).exists()


def test_origin_snapshot_reentry_does_not_overwrite(tmp_path):
    root, attempt, producer, origin, prepared, source = _real_origin_source_fixture(tmp_path)
    path = cycle._persist_original_handoff_manifest(
        canonical=root, attempt=attempt,
        prepared_execution=prepared, source_state=source,
    )
    original = path.read_bytes()
    with pytest.raises(cycle.GovernedWorkerCycleError, match="overwrite"):
        cycle._persist_original_handoff_manifest(
            canonical=root, attempt=attempt,
            prepared_execution=prepared, source_state=source,
        )
    assert path.read_bytes() == original


def test_origin_copy_tampering_detected_during_advance_preflight(tmp_path):
    root, attempt, producer, origin, prepared, source = _real_origin_source_fixture(tmp_path)
    path = cycle._persist_original_handoff_manifest(
        canonical=root, attempt=attempt,
        prepared_execution=prepared, source_state=source,
    )
    edited = dict(origin)
    edited["dependency_health_slice"] = {"tampered": True}
    write_yaml(path, edited)
    with pytest.raises(cycle.GovernedWorkerCycleError, match="HASH_DRIFT"):
        cycle._load_verified_original_handoff_manifest(
            attempt=attempt, prepared_execution=prepared, source_state=source,
        )


def test_origin_producer_path_escape_is_forbidden(tmp_path):
    root, attempt, producer, origin, prepared, source = _real_origin_source_fixture(tmp_path)
    prepared["origin_handoff_runtime_manifest_ref"] = "../../etc/passwd"
    with pytest.raises(Exception, match="escapes|outside"):
        cycle._persist_original_handoff_manifest(
            canonical=root, attempt=attempt,
            prepared_execution=prepared, source_state=source,
        )
    assert not (attempt / "input" / cycle._ORIGINAL_HANDOFF_INPUT_NAME).exists()


def test_cf09_producer_envelope_carries_verified_runtime_origin_ref(tmp_path):
    from scripts.coordination.control_plane import dispatch_intent
    from types import SimpleNamespace

    root, attempt, producer, origin, prepared, source = _real_origin_source_fixture(tmp_path)
    runtime_file = root / "scripts/coordination/work_front_v0_1.py"
    runtime_file.parent.mkdir(parents=True, exist_ok=True)
    runtime_file.write_text("# test-only runtime marker\n", encoding="utf-8")
    def fake_runner(argv, **_kwargs):
        if argv[0] == "make":
            return SimpleNamespace(returncode=0, stdout=(
                "ASSISTANT_HANDOFF_V2_RUNTIME=PASS\n"
                "LAUNCH_MODE=TASK_EXECUTION\n"
                "EXECUTION_AUTHORITY_GRANTED=false\n"
                "DISPATCH_AUTHORITY_GRANTED=false\n"
                "WORKER_DISPATCH_PERFORMED=false\n"
                f"HANDOFF_MANIFEST_SHA256={prepared['handoff_manifest_sha256']}\n"
                f"RUNTIME_MANIFEST={prepared['origin_handoff_runtime_manifest_ref']}\n"
            ))
        return SimpleNamespace(returncode=0, stdout=(
            "WORK_FRONT_VALIDATION=PASS\nWORK_FRONT_ID=wf-test\n"
            "WORK_FRONT_PATH=coordination/work_fronts/test.yaml\n"
        ))
    result = dispatch_intent.prepare_cf09_task_execution(
        root=root,
        work_front="coordination/work_fronts/test.yaml",
        execution_profile="light-maintenance",
        task_prompt_id="task-test",
        task_module_root=".",
        module="forprint_system_blueprint",
        procedure_id="governed_canonical_mutation",
        runner=fake_runner,
    )
    assert result["origin_handoff_runtime_manifest_ref"] == prepared[
        "origin_handoff_runtime_manifest_ref"
    ]
    assert result["handoff_manifest_sha256"] == prepared["handoff_manifest_sha256"]
    assert result["governed_worker_context"] == prepared["governed_worker_context"]

# CF10_GENUINE_ORIGIN_PROVENANCE_TESTS_V0_1_END


# CF10_POST_WORKER_OWNED_LEDGER_FINGERPRINT_REGRESSION_V0_1
@pytest.fixture
def owned_ledger_drift(tmp_path, monkeypatch):
    """Real canonical ledger records with synthetic source snapshots only."""
    from scripts.coordination import execution_attempt_ledger_v0_1 as ledger
    from copy import deepcopy

    root = tmp_path / 'canonical'
    root.mkdir()
    source = Path(__file__).resolve().parents[3] / (
        'coordination/standards/automation/execution_attempt_ledger_contract_v0_1.yaml'
    )
    contract_path = root / 'coordination/standards/automation/execution_attempt_ledger_contract_v0_1.yaml'
    contract_path.parent.mkdir(parents=True)
    contract_path.write_bytes(source.read_bytes())
    attempt_id = 'cf10-isolated-source-ledger-a998'
    starter = {
        'schema_version': 'forprint_execution_attempt_record_v0_1',
        'attempt_id': attempt_id,
        'work_front_id': 'wf-isolated',
        'recorded_at': '2026-10-10T09:00:00Z',
        'actor_or_worker_ref': 'worker-01',
        'where': 'isolated-worker-workspace',
        'why': 'unit test own append-only ledger delta',
        'source_fingerprint': 'a' * 64,
        'profile_ref_or_revision': 'test@v1',
        'pack_hash_or_context_hash': 'b' * 64,
        'launch_or_invocation_ref': 'isolated:launch',
        'attempt_stage': 'STARTED',
        'result_state': 'PENDING',
        'result_refs': [],
        'validator_outcome': 'NOT_RUN',
        'validator_evidence_refs': [],
        'failure_or_retry_ref': None,
        'resume': {
            'latest_accepted_ref': None,
            'resume_coordinates': [],
            'replay_forbidden_refs': [],
        },
    }
    record_path = ledger.append_record(root, starter)
    store = ledger.store_root(root, ledger.load_contract(root), None)
    relative = record_path.relative_to(root).as_posix()
    frozen = {
        'schema_version': 'forprint_source_state_v0_1',
        'source_mode': 'working_tree',
        'git_head': 'c' * 40,
        'git_branch': 'fixture',
        'durable_dirty_paths': ['existing.txt'],
        'dirty_path_status': {'existing.txt': ' M'},
        'dirty_path_content_or_symlink_fingerprint': {
            'existing.txt': {'type': 'file', 'sha256': 'd' * 64}
        },
        'rename_or_copy_origins': {},
        'bounded_final_applied_artifact_hashes': {},
        'exclusion_policy': {'reports_implicitly_excluded': False},
        'fingerprint_sha256': 'a' * 64,
    }
    current = deepcopy(frozen)
    current['fingerprint_sha256'] = 'e' * 64
    current['durable_dirty_paths'].append(relative)
    current['dirty_path_status'][relative] = '??'
    current['dirty_path_content_or_symlink_fingerprint'][relative] = {
        'type': 'file', 'sha256': 'f' * 64
    }
    def strict_stale(*args, **kwargs):
        raise cycle.GovernedWorkerCycleError(
            'post-worker candidate validation: frozen source state is stale'
        )
    monkeypatch.setattr(cycle, '_assert_frozen_source_state_current', strict_stale)
    monkeypatch.setattr(cycle, 'build_source_state', lambda root: current)
    return {
        'root': root, 'store': store, 'ledger': ledger,
        'record': starter, 'records': [starter],
        'path': record_path, 'relative': relative,
        'frozen': frozen, 'current': current,
        'attempt_id': attempt_id,
    }


def _check_owned_delta(case):
    return cycle._assert_post_worker_source_state_current(
        case['root'], case['frozen'],
        attempt_id=case['attempt_id'], records=case['records'], store=case['store'],
    )


def test_post_worker_accepts_only_own_canonical_started_append(owned_ledger_drift):
    assert _check_owned_delta(owned_ledger_drift) is owned_ledger_drift['current']


def test_post_worker_rejects_unrelated_added_file(owned_ledger_drift):
    case = owned_ledger_drift
    case['current']['durable_dirty_paths'].append('unrelated.py')
    case['current']['dirty_path_status']['unrelated.py'] = '??'
    case['current']['dirty_path_content_or_symlink_fingerprint']['unrelated.py'] = {
        'type': 'file', 'sha256': 'f' * 64
    }
    with pytest.raises(cycle.GovernedWorkerCycleError, match='NON_LEDGER_SOURCE_DRIFT'):
        _check_owned_delta(case)


def test_post_worker_rejects_existing_dirty_content_change(owned_ledger_drift):
    case = owned_ledger_drift
    case['current']['dirty_path_content_or_symlink_fingerprint']['existing.txt'] = {
        'type': 'file', 'sha256': '0' * 64
    }
    with pytest.raises(cycle.GovernedWorkerCycleError, match='NON_LEDGER_SOURCE_DRIFT'):
        _check_owned_delta(case)


def test_post_worker_rejects_ledger_content_tampering(owned_ledger_drift):
    case = owned_ledger_drift
    bad = dict(case['record'])
    bad['why'] = 'tampered after immutable append'
    case['path'].write_text(yaml.safe_dump(bad), encoding='utf-8')
    with pytest.raises(cycle.GovernedWorkerCycleError, match='CONTENT_MISMATCH'):
        _check_owned_delta(case)


def test_post_worker_allows_own_verified_terminal_append_on_reentry(owned_ledger_drift):
    case = owned_ledger_drift
    terminal = dict(case['record'])
    terminal.update({
        'recorded_at': '2026-10-10T09:00:01Z',
        'attempt_stage': 'FINISHED',
        'result_state': 'SUCCEEDED',
        'validator_outcome': 'PASS',
        'result_refs': ['isolated:result'],
        'validator_evidence_refs': ['isolated:validated-result'],
    })
    path = case['ledger'].append_record(case['root'], terminal)
    relative = path.relative_to(case['root']).as_posix()
    case['records'].append(terminal)
    case['current']['durable_dirty_paths'].append(relative)
    case['current']['durable_dirty_paths'].sort()
    case['current']['dirty_path_status'][relative] = '??'
    case['current']['dirty_path_content_or_symlink_fingerprint'][relative] = {
        'type': 'file', 'sha256': '1' * 64
    }
    assert _check_owned_delta(case) is case['current']
