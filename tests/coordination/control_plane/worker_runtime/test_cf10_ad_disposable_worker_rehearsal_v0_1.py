"""AD non-authorizing physical process rehearsal: strict negative tests."""
from __future__ import annotations
import copy
import hashlib
import os
import socket
from types import SimpleNamespace
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_ad_disposable_worker_rehearsal_v0_1 as a
from scripts.coordination.control_plane.worker_runtime import cf10_ad_disposable_worker_child_v0_1 as c

UNIT='forprint-cf10-batchad-'+'a'*16+'.service'
NONCE='b'*64
INV='c'*32

def task():return {'task_prompt_id':a.EXPECTED_TASK,'work_id':'u180j','module':'forprint_system_blueprint','candidate_only':True}
def cross():return {'canonical_task_resolved':True,'canonical_synthetic_11_step_lifecycle_passed':True,
       'owner_claim_consumed':False,'worker_started':False,'gates_open':a.OPEN,
       'report_sha256':'d'*64}
def held():return {'schema':c.VERSION,'phase':'HELD','unit':UNIT,'task_id':a.EXPECTED_TASK,
                    'nonce_sha256':hashlib.sha256(NONCE.encode()).hexdigest()}
def result():return {'schema':c.VERSION,'phase':'RESULT','unit':UNIT,'task_id':a.EXPECTED_TASK,
                    'result_kind':'SYNTHETIC_READONLY_NON_AI','result_sha256':c.worker_digest(a.EXPECTED_TASK,NONCE)}
def rows(**mod):
    r=dict(Id=UNIT,LoadState='loaded',ActiveState='active',SubState='running',
        MainPID='2468',ControlGroup='/system.slice/'+UNIT,InvocationID=INV,
        User='forprint-runner',Group='forprint-runner',KillMode='control-group',
        ExitType='cgroup',RemainAfterExit='yes',PrivateNetwork='yes',
        NoNewPrivileges='yes',Result='success',ExecMainStatus='0')
    r.update(mod);return r

def test_task_valid_no_authority():
    r=a.validate_task(task=task(),crossplane=cross(),backend_closed=True)
    assert r['worker_claim_consumed'] is False and r['production_dispatch_performed'] is False
    assert r['gates_open']==a.OPEN

@pytest.mark.parametrize('section,key,val',[
    ('task','task_prompt_id','other'),('task','work_id','u180k'),('task','module','other'),
    ('task','candidate_only',False),('cross','canonical_task_resolved',False),
    ('cross','canonical_synthetic_11_step_lifecycle_passed',False),
    ('cross','owner_claim_consumed',True),('cross','worker_started',True),
    ('cross','gates_open',[]),
])
def test_canonical_binding_drifts_fail(section,key,val):
    t=task();x=cross(); (t if section=='task' else x)[key]=val
    with pytest.raises(a.RehearsalHold):a.validate_task(task=t,crossplane=x,backend_closed=True)

def test_prod_gate_fails():
    with pytest.raises(a.RehearsalHold):a.validate_task(task=task(),crossplane=cross(),backend_closed=False)

def test_synthetic_result_verified():
    check=a.check_phase(held(),result(),unit=UNIT,nonce=NONCE)
    assert check['result_verified_by_root'] and check['model_inference_executed'] is False
    assert check['worker_result_accepted'] is False

@pytest.mark.parametrize('section,key,value',[
    ('held','phase','RESULT'),('held','task_id','other'),('held','nonce_sha256','0'*64),
    ('result','result_sha256','0'*64),('result','result_kind','LIVE_MODEL'),
    ('result','task_id','other'),('result','phase','HELD'),
])
def test_tamper_holds(section,key,value):
    h=held();r=result();(h if section=='held' else r)[key]=value
    with pytest.raises(a.RehearsalHold):a.check_phase(h,r,unit=UNIT,nonce=NONCE)

def test_unknown_message_field_holds():
    h=held();h['provider_token']='secret'
    with pytest.raises(a.RehearsalHold):a.check_phase(h,result(),unit=UNIT,nonce=NONCE)

def test_wrong_unit_holds():
    with pytest.raises(a.RehearsalHold):a.check_phase(held(),result(),unit='forprint-cf10-worker-'+'a'*24+'.service',nonce=NONCE)

def test_held_systemd_profile():
    assert a.validate_held(rows(),UNIT,2468)['invocation_id']==INV

@pytest.mark.parametrize('k,val',[('MainPID','0'),('ActiveState','inactive'),('ExitType','main'),
    ('RemainAfterExit','no'),('PrivateNetwork','no'),('NoNewPrivileges','no'),
    ('KillMode','process'),('ControlGroup','/wrong'),('User','root'),('InvocationID','bad')])
def test_unsafe_systemd_profile_holds(k,val):
    with pytest.raises(a.RehearsalHold):a.validate_held(rows(**{k:val}),UNIT,2468)

def test_retained_terminal_exact():
    assert a.validate_terminal(rows(SubState='exited',MainPID='0'),UNIT,INV)['retained_systemd_proven']

@pytest.mark.parametrize('k,val',[('ActiveState','failed'),('SubState','running'),('ExecMainStatus','1'),
    ('Result','exit-code'),('InvocationID','0'*32),('ExitType','main'),('MainPID','2')])
def test_bad_terminal_holds(k,val):
    d=rows(SubState='exited',MainPID='0');d[k]=val
    with pytest.raises(a.RehearsalHold):a.validate_terminal(d,UNIT,INV)

def test_finish_proven_disposable_only():
    proof={'kernel_observation':'PINNED_FD_READ','samples':['1','0']}
    result=a.check_finish(proof=proof,retained={'retained_systemd_proven':True},
        final={'ActiveState':'inactive','MainPID':'0'},unit=UNIT)
    assert result['status']=='PASS_DISPOSABLE_SYSTEMD_RESULT_AND_KERNEL_TERMINAL'
    assert result['production_launcher_called'] is False and result['gates_open']==a.OPEN

@pytest.mark.parametrize('proof',[
    {'kernel_observation':'PINNED_FD_READ','samples':['1']},
    {'kernel_observation':'SYSTEMD_ONLY','samples':['1','0']},
    {'kernel_observation':'PINNED_FD_READ','samples':['0']},
])
def test_no_fabricated_kernel(proof):
    with pytest.raises(a.RehearsalHold):a.check_finish(proof=proof,retained={'retained_systemd_proven':True},
        final={'ActiveState':'inactive','MainPID':'0'},unit=UNIT)

def test_no_synthetic_auth_environment():
    os.environ['GH_TOKEN']='THIS_IS_NOT_TO_BE_READ'
    try:
        env=a.scrubbed_env()
        assert 'GH_TOKEN' not in env and 'GITHUB_TOKEN' not in env
        assert env['GIT_TERMINAL_PROMPT']=='0'
    finally:os.environ.pop('GH_TOKEN',None)

def test_frame_reject_duplicate_and_receive_pair():
    left,right=socket.socketpair()
    try:
        c.send(left,held())
        assert c.recv(right)==held()
        left.sendall(b'{"x":1,"x":2}\n')
        with pytest.raises(ValueError,match='duplicate'):c.recv(right)
    finally:left.close();right.close()

def test_digest_is_bound_to_task_and_nonce():
    assert c.worker_digest(a.EXPECTED_TASK,NONCE)!=c.worker_digest(a.EXPECTED_TASK,'0'*64)
    assert c.worker_digest(a.EXPECTED_TASK,NONCE)!=c.worker_digest('other',NONCE)

def test_loopback_is_not_a_provider_api():
    assert a.EXPECTED_TASK.startswith('cf10-')
    assert a.UNIT_RE.fullmatch(UNIT)
    assert a.UNIT_RE.fullmatch('forprint-cf10-worker-'+'a'*24+'.service') is None

def test_source_review_is_closed():
    s=a.source_check()
    assert s['production_dispatch'] is False and s['claim_consumed'] is False

@pytest.mark.skipif(os.geteuid()!=0,reason='root-only disposable IPC test')
def test_full_ipc_controller_order_with_fake_systemd_only(tmp_path,monkeypatch):
    """Actual UNIX socket message exchange; systemd and cgroup only are simulated."""
    import threading
    import time
    import tempfile
    from pathlib import Path
    testroot=Path(tempfile.mkdtemp(prefix='cf10-ad-',dir='/tmp'))
    monkeypatch.setattr(a,'RUN_ROOT',testroot)
    monkeypatch.setattr(a,'inspect_canonical',lambda:{'canonical_task_resolved':True})
    monkeypatch.setattr(a.secrets,'token_hex',lambda n:'a'*16 if n==8 else 'b'*64)
    monkeypatch.setattr(a,'peer',lambda _:2468)
    monkeypatch.setattr(a,'proc_cgroup',lambda *_:None)
    monkeypatch.setattr(a,'pin_cgroup',lambda *_:(os.open('/dev/null',os.O_RDONLY),os.open('/dev/null',os.O_RDONLY)))
    monkeypatch.setattr(a,'wait_zero',lambda *_:{'kernel_observation':'PINNED_FD_READ',
        'samples':['1','0'],'unit':UNIT,'invocation_id':INV})
    control={'stop':False,'show_count':0}
    def fake_call(argv,timeout=15):
        if argv[0]=='/usr/bin/systemctl' and 'stop' in argv:control['stop']=True
        return SimpleNamespace(returncode=0,stdout=b'',stderr=b'')
    monkeypatch.setattr(a,'call',fake_call)
    def fake_show(unit):
        if control['stop']:return rows(ActiveState='inactive',SubState='dead',MainPID='0')
        control['show_count']+=1
        if control['show_count']>1:return rows(SubState='exited',MainPID='0')
        return rows()
    monkeypatch.setattr(a,'show',fake_show)
    errors=[]
    def fake_worker():
        try:
            path=testroot/UNIT.removesuffix('.service')/'control.sock'
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as sock:
                for _ in range(300):
                    try:sock.connect(str(path));break
                    except (FileNotFoundError,ConnectionRefusedError):time.sleep(.005)
                else:raise AssertionError('no socket')
                c.send(sock,held())
                release=c.recv(sock)
                assert release['phase']=='RELEASE_ONE_DISPOSABLE' and release['nonce']==NONCE
                c.send(sock,result())
                ack=c.recv(sock)
                assert ack['phase']=='RESULT_RECEIVED'
                control['result']=True
        except BaseException as exc:errors.append(repr(exc))
    t=threading.Thread(target=fake_worker,daemon=True)
    t.start()
    report=a.run_once()
    t.join(3)
    assert not errors,errors
    assert report['status']=='PASS_DISPOSABLE_SYSTEMD_RESULT_AND_KERNEL_TERMINAL',report
    assert report['stage']=='STOPPED_VERIFIED'
    assert report['result']['result_verified_by_root'] is True
    assert report['runtime_cleanup']=='PASS_DISPOSABLE_ONLY'
    assert not (testroot/UNIT.removesuffix('.service')).exists()
    testroot.rmdir()
