"""All fixture tests; NO production state, external signers, ledger or Worker."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys
import types

import pytest

P = Path(__file__).with_name("cf10_s01_controlled_launch_corridor_v0_1.py")
if not P.exists():
    P = Path(__file__).resolve().parents[3] / "scripts/coordination/control_plane/cf10_s01_controlled_launch_corridor_v0_1.py"
spec = importlib.util.spec_from_file_location("cf10_corridor_preflight_fixture", P)
corridor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(corridor)

@pytest.fixture(autouse=True)
def isolate_existing_root_state_module(monkeypatch):
    """Fixture-only stand-in; never reads /var/lib or actual project files."""
    scripts = types.ModuleType("scripts")
    coordination = types.ModuleType("scripts.coordination")
    plane = types.ModuleType("scripts.coordination.control_plane")
    root_state = types.ModuleType("scripts.coordination.control_plane.cf10_s01_root_controlled_single_use_v0_2")
    root_state.validate_binding = lambda binding: [] if binding.get("worker_id") == "worker-01" else ["WORKER_ID_INVALID"]
    plane.cf10_s01_root_controlled_single_use_v0_2 = root_state
    scripts.coordination = coordination
    coordination.control_plane = plane
    for name, mod in [("scripts", scripts), ("scripts.coordination", coordination),
                      ("scripts.coordination.control_plane", plane),
                      ("scripts.coordination.control_plane.cf10_s01_root_controlled_single_use_v0_2", root_state)]:
        monkeypatch.setitem(sys.modules, name, mod)


HEAD = "a" * 40
WORKER = "worker-01"
TASK = "cf10-s01-bounded-operator-pilot-v0-1"
ATTEMPT = "cf10-u180j-a048"


def root(tmp_path, *, guarded=False):
    d = tmp_path / "repo"
    p = d / "scripts/coordination/control_plane/governed_worker_cycle.py"
    p.parent.mkdir(parents=True)
    gate = "    require_bounded_s01_launch_authority()\n" if guarded else ""
    p.write_text("def launch_cycle():\n" + gate + "    pass\n\n"
                 "def launch_authorized_worker_cycle():\n" + gate + "    pass\n")
    (d / "Makefile").write_text("cf10-s01-runtime-launch-preflight:\n\t@echo QUARANTINED_NEEDS_INDEPENDENT_REBIND; exit 2\n")
    return d


def binding():
    return {"receipt_sha256": "b" * 64, "publication_commit": HEAD,
            "worker_id": WORKER, "task_prompt_id": TASK, "attempt_id": ATTEMPT}


def test_current_unguarded_python_routes_explicitly_identified(tmp_path):
    d = root(tmp_path)
    assert corridor.launch_route_blockers(d) == [
        "DIRECT_PYTHON_LAUNCH_UNGUARDED:launch_cycle",
        "DIRECT_PYTHON_LAUNCH_UNGUARDED:launch_authorized_worker_cycle"]


@pytest.mark.parametrize("name", ["launch_cycle", "launch_authorized_worker_cycle"])
def test_one_python_route_cannot_cover_other(tmp_path, name):
    d = root(tmp_path)
    p = d / "scripts/coordination/control_plane/governed_worker_cycle.py"
    src = p.read_text().replace("def " + name + "():\n", "def " + name + "():\n    require_bounded_s01_launch_authority()\n")
    p.write_text(src)
    assert len(corridor.launch_route_blockers(d)) == 1


def test_two_static_guard_references_never_prove_live_authority(tmp_path, monkeypatch):
    d = root(tmp_path, guarded=True)
    monkeypatch.setattr(corridor, "_signed_binding", lambda *a, **kw: (binding(), []))
    monkeypatch.setattr(corridor, "_root_state_readiness", lambda: "READY_READ_ONLY_NOT_RESERVED")
    result = corridor.evaluate(d, worker_id=WORKER, task_prompt_id=TASK, attempt_id=ATTEMPT)
    assert result["checks"]["python_routes"] == "STATIC_GUARD_REFERENCES_PRESENT"
    assert result["blockers"] == ["LIVE_MAKE_QUARANTINE_RETAINED"]
    assert result["status"] == "BLOCKED_NON_AUTHORIZING"
    assert result["claim_record_written"] is False
    assert result["claim_consumed"] is False
    assert all(result[k] is False for k in ("worker_launched", "launch_allowed", "authority_granted", "live_make_wired"))


def test_no_pilot_params_skips_all_external_checks(tmp_path, monkeypatch):
    d = root(tmp_path)
    monkeypatch.setattr(corridor, "_signed_binding", lambda *a, **kw: (_ for _ in ()).throw(AssertionError("called")))
    monkeypatch.setattr(corridor, "_root_state_readiness", lambda: (_ for _ in ()).throw(AssertionError("called")))
    r = corridor.evaluate(d, worker_id="", task_prompt_id="", attempt_id="")
    assert "EXPLICIT_WORKER_TASK_ATTEMPT_REQUIRED" in r["blockers"]


def test_missing_or_symlinked_launch_source_blocks(tmp_path):
    d = root(tmp_path)
    p = d / "scripts/coordination/control_plane/governed_worker_cycle.py"
    p.unlink()
    assert corridor.launch_route_blockers(d) == ["GOVERNED_CYCLE_SOURCE_UNAVAILABLE"]
    p.symlink_to(d / "Makefile")
    assert corridor.launch_route_blockers(d) == ["GOVERNED_CYCLE_SOURCE_UNAVAILABLE"]


def test_syntax_failure_blocks(tmp_path):
    d = root(tmp_path)
    p = d / "scripts/coordination/control_plane/governed_worker_cycle.py"
    p.write_text("def launch_cycle(:\n")
    assert corridor.launch_route_blockers(d) == ["GOVERNED_CYCLE_SOURCE_UNREADABLE"]


@pytest.mark.parametrize("state_error", ["ROOT_CONTROLLED_STATE_NOT_VERIFIED", "PERSISTENT_SINGLE_USE_ALREADY_CONSUMED", "PERSISTENT_STATE_NOT_INSPECTABLE"])
def test_root_store_unready_or_consumed_blocks(tmp_path, monkeypatch, state_error):
    d = root(tmp_path)
    monkeypatch.setattr(corridor, "_signed_binding", lambda *a, **kw: (binding(), []))
    monkeypatch.setattr(corridor, "_root_state_readiness", lambda: state_error)
    r = corridor.evaluate(d, worker_id=WORKER, task_prompt_id=TASK, attempt_id=ATTEMPT)
    assert state_error in r["blockers"]
    assert r["claim_record_written"] is False


def test_signed_failure_blocks_without_claim(tmp_path, monkeypatch):
    d = root(tmp_path)
    monkeypatch.setattr(corridor, "_signed_binding", lambda *a, **kw: (None, ["SIGNED_PILOT_PREDICATE_NOT_VERIFIED"]))
    monkeypatch.setattr(corridor, "_root_state_readiness", lambda: "READY_READ_ONLY_NOT_RESERVED")
    r = corridor.evaluate(d, worker_id=WORKER, task_prompt_id=TASK, attempt_id=ATTEMPT)
    assert "SIGNED_PILOT_PREDICATE_NOT_VERIFIED" in r["blockers"]
    assert r["signed_binding_sha256"] is None
    assert r["claim_consumed"] is False


def test_invalid_signed_binding_blocks(tmp_path, monkeypatch):
    d = root(tmp_path)
    fake = binding(); fake["worker_id"] = "worker-02"
    monkeypatch.setattr(corridor, "_signed_binding", lambda *a, **kw: (fake, []))
    monkeypatch.setattr(corridor, "_root_state_readiness", lambda: "READY_READ_ONLY_NOT_RESERVED")
    r = corridor.evaluate(d, worker_id=WORKER, task_prompt_id=TASK, attempt_id=ATTEMPT)
    assert "ROOT_CLAIM_BINDING_CONTRACT_MISMATCH" in r["blockers"]


def test_unexpected_inspection_exception_is_fail_closed(monkeypatch):
    monkeypatch.setattr(corridor, "evaluate", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("sensitive")))
    assert corridor.main(["inspect"]) == 0
    assert corridor.main(["launch-preflight"]) == 2


def test_hypothetical_clean_evaluate_still_never_launch_preflight(monkeypatch):
    monkeypatch.setattr(corridor, "evaluate", lambda *a, **kw: {"status": "INSPECTED", "blockers": [], "launch_allowed": False})
    assert corridor.main(["launch-preflight"]) == 2


def install_mock_modules(monkeypatch, *, base_ok=True, second_signature=True, scope_errors=None,
                         proof_errors=None, proof_count=8, first_head=HEAD, second_head=HEAD):
    rebind = types.ModuleType("scripts.coordination.control_plane.cf10_s01_runtime_rebind_v0_2")
    rebind.RECEIPT_FILE = Path("/does/not/get/opened/in/fixture")
    rebind.REQUIREMENTS = tuple("x" for _ in range(8))
    rebind.evaluate = lambda *a, **kw: {"status": "PREDICATE_PASS_NON_AUTHORIZING" if base_ok else "BLOCKED_NON_AUTHORIZING",
                                        "predicate_pass": base_ok, "blockers": [] if base_ok else ["blocked"],
                                        "launch_allowed": False, "authority_granted": False}
    receipt = {"pilot_scope": "fixture"}
    raw = b'fixture signed bytes\n'
    rebind._trusted_json = lambda *a: (receipt, raw)
    rebind._reverify_receipt = lambda *a: second_signature
    rebind.scope_blockers = lambda *a, **kw: scope_errors or []
    rebind.proof_blockers = lambda *a: (proof_errors or [], proof_count)
    scripts = types.ModuleType("scripts")
    coord = types.ModuleType("scripts.coordination")
    plane = types.ModuleType("scripts.coordination.control_plane")
    plane.cf10_s01_runtime_rebind_v0_2 = rebind
    scripts.coordination = coord
    coord.control_plane = plane
    for n, m in [("scripts", scripts), ("scripts.coordination", coord),
                 ("scripts.coordination.control_plane", plane),
                 ("scripts.coordination.control_plane.cf10_s01_runtime_rebind_v0_2", rebind)]:
        monkeypatch.setitem(sys.modules, n, m)
    heads = iter([first_head, second_head])
    monkeypatch.setattr(corridor, "_git_head", lambda root: next(heads))
    return raw


def test_signed_predicate_is_recomputed_and_receipt_digest_comes_from_bytes(monkeypatch, tmp_path):
    raw = install_mock_modules(monkeypatch)
    result, errors = corridor._signed_binding(tmp_path, worker_id=WORKER,
                                            task_prompt_id=TASK, attempt_id=ATTEMPT)
    assert errors == []
    assert result["receipt_sha256"] == corridor._sha(raw)
    assert result["publication_commit"] == HEAD


@pytest.mark.parametrize("problem,expected", [
    ({"base_ok": False}, "SIGNED_PILOT_PREDICATE_NOT_VERIFIED"),
    ({"second_signature": False}, "RELEASE_RECEIPT_SIGNATURE_REREAD_FAILED"),
    ({"scope_errors": ["SCOPE_MISMATCH"]}, "SCOPE_MISMATCH"),
    ({"proof_errors": ["PROOF_BYTES_MISMATCH"]}, "PROOF_BYTES_MISMATCH"),
    ({"proof_count": 7}, "INDEPENDENT_PROOF_MATRIX_NOT_ACCEPTED"),
    ({"second_head": "f" * 40}, "SOURCE_HEAD_CHANGED_DURING_CORRIDOR"),
])
def test_all_signed_boundary_mismatches_fail_closed(monkeypatch, tmp_path, problem, expected):
    install_mock_modules(monkeypatch, **problem)
    result, errors = corridor._signed_binding(tmp_path, worker_id=WORKER,
                                            task_prompt_id=TASK, attempt_id=ATTEMPT)
    assert result is None
    assert expected in errors


def test_live_make_not_replaced_or_authorized(tmp_path, monkeypatch):
    d = root(tmp_path)
    (d / "Makefile").write_text("unguarded new launch:\n\t@echo OOPS\n")
    r = corridor.evaluate(d, worker_id="", task_prompt_id="", attempt_id="")
    assert "LIVE_MAKE_QUARANTINE_ABSENT_REQUIRES_INDEPENDENT_REVIEW" in r["blockers"]
    assert r["live_make_wired"] is False


def test_source_has_no_actual_worker_or_claim_calls():
    source = P.read_text("utf-8")
    for prohibited in ("consume_once_fd(", "launch_authorized_worker_cycle(",
                       "subprocess.Popen(", "launcher.launch(", "ledger.append_record(",
                       "git push", "git commit", "os.system("):
        assert prohibited not in source
