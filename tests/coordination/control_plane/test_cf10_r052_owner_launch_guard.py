"""r052 source-bound attachment is fail-closed and never launch authority."""
from pathlib import Path
import ast
import hashlib
import inspect
import types
import pytest

from scripts.coordination.control_plane import cf10_r052_owner_launch_guard_v0_1 as gate
from scripts.coordination.control_plane import cf10_r050_two_phase_pilot_v0_1 as phase
from scripts.coordination.control_plane import cf10_owner_pam_launch_v0_1 as owner


HEAD='2e9e70c2cf916c632aca54da439409f832dc7ccc'
TASK=gate.TASK
ATTEMPT='cf10-u180j-a199'


def test_requirements_never_authorize():
    x=gate.requirements()
    assert x['launch_allowed'] is False
    assert x['production_cutover'] is False
    assert x['production_worker_launched'] is False
    assert x['root_preclaim_recollected'] is False
    assert x['status']=='GUARD_WIRED_PILOT_RELEASE_NOT_ACTIVATED'


def test_guard_does_not_export_launch_or_issue_api():
    code=Path(inspect.getfile(gate)).read_text()
    funcs={x.name for x in ast.parse(code).body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
    assert 'launch' not in funcs and 'issue' not in funcs and 'consume' not in funcs
    assert not any('subprocess.Popen' in ast.unparse(node) for node in ast.walk(ast.parse(code)) if isinstance(node,ast.Call))


def test_invalid_stage_fail_closed_before_observers(monkeypatch):
    monkeypatch.setattr(gate,'_observe',lambda **kw: pytest.fail('called live observer'))
    with pytest.raises(gate.LaunchGuardBlocked, match='INVALID_BOUNDARY_STAGE'):
        gate._assert_stage(stage='OTHER',root=gate.PROJECT,runtime_root=gate.RUNTIME,task=TASK,attempt=ATTEMPT,head=HEAD)


@pytest.mark.parametrize('field',sorted(set(phase.REQUIRED_LAUNCH_OBSERVATIONS)-{'owner_pam_session_authenticated'}))
def test_any_missing_observation_blocks_before_password(monkeypatch,field):
    observations={k:True for k in phase.REQUIRED_LAUNCH_OBSERVATIONS if k!='owner_pam_session_authenticated'}
    observations[field]=False
    monkeypatch.setattr(gate,'_observe',lambda **kw: observations)
    with pytest.raises(gate.LaunchGuardBlocked, match='BOUNDARY_INCOMPLETE'):
        gate.assert_pre_password(root=gate.PROJECT,runtime_root=gate.RUNTIME,task=TASK,attempt=ATTEMPT,head=HEAD)


def test_missing_observation_does_not_default_to_true(monkeypatch):
    monkeypatch.setattr(gate,'_observe',lambda **kw: {})
    with pytest.raises(gate.LaunchGuardBlocked, match='BOUNDARY_INCOMPLETE'):
        gate.assert_pre_password(root=gate.PROJECT,runtime_root=gate.RUNTIME,task=TASK,attempt=ATTEMPT,head=HEAD)


def test_read_only_requirements_cli(capsys):
    assert gate.main(['--mode','requirements'])==0
    assert 'GUARD_WIRED_PILOT_RELEASE_NOT_ACTIVATED' in capsys.readouterr().out


def test_make_quarantine_not_counted_as_launch_route(tmp_path):
    (tmp_path/'Makefile').write_text('cf10-s01-runtime-launch-preflight:\n\t@echo QUARANTINED_NEEDS_INDEPENDENT_REBIND; exit 2\n')
    assert not gate._make_has_guarded_pilot_route(tmp_path)


def test_unrelated_read_only_make_target_not_counted(tmp_path):
    (tmp_path/'Makefile').write_text('cf10-s01-runtime-launch-preflight:\n\t@echo \"CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND\"; exit 2\ncf10-r052-owner-launch-check:\n\tpython -m scripts.coordination.control_plane.cf10_r052_owner_launch_guard_v0_1 --mode guarded-preflight\n')
    assert not gate._make_has_guarded_pilot_route(tmp_path)


def test_later_explicit_wired_make_target_could_be_discovered(tmp_path):
    (tmp_path/'Makefile').write_text('cf10-s01-runtime-launch-preflight:\n\t@echo \"CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND\"; exit 2\ncf10-s01-pilot-launch-preflight:\n\t@python -m scripts.coordination.control_plane.cf10_r052_owner_launch_guard_v0_1 --mode guarded-preflight\n')
    assert gate._make_has_guarded_pilot_route(tmp_path)


def test_live_source_missing_refuses(tmp_path):
    with pytest.raises(gate.LaunchGuardBlocked, match='SOURCE_MISSING_OR_SYMLINK'):
        gate._source_exact(tmp_path,HEAD)


@pytest.mark.parametrize('head',['', 'f'*39,'zz'*20,123,None])
def test_invalid_head_refuses(tmp_path,head):
    with pytest.raises(gate.LaunchGuardBlocked, match='SOURCE_HEAD_INVALID'):
        gate._source_exact(tmp_path,head)


def test_owner_guard_ordering_is_before_password_and_claim():
    src=inspect.getsource(owner.launch_once)
    a=src.index('pilot_guard.assert_pre_password(')
    b=src.index('console.authenticate_operator()')
    c=src.index('pilot_guard.assert_post_password_pre_claim(')
    d=src.index('_owner_claim(')
    assert a<b<c<d
    assert src.index('modern_route.assert_cutover_ready()')<a


def test_owner_live_source_pins_guard():
    src=inspect.getsource(owner._assert_live_source)
    assert 'cf10_r052_owner_launch_guard_v0_1.py' in src


def test_stage_all_true_after_password_uses_verified_snapshot(monkeypatch):
    obs={k:True for k in phase.REQUIRED_LAUNCH_OBSERVATIONS if k!='owner_pam_session_authenticated'}
    monkeypatch.setattr(gate,'_observe',lambda **kw: obs)
    from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as r046
    from scripts.coordination.control_plane import cf10_r051_root_preclaim_receipt_v0_1 as r051
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    monkeypatch.setattr(r046,'inspect',lambda **kw:{'status':'PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED','blockers':[],'checks':{'r047_source_lineage':'EXACT_RAW_BYTES_BOUND'}})
    monkeypatch.setattr(r051,'inspect',lambda **kw:{'preclaim_root_receipt_verified':True})
    monkeypatch.setattr(r051,'read_verified',lambda **kw:{'sealed':'real'})
    monkeypatch.setattr(once,'open_root_owned_state_dir',lambda:9)
    import os
    monkeypatch.setattr(os,'close',lambda fd: None)
    received=[]
    def evaluated(**kw):
        received.append(kw)
        return {'status':'PILOT_LAUNCH_CANDIDATE_NON_AUTHORIZING','blockers':[]}
    monkeypatch.setattr(phase,'launch_window',evaluated)
    gate.assert_post_password_pre_claim(root=gate.PROJECT,runtime_root=gate.RUNTIME,task=TASK,attempt=ATTEMPT,head=HEAD)
    assert len(received)==1
    assert received[0]['snapshot']=={'sealed':'real'}
    assert received[0]['observations']['owner_pam_session_authenticated'] is True


def test_stage_rejects_changed_preclaim_under_owner_lock(monkeypatch):
    obs={k:True for k in phase.REQUIRED_LAUNCH_OBSERVATIONS if k!='owner_pam_session_authenticated'}
    monkeypatch.setattr(gate,'_observe',lambda **kw: obs)
    from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as r046
    from scripts.coordination.control_plane import cf10_r051_root_preclaim_receipt_v0_1 as r051
    monkeypatch.setattr(r046,'inspect',lambda **kw:{'status':'PILOT_PROOF_CANDIDATE_VERIFIED_NOT_AUTHORIZED','blockers':[]})
    monkeypatch.setattr(r051,'inspect',lambda **kw:{'preclaim_root_receipt_verified':False})
    with pytest.raises(gate.LaunchGuardBlocked,match='POST_PASSWORD_PRECLAIM_CHANGED'):
        gate.assert_post_password_pre_claim(root=gate.PROJECT,runtime_root=gate.RUNTIME,task=TASK,attempt=ATTEMPT,head=HEAD)


def test_stage_rejects_finalizer_candidate_mismatch(monkeypatch):
    obs={k:True for k in phase.REQUIRED_LAUNCH_OBSERVATIONS if k!='owner_pam_session_authenticated'}
    monkeypatch.setattr(gate,'_observe',lambda **kw: obs)
    from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as r046
    from scripts.coordination.control_plane import cf10_r051_root_preclaim_receipt_v0_1 as r051
    from scripts.coordination.control_plane import cf10_s01_root_controlled_single_use_v0_2 as once
    import os
    monkeypatch.setattr(r046,'inspect',lambda **kw:{'status':'BLOCKED_PENDING_PILOT_RELEASE_EVIDENCE','blockers':['MISSING']})
    monkeypatch.setattr(r051,'inspect',lambda **kw:{'preclaim_root_receipt_verified':True})
    monkeypatch.setattr(r051,'read_verified',lambda **kw:{'sealed':'real'})
    monkeypatch.setattr(once,'open_root_owned_state_dir',lambda:9)
    monkeypatch.setattr(os,'close',lambda fd: None)
    monkeypatch.setattr(phase,'launch_window',lambda **kw:{'status':'BLOCKED_LAUNCH_WINDOW','blockers':['MISSING']})
    with pytest.raises(gate.LaunchGuardBlocked,match='CANONICAL_TWO_PHASE_LAUNCH_WINDOW_FAILED'):
        gate.assert_post_password_pre_claim(root=gate.PROJECT,runtime_root=gate.RUNTIME,task=TASK,attempt=ATTEMPT,head=HEAD)


def test_no_tmp_dependency_in_new_guard():
    src=inspect.getsource(gate)
    assert '/tmp/' not in src and "'tmp/'" not in src


def test_existing_systemd_gate_literal_not_opened():
    p=Path('/mnt/data/r051_workspace/scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py')
    # environment-local source fixture is not a production path
    if p.exists():
        assert 'LIVE_CUTOVER_ENABLED=False' in p.read_text()
