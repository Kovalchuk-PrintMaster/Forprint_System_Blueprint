"""r030 canonical systemd wiring safety tests. No production Worker/systemd."""
from __future__ import annotations
import ast
from pathlib import Path
import pytest
from scripts.coordination.control_plane import cf10_r030_canonical_systemd_route_v0_1 as route
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend
from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bound

ROOT=Path(__file__).resolve().parents[3]
CONTROL=ROOT/'scripts/coordination/control_plane'
GOV=CONTROL/'governed_worker_cycle.py'
OWN=CONTROL/'cf10_owner_pam_launch_v0_1.py'


def test_blocked_by_default():
    assert backend.LIVE_CUTOVER_ENABLED is False
    with pytest.raises(route.CanonicalCutoverBlocked,match='NOT_RELEASED'):
        route.assert_cutover_ready()


def test_run_once_fails_before_any_backend_effect(monkeypatch):
    def bad(**kwargs):raise AssertionError('backend must never be reached')
    monkeypatch.setattr(backend,'launch_after_owner_claim',bad)
    with pytest.raises(route.CanonicalCutoverBlocked,match='NOT_RELEASED'):
        route.run_once(root=backend.BLUEPRINT,runtime_root=backend.RUNTIME,
            task_prompt_id='test-task',attempt_id='cf10-test-a030',source_head='a'*40,
            baseline_sha256='b'*64,handoff_sha256='c'*64,launch_values={},
            started_callback=lambda _:None)


def values(attempt='cf10-r030case-a030'):
    a=backend.RUNTIME/'forprint_system_blueprint/worker-01'/attempt
    return dict(root=backend.BLUEPRINT,runtime_root=backend.RUNTIME,
      task_prompt_id='test-task-r030',attempt_id=attempt,
      source_head='a'*40,baseline_sha256='b'*64,handoff_sha256='c'*64,
      launch_values={'argv':['/usr/bin/python3','-c','pass'],
        'cwd':str(a/'workspace/repo'),'stdout_path':str(a/'logs/stdout.log'),
        'stderr_path':str(a/'logs/stderr.log'),'timeout_seconds':300})


def test_bound_valid():
    spec,plan=route.bind_contract(**values())
    assert spec.argv==('/usr/bin/python3','-c','pass')
    assert plan['identity']['unit']==bound.unit_for(spec.attempt_id,spec.source_head)
    assert plan['identity']['runner_account']=='forprint-runner'
    assert plan['flags']['authorizing'] is False

@pytest.mark.parametrize('key,bad',[
 ('source_head','0'),('handoff_sha256','a'),('baseline_sha256','a'),
 ('task_prompt_id','a'),('attempt_id','cf10-foobar-a049-noncanonical'),
 ('runtime_root',Path('/var/tmp/elsewhere')),('root',Path('/var/tmp/elsewhere')),
])
def test_invalid_bindings(key,bad):
    args=values();args[key]=bad
    with pytest.raises((bound.BoundaryBlocked,route.CanonicalCutoverBlocked)):
        route.bind_contract(**args)

@pytest.mark.parametrize('field,bad',[
 ('argv',['bash','-c','echo hello']),
 ('cwd','/tmp/hijack'),('stdout_path','/tmp/stdout.log'),
 ('stderr_path','/tmp/stderr.log'),('timeout_seconds',0),
])
def test_invalid_launch_values(field,bad):
    args=values();args['launch_values'][field]=bad
    with pytest.raises((bound.BoundaryBlocked,route.CanonicalCutoverBlocked)):
        route.bind_contract(**args)


def test_cgroup_missing_is_not_success(monkeypatch):
    monkeypatch.setattr(route.kernel,'_kernel_snapshot',lambda *a,**kw:{'cgroup_state':'REMOVED_NOT_PROOF','sampled_populated':None})
    assert route._cgroup_populated('forprint-cf10-worker-'+'a'*24+'.service')!='0'


def test_cgroup_populated_is_not_success(monkeypatch):
    monkeypatch.setattr(route.kernel,'_kernel_snapshot',lambda *a,**kw:{'cgroup_state':'POPULATED','sampled_populated':'1'})
    assert route._cgroup_populated('forprint-cf10-worker-'+'a'*24+'.service')!='0'


def test_cgroup_empty_is_sample_only(monkeypatch):
    monkeypatch.setattr(route.kernel,'_kernel_snapshot',lambda *a,**kw:{'cgroup_state':'EMPTY_AT_SAMPLE','sampled_populated':'0'})
    assert route._cgroup_populated('forprint-cf10-worker-'+'a'*24+'.service')=='0'


def test_systemctl_readback_command_scope():
    with pytest.raises(route.CanonicalCutoverBlocked,match='COMMAND_SCOPE'):
        route._trusted_runner(['/usr/bin/systemctl','stop','forprint-worker.service'])


def _calls(src):
    tree=ast.parse(src)
    return [(n.lineno,ast.unparse(n.func)) for n in ast.walk(tree) if isinstance(n,ast.Call)]


def test_canonical_route_no_legacy_fallback():
    s=GOV.read_text()
    calls=_calls(s)
    assert not any(f=='launcher.launch_process' for _,f in calls)
    assert len([f for _,f in calls if f=='modern_route.run_once'])==1
    assert 'process_result = modern_route.run_once(' in s


def test_owner_preclaim_gate_before_password_and_claim():
    s=OWN.read_text();calls=_calls(s)
    gate=[n for n,f in calls if f=='modern_route.assert_cutover_ready']
    claim=[n for n,f in calls if f=='_owner_claim']
    password=[n for n,f in calls if f=='console.authenticate_operator']
    assert len(gate)==1 and len(claim)==1 and len(password)==1
    assert gate[0]<password[0]<claim[0]


def test_started_to_terminal_order():
    s=CONTROL.joinpath('cf10_r030_canonical_systemd_route_v0_1.py').read_text()
    tree=ast.parse(s)
    fun=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='run_once')
    calls=[(x.lineno,ast.unparse(x.func)) for x in ast.walk(fun) if isinstance(x,ast.Call)]
    launch=[n for n,f in calls if f=='backend.launch_after_owner_claim']
    terminal=[n for n,f in calls if f=='terminal.wait_terminal']
    assert len(launch)==len(terminal)==1 and launch[0]<terminal[0]


def test_never_self_activates_backend():
    s=CONTROL.joinpath('cf10_r030_canonical_systemd_route_v0_1.py').read_text()
    assert 'LIVE_CUTOVER_ENABLED = True' not in s
    assert 'os.getenv' not in s and 'os.environ' not in s


def test_no_tmp_dependency():
    for p in (GOV,OWN,CONTROL/'cf10_r030_canonical_systemd_route_v0_1.py'):
        assert '/tmp/' not in p.read_text()


@pytest.mark.parametrize('mode,authority,allowed',[
    ('LEGACY_ROOT_INHERITED_POPEN',False,True),
    ('SEALED_CANONICAL_SYSTEMD',False,True),
    ('UNKNOWN_BACKEND',False,False),
    ('SEALED_CANONICAL_SYSTEMD',True,False),
])
def test_r027_regression_gate_remains_committed_and_non_authorizing(monkeypatch,mode,authority,allowed):
    import subprocess
    from scripts.validation import cf10_r027_launcher_modernization_check_v0_1 as check27
    from scripts.coordination.control_plane import cf10_r025_canonical_seam_v0_1 as seam
    assert ROOT == Path.cwd()
    observed=[]
    def read_committed(root,head):
        observed.append((root,head))
        return dict(launch_mode=mode,worker_cutover_authorized=authority,
                    production_launch_allowed=False)
    monkeypatch.setattr(seam,'inspect_committed',read_committed)
    # Only bypass the tmp-location check in this isolated fixture.
    monkeypatch.setattr(check27,'TARGETS',())
    monkeypatch.setattr(subprocess,'check_output',lambda *a,**k: '0123456789abcdef'*3)
    monkeypatch.setattr(subprocess,'run',lambda *a,**k: None)
    if allowed:
        check27.check(root=ROOT)
        assert observed and observed[0][0]==ROOT
    else:
        with pytest.raises(SystemExit,match='CF10_R027_BLOCKED_CANONICAL_SEAM_DRIFT'):
            check27.check(root=ROOT)


def test_r027_regression_still_uses_strict_git_provenance():
    p=ROOT/'scripts/validation/cf10_r027_launcher_modernization_check_v0_1.py'
    source=p.read_text()
    assert 'seam.inspect_committed(root,head)' in source
    assert 'LIVE_CUTOVER_ENABLED is not False' in source
    assert 'result[\'production_launch_allowed\'] is not False' in source
