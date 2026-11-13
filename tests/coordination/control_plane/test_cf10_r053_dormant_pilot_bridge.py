"""r053 scoped tests; no live Worker, no root receipt, no PAM."""
from pathlib import Path
import ast
import json
import inspect
import os
import subprocess
import pytest
from scripts.coordination.control_plane import cf10_r053_dormant_pilot_bridge_v0_1 as bridge
from scripts.coordination.control_plane import cf10_r052_owner_launch_guard_v0_1 as r052
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend

ROOT = Path(__file__).resolve().parents[3]
MAKE = ROOT/'Makefile'


def test_readonly_dormant_requirements():
    d = bridge.requirements()
    assert d['production_cutover'] is False
    assert d['launch_allowed'] is False
    assert d['root_pilot_proof_issued'] is False
    assert d['preclaim_receipt_issued'] is False
    assert d['legacy_release_quarantine_unchanged'] is True


def test_requirements_cli(capsys):
    assert bridge.main(['--mode','requirements']) == 0
    assert 'BACKEND_DORMANT' in capsys.readouterr().out


@pytest.mark.parametrize('spec,guard',[
    (None, None), (object(), object()), ({'attempt_id':'cf10-u180j-a888'},True),
    ({'source_head':'a'*40}, {'proofs':'all-pass'}),
])
def test_backend_refuses_all_candidate_input(spec,guard):
    with pytest.raises(bridge.PilotDormantBlocked,match='DORMANT_BACKEND_NOT_RELEASED'):
        bridge.refuse_backend_launch(spec=spec,guard_module=guard)


def test_backend_gate_refuses_even_if_dormant_raises(monkeypatch):
    assert backend.LIVE_CUTOVER_ENABLED is False
    monkeypatch.setattr(bridge,'refuse_backend_launch',lambda **kw: (_ for _ in ()).throw(bridge.PilotDormantBlocked('NO')))
    with pytest.raises(backend.SystemdLaunchBlocked, match='CUTOVER_NOT_AUTHORIZED'):
        backend.launch_after_owner_claim(spec=object(),plan={},started_callback=lambda _:None)


def test_backend_gate_refuses_if_stub_returns(monkeypatch):
    monkeypatch.setattr(bridge,'refuse_backend_launch',lambda **kw: None)
    monkeypatch.setattr(backend,'_core',lambda **kw: pytest.fail('_core would run'))
    with pytest.raises(backend.SystemdLaunchBlocked, match='CUTOVER_NOT_AUTHORIZED'):
        backend.launch_after_owner_claim(spec=object(),plan={},started_callback=lambda _:None)


def test_legacy_make_and_launch_targets_untouched():
    s=MAKE.read_text()
    assert ('cf10-s01-runtime-launch-preflight:\n'
            '\t@echo "CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND"; exit 2') in s
    for t in ('governed-worker-cycle-launch','governed-worker-cycle-advance',
              'governed-worker-cycle-reconcile-result-return'):
        assert f'{t}: cf10-s01-runtime-launch-preflight' in s
    assert s.count('cf10-s01-pilot-launch-preflight:\n') == 1
    assert r052._make_has_guarded_pilot_route(ROOT) is True
    assert r052._backend_has_guarded_pilot_route(ROOT) is True


def test_backend_flag_literal_and_no_popen():
    source=inspect.getsource(backend)
    assert 'LIVE_CUTOVER_ENABLED=False' in source
    assert '# CF10_SOURCE_BOUND_PILOT_BACKEND_BRANCH_VERIFIED' in source
    fn=ast.parse(inspect.getsource(backend.launch_after_owner_claim))
    calls=[ast.unparse(n.func) for n in sorted(ast.walk(fn), key=lambda n: getattr(n,'lineno',10**9)) if isinstance(n,ast.Call)]
    assert 'dormant.refuse_backend_launch' in calls
    assert '_core' in calls
    assert calls.index('dormant.refuse_backend_launch') < calls.index('_core')
    assert 'subprocess.Popen' not in calls


def test_preflight_env_cannot_grant_authority(monkeypatch,capsys):
    monkeypatch.setenv('CF10_TASK',r052.TASK)
    monkeypatch.setenv('CF10_ATTEMPT','cf10-u180j-a999')
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    monkeypatch.setattr(console,'source_guard',lambda root:'a'*40)
    monkeypatch.setattr(r052,'assert_pre_password',lambda **kw:None)
    # all-true mock only proves the CLI exit/status is nonauthorizing
    assert r052.main(['--mode','guarded-preflight']) == 0
    out=json.loads(capsys.readouterr().out)
    assert out['status']=='EVIDENCE_CANDIDATE_NON_AUTHORIZING'
    assert out['launch_allowed'] is False
    assert out['operator_claim_consumed'] is False


@pytest.mark.parametrize('bad_task,bad_attempt',[
    ('', 'cf10-u180j-a123'), (r052.TASK,''), ('???','cf10-u180j-a123'),
])
def test_preflight_invalid_ids_block(monkeypatch,capsys,bad_task,bad_attempt):
    monkeypatch.setenv('CF10_TASK',bad_task)
    monkeypatch.setenv('CF10_ATTEMPT',bad_attempt)
    assert r052.main(['--mode','guarded-preflight']) == 2
    out=json.loads(capsys.readouterr().out)
    assert out['launch_allowed'] is False
    assert out['status']=='BLOCKED_READ_ONLY_PILOT_PREFLIGHT'


def test_preflight_blocks_on_proof_refusal(monkeypatch,capsys):
    from scripts.coordination.control_plane import cf10_owner_operator_console_v0_1 as console
    monkeypatch.setenv('CF10_TASK',r052.TASK)
    monkeypatch.setenv('CF10_ATTEMPT','cf10-u180j-a999')
    monkeypatch.setattr(console,'source_guard',lambda root:'a'*40)
    def fail(**kw):raise r052.LaunchGuardBlocked('NO_PROOFS')
    monkeypatch.setattr(r052,'assert_pre_password',fail)
    assert r052.main(['--mode','guarded-preflight']) == 2
    assert json.loads(capsys.readouterr().out)['status']=='BLOCKED_READ_ONLY_PILOT_PREFLIGHT'


def test_preflight_does_not_call_pam_claim_or_worker():
    source=inspect.getsource(r052.main)
    assert 'authenticate_operator' not in source
    assert '_owner_claim' not in source
    assert 'launch_once' not in source
    assert 'launch_cycle' not in source


def test_make_target_readonly_deny_in_current_environment():
    env={**os.environ,'CF10_TASK':r052.TASK,'CF10_ATTEMPT':'cf10-u180j-a999'}
    cp=subprocess.run(['make','-s','PYTHON=python3','cf10-s01-pilot-launch-preflight'],cwd=ROOT,
                      capture_output=True,text=True,timeout=40,env=env)
    assert cp.returncode != 0
    assert 'BLOCKED_READ_ONLY_PILOT_PREFLIGHT' in cp.stdout


def test_no_production_operations_in_dormant_module():
    src=inspect.getsource(bridge)
    for token in ('subprocess.run(', 'subprocess.Popen(', 'os.open(',
                  'launch_cycle(', 'systemd-run', 'claim('):
        assert token not in src
