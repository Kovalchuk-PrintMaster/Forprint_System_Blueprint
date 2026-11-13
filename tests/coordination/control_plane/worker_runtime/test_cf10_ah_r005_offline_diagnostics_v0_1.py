"""AH r005: proof of metadata-only offline Copilot diagnostics (no provider)."""
from __future__ import annotations
import hashlib,socket,subprocess,threading
from types import SimpleNamespace
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_ad_disposable_worker_child_v0_1 as child
from scripts.coordination.control_plane.worker_runtime import cf10_ah_pinned_copilot_offline_v0_1 as ah
from scripts.coordination.control_plane.worker_runtime import cf10_ae_delegated_kernel_rehearsal_v0_1 as ae
UNIT='forprint-cf10-batchad-'+'a'*16+'.service'
NONCE='b'*64
H=lambda:hashlib.sha256(NONCE.encode()).hexdigest()

@pytest.mark.parametrize('rc,expected',[(1,'NONZERO_EXIT'),(-9,'NONZERO_EXIT')])
def test_nonzero_cli_is_bounded_failure(rc,expected):
    def fail(*a,**kw):return SimpleNamespace(returncode=rc,stdout=b'v'+b'1.0.107',stderr=b'sensitive data')
    with pytest.raises(child.OfflineProbeFailure) as ex:child.offline_version_probe(runner=fail)
    assert ex.value.record['failure_code']==expected
    assert ex.value.record['return_code']==rc
    assert 'sensitive' not in repr(ex.value.record)
    assert 'sensitive' not in str(ex.value)

@pytest.mark.parametrize('scenario,expected',[
    ('timeout','TIMEOUT'),('missing','EXEC_OSERROR'),('version','VERSION_NOT_OBSERVED'),
    ('too_large','OUTPUT_OVERSIZE'),('nul','OUTPUT_NUL'),('nonutf','OUTPUT_ENCODING'),
    ('bad_types','OUTPUT_TYPE')])
def test_cli_failures_classified_without_raw_output(scenario,expected):
    def fake(*a,**kw):
        if scenario=='timeout':raise subprocess.TimeoutExpired(a[0],18,output=b'password',stderr=b'secret')
        if scenario=='missing':raise OSError(13,'permission denied')
        if scenario=='version':return SimpleNamespace(returncode=0,stdout=b'unknown',stderr=b'secret')
        if scenario=='too_large':return SimpleNamespace(returncode=0,stdout=b'1.0.107'+b'a'*5000,stderr=b'')
        if scenario=='nul':return SimpleNamespace(returncode=0,stdout=b'1.0.107\0',stderr=b'')
        if scenario=='nonutf':return SimpleNamespace(returncode=0,stdout=b'1.0.107\xff',stderr=b'')
        return SimpleNamespace(returncode=0,stdout='1.0.107',stderr=b'')
    with pytest.raises(child.OfflineProbeFailure) as ex:child.offline_version_probe(runner=fake)
    assert ex.value.record['failure_code']==expected
    assert 'password' not in repr(ex.value.record)
    assert 'secret' not in repr(ex.value.record)

def failure(code='NONZERO_EXIT'):
    out={'schema':child.VERSION,'phase':'COPILOT_OFFLINE_VERSION_HOLD','unit':UNIT,'nonce_sha256':H(),
       'failure_code':code,'return_code':1 if code=='NONZERO_EXIT' else None,
       'os_errno':13 if code=='EXEC_OSERROR' else None,
       'stdout_bytes':0,'stderr_bytes':6,
       'stdout_sha256':hashlib.sha256(b'').hexdigest(),
       'stderr_sha256':hashlib.sha256(b'secret').hexdigest()}
    return out

def test_root_accepts_diagnostic_but_never_proof():
    row=ah.verify_failure(failure(),unit=UNIT,nonce=NONCE)
    assert row['offline_cli_verified'] is False
    assert row['failure_is_not_terminal_success'] is True
    assert row['failure_code']=='NONZERO_EXIT'
    assert 'secret' not in repr(row)
    with pytest.raises(ah.OfflineHold):ah.verify_probe(failure(),unit=UNIT,nonce=NONCE)

@pytest.mark.parametrize('key,value',[
    ('unit','other.service'),('nonce_sha256','0'*64),('failure_code','SUCCESS'),
    ('return_code',True),('return_code',65536),('os_errno',True),('stderr_bytes',True),
    ('stderr_bytes',65536),('failure_code',[]),('failure_code',{}),('stdout_sha256','x'),('phase','COPILOT_OFFLINE_VERSION_PROOF')])
def test_invalid_failure_cannot_pass(key,value):
    row=failure();row[key]=value
    with pytest.raises(ah.OfflineHold):ah.verify_failure(row,unit=UNIT,nonce=NONCE)

def test_added_fields_blocked():
    x=failure();x['secret_data']='do not accept'
    with pytest.raises(ah.OfflineHold):ah.verify_failure(x,unit=UNIT,nonce=NONCE)

def test_real_socket_failure_frame_exits_nonzero_and_never_emits_result(monkeypatch):
    original=child.offline_version_probe
    def fake():
        def run(*a,**kw):return SimpleNamespace(returncode=37,stdout=b'',stderr=b'secret!')
        return original(runner=run)
    monkeypatch.setattr(child,'offline_version_probe',fake)
    monkeypatch.setattr(child.os,'getuid',lambda:996)
    monkeypatch.setattr(child.os,'getgid',lambda:992)
    monkeypatch.setattr(child.os,'geteuid',lambda:996)
    client,root=socket.socketpair()
    class Proxy:
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def settimeout(self,_):pass
        def connect(self,_):pass
        def recv(self,n):return client.recv(n)
        def sendall(self,b):return client.sendall(b)
    monkeypatch.setattr(child.socket,'socket',lambda *a,**kw:Proxy())
    records=[]
    def listen():
        try:
            held=child.recv(root)
            assert held['phase']=='HELD'
            child.send(root,{'schema':child.VERSION,'phase':'RELEASE_ONE_DISPOSABLE','unit':UNIT,
                'nonce':NONCE,'task_id':child.TASK,'offline_copilot_version':True})
            fail=child.recv(root)
            records.append(ah.verify_failure(fail,unit=UNIT,nonce=NONCE))
        except BaseException as e:records.append(type(e).__name__)
    t=threading.Thread(target=listen,daemon=True);t.start()
    try:code=child.main(['child.py',UNIT,'/run/'+UNIT.removesuffix('.service')+'/control.sock',NONCE,child.TASK])
    finally:t.join(2);client.close();root.close()
    assert code==77 and len(records)==1 and isinstance(records[0],dict)
    assert records[0]['return_code']==37

def test_ae_root_rejects_offline_failure_before_any_success():
    from pathlib import Path
    text=Path(ae.__file__).read_text()
    assert "deny('OFFLINE_VERSION_CHILD_REPORTED_HOLD')" in text
    assert text.index("verify_failure(\n")<text.index("report['copilot_offline']=offline.verify_probe")
    assert "PINNED_COPILOT_OFFLINE_CHILD_REPORTED_HOLD" in text

def test_no_live_authorization():
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend
    assert backend.LIVE_CUTOVER_ENABLED is False
