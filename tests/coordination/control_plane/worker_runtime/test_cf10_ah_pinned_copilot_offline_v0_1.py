"""AH: offline pinned Copilot under a nonce-bound delegated Worker only."""
from __future__ import annotations
import copy
import hashlib
import os
import socket
import subprocess
import threading
from types import SimpleNamespace
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_ah_pinned_copilot_offline_v0_1 as ah
from scripts.coordination.control_plane.worker_runtime import cf10_ad_disposable_worker_child_v0_1 as child
from scripts.coordination.control_plane.worker_runtime import cf10_ae_delegated_kernel_rehearsal_v0_1 as ae
from scripts.coordination.control_plane.worker_runtime import cf10_ag_bound_dispatcher_worker_v0_1 as ag

UNIT='forprint-cf10-batchad-'+'a'*16+'.service'
NONCE='b'*64
H=lambda:hashlib.sha256(NONCE.encode()).hexdigest()

def probe():
    return {'schema':child.VERSION,'phase':'COPILOT_OFFLINE_VERSION_PROOF',
       'unit':UNIT,'nonce_sha256':H(),'exit_code':0,
       'stdout_sha256':hashlib.sha256(b'1.0.107\n').hexdigest(),
       'stderr_sha256':hashlib.sha256(b'').hexdigest(),
       'stdout_bytes':8,'stderr_bytes':0,'version_1_0_107_observed':True,
       'argv_mode':'PINNED_COPILOT_VERSION_ONLY',
       'credentials_passed':False,'provider_inference':False}

def fake_runner(args,**kw):
    assert args==['/usr/local/bin/forprint-copilot-1.0.107','--version']
    assert kw['cwd']=='/' and kw['timeout']<=18
    assert kw['stdin'] is subprocess.DEVNULL
    assert kw['check'] is False
    assert not any('TOKEN' in k or 'SECRET' in k or 'KEY' in k for k in kw['env'])
    assert kw['env']['HOME']=='/nonexistent'
    return SimpleNamespace(returncode=0,stdout=b'1.0.107\n',stderr=b'')

def test_exact_offline_child_argv_and_env():
    r=child.offline_version_probe(runner=fake_runner)
    assert r['version_1_0_107_observed'] and r['argv_mode']=='PINNED_COPILOT_VERSION_ONLY'
    assert r['credentials_passed'] is False and r['provider_inference'] is False

def test_root_proof_positive():
    r=ah.verify_probe(probe(),unit=UNIT,nonce=NONCE)
    assert r['offline_cli_verified'] and r['binary_sha256_expected']==ah.PIN
    assert r['independent_exec_inode_proven'] is False
    assert r['gates_open']==ah.GATES

@pytest.mark.parametrize('name,value',[
 ('schema','not-ours'),('phase','OTHER'),('unit','forprint-cf10-worker-'+'a'*24+'.service'),
 ('nonce_sha256','0'*64),('exit_code',True),('exit_code',1),
 ('stdout_sha256','f'),('stderr_sha256','!'),('stdout_bytes',-1),
 ('stderr_bytes',4097),('stdout_bytes',True),('version_1_0_107_observed',1),
 ('version_1_0_107_observed',False),('credentials_passed',True),
 ('credentials_passed',1),('provider_inference',True),('provider_inference',0),
 ('argv_mode','COPILOT_P_WITH_TOKEN'),('stdout_bytes',0)
])
def test_bad_proof_holds(name,value):
    row=probe();row[name]=value
    if name=='stdout_bytes':row['stderr_bytes']=0
    with pytest.raises(ah.OfflineHold):ah.verify_probe(row,unit=UNIT,nonce=NONCE)

@pytest.mark.parametrize('addition',('token','environment','authorization','unknown'))
def test_injected_fields_rejected(addition):
    row=probe();row[addition]='sensitive-shape'
    with pytest.raises(ah.OfflineHold):ah.verify_probe(row,unit=UNIT,nonce=NONCE)

@pytest.mark.parametrize('unit,nonce',[(UNIT,'x'*64),('evil.service',NONCE),(UNIT,1)])
def test_broken_independent_expectations_hold(unit,nonce):
    with pytest.raises(ah.OfflineHold):ah.verify_probe(probe(),unit=unit,nonce=nonce)

def test_version_failure_never_passes():
    with pytest.raises(ValueError):
        child.offline_version_probe(runner=lambda *a,**k:SimpleNamespace(returncode=1,stdout=b'1.0.107\n',stderr=b''))
    with pytest.raises(ValueError):
        child.offline_version_probe(runner=lambda *a,**k:SimpleNamespace(returncode=0,stdout=b'unknown\n',stderr=b''))
    with pytest.raises(ValueError):
        child.offline_version_probe(runner=lambda *a,**k:SimpleNamespace(returncode=0,stdout=b'a'*5000,stderr=b''))


def test_child_protocol_real_unix_socketpair_with_fake_pinned_cli(monkeypatch):
    """Real IPC, offline phase is mandatory before result and acknowledges via root."""
    client,root=socket.socketpair()
    monkeypatch.setattr(child.os,'getuid',lambda:996)
    monkeypatch.setattr(child.os,'getgid',lambda:992)
    monkeypatch.setattr(child.os,'geteuid',lambda:996)
    unpatched_probe=child.offline_version_probe
    monkeypatch.setattr(child,'offline_version_probe',lambda:unpatched_probe(runner=fake_runner))
    class Proxy:
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def settimeout(self,_):pass
        def connect(self,_):pass
        def recv(self,n):return client.recv(n)
        def sendall(self,b):return client.sendall(b)
    monkeypatch.setattr(child.socket,'socket',lambda *a,**kw:Proxy())
    statuses=[]
    def root_control():
        try:
            held=child.recv(root)
            assert held['phase']=='HELD'
            child.send(root,{'schema':child.VERSION,'phase':'RELEASE_ONE_DISPOSABLE',
                'unit':UNIT,'nonce':NONCE,'task_id':child.TASK,'offline_copilot_version':True})
            observed=child.recv(root)
            assert ah.verify_probe(observed,unit=UNIT,nonce=NONCE)['offline_cli_verified']
            child.send(root,{'schema':child.VERSION,'phase':'OFFLINE_PROOF_ACCEPTED',
                'unit':UNIT,'nonce_sha256':H()})
            final=child.recv(root)
            assert final['phase']=='RESULT'
            assert final['result_sha256']==child.worker_digest(child.TASK,NONCE)
            child.send(root,{'schema':child.VERSION,'phase':'RESULT_RECEIVED',
                'unit':UNIT,'result_sha256':final['result_sha256']})
            statuses.append('pass')
        except BaseException as exc:statuses.append(type(exc).__name__+':'+str(exc))
    t=threading.Thread(target=root_control,daemon=True)
    t.start()
    try:status=child.main(['child.py',UNIT,'/run/'+UNIT.removesuffix('.service')+'/control.sock',NONCE,child.TASK])
    finally:client.close();root.close();t.join(2)
    assert status==0 and statuses==['pass'],statuses


def test_legacy_child_release_still_has_exact_old_protocol(monkeypatch):
    assert child.worker_digest(child.TASK,NONCE)==hashlib.sha256(
      ('CF10_AD_SYNTHETIC_RESULT\0'+child.TASK+'\0'+NONCE).encode()).hexdigest()
    # There is no opt-in via user text, token environment or arbitrary command.
    assert 'COPILOT_GITHUB_TOKEN' not in child.offline_version_probe(runner=fake_runner)


def joined():
    return {'status':'PASS_CANONICAL_DISPATCHER_NONCE_BOUND_TO_PHYSICAL_TERMINAL',
      'real_kernel_leaf_1_to_0':True,'nonce_binding_verified_against_child_digest':True,
      'physical_unit':UNIT,'physical_invocation_id':'c'*32,'physical_result_sha256':'d'*64,
      'gates_open':ah.GATES,'canonical_worker_claim_consumed':False,
      'real_copilot_inference':False,'preview_identity_sha256':'e'*64,
      'nonce_commitment_sha256':H()}

def physical():
    return {'status':'PASS_DISPOSABLE_DELEGATED_WORKER_IPC_KERNEL_TERMINAL',
      'copilot_offline':ah.verify_probe(probe(),unit=UNIT,nonce=NONCE),
      'unit':UNIT,'kernel':{'transition':'1_TO_0','samples':['1','0'],'invocation_id':'c'*32},
      'result':{'synthetic_result_digest':'d'*64},
      'poststop':{'active':'inactive'},
      'runtime_cleanup':'PASS_DISPOSABLE_ONLY',
      'stage':'STOPPED_AND_TERMINAL_VERIFIED'}

def preview():return {'ack_from_independent_assistant':False,'production_owner_auth':False}

def test_full_join_verifier():
    row=ah.attest(preview=preview(),physical=physical(),joined=joined())
    assert row['status']=='PASS_CANONICAL_NONCE_BOUND_PINNED_COPILOT_OFFLINE_KERNEL_TERMINAL'
    assert row['offline_binary_version_observed'] and row['kernel_leaf_1_to_0_proven']
    assert row['provider_authenticated'] is False and row['production_dispatcher_claim_consumed'] is False

@pytest.mark.parametrize('where,key,value',[
 ('physical','status','FAKE'),('physical','runtime_cleanup','HOLD'),
 ('physical','stage','RESULT'),('joined','physical_unit','bad.service'),
 ('joined','real_kernel_leaf_1_to_0',False),('joined','real_kernel_leaf_1_to_0',1),
 ('joined','real_copilot_inference',True),('preview','ack_from_independent_assistant',True),
 ('preview','production_owner_auth',True),('joined','canonical_worker_claim_consumed',True),
])
def test_join_authority_and_identity_tamper(where,key,value):
    docs={'physical':physical(),'joined':joined(),'preview':preview()}
    docs[where][key]=value
    with pytest.raises(ah.OfflineHold):ah.attest(**docs)


def test_no_offline_field_means_no_offline_proof():
    x=physical();x.pop('copilot_offline')
    with pytest.raises(ah.OfflineHold):ah.attest(preview=preview(),physical=x,joined=joined())


def test_existing_ae_default_and_ag_runner_default_unchanged():
    from inspect import signature
    assert signature(ae.run_once).parameters['offline_copilot_probe'].default is False
    assert signature(ag.run_with_apis).parameters['offline_copilot_probe'].default is False
    assert ae.GATES==ah.GATES and ag.GATES==ah.GATES


def test_production_launch_switch_remains_in_source():
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend
    assert backend.LIVE_CUTOVER_ENABLED is False
