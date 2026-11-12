"""AE: negative scope and physical protocol checks. No provider/network/systemd used locally."""
from __future__ import annotations
import copy
import hashlib
import os
from pathlib import Path
import socket
import threading
import time
from types import SimpleNamespace
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_ae_delegated_kernel_rehearsal_v0_1 as a
from scripts.coordination.control_plane.worker_runtime import cf10_ae_delegated_anchor_v0_1 as an
from scripts.coordination.control_plane.worker_runtime import cf10_ad_disposable_worker_child_v0_1 as child
from scripts.coordination.control_plane.worker_runtime import cf10_ad_disposable_worker_rehearsal_v0_1 as ad

UNIT='forprint-cf10-batchad-'+'a'*16+'.service'
INV='c'*32
NONCE='b'*64
ANCHOR_PID=4200
WORKER_PID=4201

def task():return {'task_id':child.TASK,'worker_claim_consumed':False,'production_dispatch_performed':False}
def held():return {'schema':child.VERSION,'phase':'HELD','unit':UNIT,'task_id':child.TASK,'nonce_sha256':hashlib.sha256(NONCE.encode()).hexdigest()}
def result():return {'schema':child.VERSION,'phase':'RESULT','unit':UNIT,'task_id':child.TASK,'result_kind':'SYNTHETIC_READONLY_NON_AI','result_sha256':child.worker_digest(child.TASK,NONCE)}
def proof():return {'observation':'PINNED_DELEGATED_LEAF_FD','transition':'1_TO_0','samples':['1','0'],'unit':UNIT,'invocation_id':INV,'parent_anchor_populated':'1','leaf_name':a.LEAF}
def retained():return {'retained_systemd_proven':True,'invocation_id':INV}
def stopped():return {'ActiveState':'inactive','MainPID':'0','Result':'success'}

def attest(**overrides):
    kw=dict(task=task(),anchor_pid=ANCHOR_PID,worker_pid=WORKER_PID,held=held(),result=result(),
            proof=proof(),retained=retained(),stop=stopped(),unit=UNIT,invocation_id=INV,nonce=NONCE)
    kw.update(overrides)
    return a.attest(**kw)

def test_attest_success_never_closes_gates():
    ret=attest()
    assert ret['status'].startswith('PASS_DISPOSABLE_')
    assert ret['gates_open']==a.GATES
    assert all(ret[key] is False for key in ('canonical_dispatcher_release','production_result_acceptance',
        'production_claim_consumed','production_ledger_written','provider_inference','provider_credentials','external_egress'))

@pytest.mark.parametrize('field,changed',[('transition','FAKE'),('samples',['1']),('samples',['0']),
   ('observation','SYSTEMD_ONLY'),('invocation_id','d'*32),('unit','bad'),
   ('parent_anchor_populated','0'),('leaf_name','wrong')])
def test_kernel_evidence_tamper_holds(field,changed):
    r=proof();r[field]=changed
    with pytest.raises(a.AEHold):attest(proof=r)

@pytest.mark.parametrize('field,value',[('retained_systemd_proven',False),('invocation_id','d'*32)])
def test_retained_tamper_holds(field,value):
    r=retained();r[field]=value
    with pytest.raises(a.AEHold):attest(retained=r)

@pytest.mark.parametrize('field,value',[('ActiveState','failed'),('MainPID','7'),('Result','exit-code')])
def test_stop_tamper_holds(field,value):
    r=stopped();r[field]=value
    with pytest.raises(a.AEHold):attest(stop=r)

@pytest.mark.parametrize('field,value',[('worker_claim_consumed',True),('production_dispatch_performed',True)])
def test_task_authority_holds(field,value):
    r=task();r[field]=value
    with pytest.raises(a.AEHold):attest(task=r)

@pytest.mark.parametrize('kw',[{'anchor_pid':WORKER_PID},{'worker_pid':1},
   {'unit':'forprint-cf10-worker-'+'f'*24+'.service'}, {'worker_pid':ANCHOR_PID}])
def test_identity_tamper_holds(kw):
    with pytest.raises(a.AEHold):attest(**kw)

@pytest.mark.parametrize('field,value',[('task_id','OTHER'),('phase','WRONG')])
def test_result_frame_holds(field,value):
    row=result();row[field]=value
    with pytest.raises(ad.RehearsalHold):attest(result=row)

def test_empty_or_duplicate_anchor_frame_denied():
    l,r=socket.socketpair()
    try:
        l.sendall(b'{"x":1,"x":2}\n')
        with pytest.raises(a.AEHold):a.recv(r)
        l.sendall(b'{"t":0}\n')
        assert a.recv(r)=={'t':0}
    finally:l.close();r.close()

def test_real_proc_stat_parent_of_own_process():
    assert a.proc_parent(os.getpid())==os.getppid()

@pytest.mark.parametrize('p',[-1,0,1,'2',None])
def test_invalid_proc_pid_holds(p):
    with pytest.raises(a.AEHold):a.proc_parent(p)

def test_delegate_wrong_unit_never_mutates():
    with pytest.raises(a.AEHold):a.delegate_child('production.service',WORKER_PID,ANCHOR_PID)

def test_anchor_payload_sanitizes_environment():
    env=an.sanitized_env()
    assert not set(env)&{'GH_TOKEN','GITHUB_TOKEN','COPILOT_GITHUB_TOKEN','OPENAI_API_KEY'}
    assert env['GIT_TERMINAL_PROMPT']=='0'

def test_anchor_frame_no_command_or_secrets():
    assert b'"event":"ANCHOR_HELD"' in an.encode({'event':'ANCHOR_HELD'})
    with pytest.raises(ValueError):an.encode({'x':'x'*2100})

def test_learned_ad_result_reused():
    assert ad.check_phase(held(),result(),unit=UNIT,nonce=NONCE)['result_verified_by_root']

def test_real_observe_leaf_fd_1_to_0(tmp_path):
    parent=tmp_path/'parent';parent.mkdir()
    (parent/'cgroup.events').write_bytes(b'populated 1\nfrozen 0\n')
    leaf=tmp_path/'leaf';leaf.write_bytes(b'populated 1\nfrozen 0\n')
    fd=os.open(leaf,os.O_RDONLY);group=os.open(parent,os.O_RDONLY|os.O_DIRECTORY)
    def flip():
        time.sleep(.05);leaf.write_bytes(b'populated 0\nfrozen 0\n')
    t=threading.Thread(target=flip,daemon=True);t.start()
    try:
        result=a.observe_zero(fd,group,UNIT,INV,timeout=1)
        assert result['samples']==['1','0'] and result['parent_anchor_populated']=='1'
    finally:os.close(fd);os.close(group);t.join()

@pytest.mark.parametrize('leaf,parent,expected',[(b'populated 0\n',b'populated 1\n','LEAF_NOT_INITIAL_1'),
    (b'populated 1\n',b'populated 1\n','PINNED_LEAF_ZERO_TIMEOUT'),
    (b'populated 1\n',b'populated 0\n','PINNED_LEAF_ZERO_TIMEOUT')])
def test_leaf_nonproven_holds(tmp_path,leaf,parent,expected):
    dir=tmp_path/'group';dir.mkdir();(dir/'cgroup.events').write_bytes(parent)
    path=tmp_path/'leaf';path.write_bytes(leaf)
    fd=os.open(path,os.O_RDONLY);parentfd=os.open(dir,os.O_RDONLY|os.O_DIRECTORY)
    try:
        with pytest.raises(a.AEHold,match=expected):a.observe_zero(fd,parentfd,UNIT,INV,timeout=.06)
    finally:os.close(fd);os.close(parentfd)

@pytest.mark.skipif(os.geteuid()!=0,reason='root-only disposable IPC order test')
def test_full_two_process_protocol_with_mock_systemd_and_cgroup(tmp_path,monkeypatch):
    """Real UNIX sockets and phase order; only systemd/kernel are simulated."""
    import tempfile
    tmp_path=Path(tempfile.mkdtemp(prefix='ae-',dir='/tmp'))
    monkeypatch.setattr(a,'RUN_ROOT',tmp_path)
    monkeypatch.setattr(a.secrets,'token_hex',lambda n:'a'*16 if n==8 else 'b'*64)
    monkeypatch.setattr(a,'_canonical',lambda:{'task_id':child.TASK,'worker_claim_consumed':False,
        'production_dispatch_performed':False,'gates_open':a.GATES})
    monkeypatch.setattr(a,'proc_cgroup',lambda *_:None)
    monkeypatch.setattr(a,'proc_parent',lambda _:ANCHOR_PID)
    monkeypatch.setattr(a,'_read_delegate',lambda *_:{'pid':ANCHOR_PID,'invocation_id':INV})
    monkeypatch.setattr(a,'peer',lambda sock,claimed_pid=None:claimed_pid if claimed_pid else ANCHOR_PID)
    monkeypatch.setattr(a,'observe_zero',lambda *_:{**proof()})
    state={'stopped':False,'anchor_sent_reaped':False,'worker_released':False,'failures':[]}
    original_rmdir=os.rmdir
    fakeparent=tmp_path/'fake-cgroup';fakeparent.mkdir()
    def fake_delegate(*_):
        leaf=fakeparent/a.LEAF;leaf.mkdir()
        return (os.open('/dev/null',os.O_RDONLY),os.open('/dev/null',os.O_RDONLY),
                os.open(fakeparent,os.O_RDONLY|os.O_DIRECTORY))
    monkeypatch.setattr(a,'delegate_child',fake_delegate)
    def fake_show(unit):
        sub='exited' if state['anchor_sent_reaped'] else 'running'
        row=dict(Id=UNIT,LoadState='loaded',ActiveState='inactive' if state['stopped'] else 'active',
            SubState='dead' if state['stopped'] else sub,
            MainPID='0' if state['stopped'] or sub=='exited' else str(ANCHOR_PID),
            ControlGroup='/system.slice/'+UNIT,InvocationID=INV,User='forprint-runner',
            Group='forprint-runner',KillMode='control-group',ExitType='cgroup',RemainAfterExit='yes',
            PrivateNetwork='yes',NoNewPrivileges='yes',Result='success',ExecMainStatus='0')
        return row
    monkeypatch.setattr(ad,'show',fake_show)
    def fake_call(argv,timeout=15):
        if argv[0]=='/usr/bin/systemctl' and 'stop' in argv:state['stopped']=True
        return SimpleNamespace(returncode=0,stdout=b'',stderr=b'')
    monkeypatch.setattr(ad,'call',fake_call)
    def anchor_thread():
        try:
            root=tmp_path/UNIT.removesuffix('.service')
            for _ in range(500):
                if (root/'anchor.sock').exists() and (root/'control.sock').exists():break
                time.sleep(.005)
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as sock:
                sock.connect(str(root/'anchor.sock'))
                an.send(sock,{'schema':an.SCHEMA,'event':'ANCHOR_HELD','unit':UNIT,
                    'nonce_sha256':hashlib.sha256(NONCE.encode()).hexdigest()})
                assert an.recv(sock)['event']=='SPAWN_ONE'
                an.send(sock,{'schema':an.SCHEMA,'event':'WORKER_SPAWNED','unit':UNIT,'pid':WORKER_PID})
                assert an.recv(sock)['event']=='FINALIZE_AFTER_PINNED_ZERO'
                an.send(sock,{'schema':an.SCHEMA,'event':'WORKER_REAPED',
                    'unit':UNIT,'pid':WORKER_PID,'exit_code':0})
                state['anchor_sent_reaped']=True
        except BaseException as exc:state['failures'].append('anchor:'+repr(exc))
    def worker_thread():
        try:
            root=tmp_path/UNIT.removesuffix('.service')
            for _ in range(500):
                if (root/'control.sock').exists():break
                time.sleep(.005)
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as sock:
                sock.connect(str(root/'control.sock'))
                child.send(sock,held())
                assert child.recv(sock)['phase']=='RELEASE_ONE_DISPOSABLE'
                child.send(sock,result())
                assert child.recv(sock)['phase']=='RESULT_RECEIVED'
                state['worker_released']=True
        except BaseException as exc:state['failures'].append('worker:'+repr(exc))
    t1=threading.Thread(target=anchor_thread,daemon=True);t2=threading.Thread(target=worker_thread,daemon=True)
    t1.start();t2.start()
    response=a.run_once()
    t1.join(5);t2.join(5)
    assert not state['failures'],state['failures']
    assert response['status']=='PASS_DISPOSABLE_DELEGATED_WORKER_IPC_KERNEL_TERMINAL',response
    assert response['stage']=='STOPPED_AND_TERMINAL_VERIFIED'
    assert state['worker_released'] and state['anchor_sent_reaped']
    assert response['runtime_cleanup']=='PASS_DISPOSABLE_ONLY'
    assert not (tmp_path/UNIT.removesuffix('.service')).exists()
    fakeparent.rmdir()
    tmp_path.rmdir()


@pytest.mark.skipif(os.geteuid()!=0,reason='root for delegated ownership metadata fixture')
def test_delegated_unit_parent_runner_owned_allowed(tmp_path):
    group=tmp_path/'unit';group.mkdir(mode=0o755)
    os.chown(group,996,992)
    fd=a._root_dir_inode(group)
    try:assert os.fstat(fd).st_uid==996
    finally:os.close(fd)

@pytest.mark.skipif(os.geteuid()!=0,reason='root for delegated ownership metadata fixture')
def test_untrusted_parent_owner_denied(tmp_path):
    group=tmp_path/'unit';group.mkdir(mode=0o755)
    os.chown(group,123,123)
    with pytest.raises(a.AEHold,match='CGROUP_INODE'):a._root_dir_inode(group)

@pytest.mark.skipif(os.geteuid()!=0,reason='root for delegated ownership metadata fixture')
def test_world_writable_delegated_parent_denied(tmp_path):
    group=tmp_path/'unit';group.mkdir(mode=0o755)
    os.chown(group,996,992);group.chmod(0o777)
    with pytest.raises(a.AEHold,match='CGROUP_INODE'):a._root_dir_inode(group)
