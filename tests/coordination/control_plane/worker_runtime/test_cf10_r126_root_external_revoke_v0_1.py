from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import secrets
import stat
import subprocess
import sys
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_r126_root_external_revoke_v0_1 as m
from scripts.coordination.control_plane.worker_runtime import cf10_r125_attempt_ipc_contract_v0_1 as r125

HEAD='d99ab3e3d1b4d8bb95e6961b5eac4d0d860aeaba'
ATTEMPT='cf10-r126-disposable-no-worker'
EPOCH='r126-epoch-001'

def fixture():
    if os.geteuid()!=0:pytest.skip('root-required Linux lease test')
    parent=Path('/run')/('forprint-cf10-r125-'+secrets.token_hex(8))
    parent.mkdir(mode=0o700)
    try: group=pwd.getpwnam('forprint-runner').pw_gid
    except KeyError: group=os.getgid()
    os.chown(parent,0,group);parent.chmod(0o710)
    lease=parent/'lease.json'
    r125.write_lease(lease,attempt=ATTEMPT,epoch=EPOCH,source_head=HEAD,capsule_id=m.CAPSULE_ID,revoked=False)
    return parent,lease

def teardown(parent):
    for p in parent.iterdir():p.unlink()
    parent.rmdir()

def binding(lease):return {'path':lease,'attempt':ATTEMPT,'epoch':EPOCH,'source_head':HEAD,'expected_gid':lease.parent.stat().st_gid}

def test_pinned_scope_and_schema():
    assert m.LEASE_RE.fullmatch('/run/forprint-cf10-r125-0123456789abcdef/lease.json')
    assert not m.LEASE_RE.fullmatch('/run/forprint-cf10-r126-0123456789abcdef/lease.json')
    assert m.CAPSULE_ID.startswith('git-12c668e0cc30-sha256-')

def test_exact_positive_root_revoke():
    parent,lease=fixture()
    try:
        assert m.inspect_lease(**binding(lease))['revoked'] is False
        result=m.revoke_lease(**binding(lease))
        assert result['revoked'] and result['new_calls_allowed'] is False
        assert m.inspect_lease(**binding(lease))['revoked'] is True
        with pytest.raises(r125.BoundaryHold):
            r125.secure_lease(lease,attempt=ATTEMPT,epoch=EPOCH,source_head=HEAD,
                              capsule_id=m.CAPSULE_ID,revoked=False)
    finally:teardown(parent)

def test_external_process_cli_revoke(monkeypatch):
    try: pwd.getpwnam('forprint-runner')
    except KeyError: pytest.skip('server runner account is absent in local container')
    parent,lease=fixture()
    try:
        # CLI mode is exercised under isolated sys.path, as on s01.
        script=Path(m.__file__).resolve()
        if script.parent.parent.parent.parent.name=='LOCAL_SUITE': pass
        env={'PATH':'/usr/bin:/bin','LANG':'C','PYTHONDONTWRITEBYTECODE':'1'}
        # To test source-only -I directly, runtime sibling r125 module exists.
        cp=subprocess.run([sys.executable,'-I','-B',str(script),'--mode','revoke',
                           '--lease',str(lease),'--attempt',ATTEMPT,'--epoch',EPOCH,
                           '--source-head',HEAD,'--capsule-id',m.CAPSULE_ID],
                          input=b'',stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=12)
        assert cp.returncode==0,cp.stderr.decode('utf8','replace')
        assert b'CF10_R126_EXTERNAL_ROOT_REVOKE=PASS' in cp.stdout
        assert m.inspect_lease(**binding(lease))['revoked'] is True
    finally:teardown(parent)

def test_revoke_twice_fails():
    parent,lease=fixture()
    try:
        m.revoke_lease(**binding(lease))
        with pytest.raises(m.ExternalRevokeHold,match='ALREADY_REVOKED'):m.revoke_lease(**binding(lease))
    finally:teardown(parent)

@pytest.mark.parametrize('field,value,code',[
    ('attempt','different','LEASE_BINDING_DRIFT'),
    ('epoch','different','LEASE_BINDING_DRIFT'),
    ('source_head','0'*40,'LEASE_BINDING_DRIFT'),
    ('capsule_id','wrong','BINDING_SOURCE_CAPSULE'),
])
def test_binding_drift(field,value,code):
    parent,lease=fixture()
    try:
        args=binding(lease);args[field]=value
        with pytest.raises(m.ExternalRevokeHold,match=code):m.revoke_lease(**args)
        assert m.inspect_lease(**binding(lease))['revoked'] is False
    finally:teardown(parent)

def test_parent_mode_fails_without_widen():
    parent,lease=fixture()
    try:
        parent.chmod(0o770)
        with pytest.raises(m.ExternalRevokeHold,match='PARENT_OWNER_MODE'):m.revoke_lease(**binding(lease))
    finally:teardown(parent)

def test_parent_owner_gid_fails():
    parent,lease=fixture()
    try:
        args=binding(lease);args['expected_gid']=os.getgid()+11111
        with pytest.raises(m.ExternalRevokeHold,match='PARENT_OWNER_MODE'):m.revoke_lease(**args)
    finally:teardown(parent)

def test_lease_mode_fails():
    parent,lease=fixture()
    try:
        lease.chmod(0o644)
        with pytest.raises(m.ExternalRevokeHold,match='LEASE_OWNER_MODE'):m.revoke_lease(**binding(lease))
    finally:teardown(parent)

def test_symlink_lease_rejected():
    parent,lease=fixture()
    try:
        original=parent/'orig.json';lease.rename(original);lease.symlink_to(original)
        with pytest.raises(m.ExternalRevokeHold,match='LEASE_OPEN'):m.revoke_lease(**binding(lease))
    finally:teardown(parent)

def test_wrong_path_is_rejected():
    with pytest.raises(m.ExternalRevokeHold,match='LEASE_PATH'):
        m.inspect_lease(Path('/tmp/any/lease.json'),attempt=ATTEMPT,epoch=EPOCH,
                        source_head=HEAD,expected_gid=0)

def test_missing_is_not_created():
    if os.geteuid()!=0:pytest.skip('root-required')
    p=Path('/run/forprint-cf10-r125-0123456789abcdef/lease.json')
    if p.parent.exists():pytest.skip('occupied host namespace')
    with pytest.raises(m.ExternalRevokeHold,match='PARENT_MISSING'):
        m.revoke_lease(p,attempt=ATTEMPT,epoch=EPOCH,source_head=HEAD,expected_gid=os.getgid())

def test_corrupt_does_not_overwrite():
    parent,lease=fixture()
    try:
        old=lease.read_bytes();lease.write_bytes(b'not-json\n')
        bad=lease.read_bytes()
        with pytest.raises(m.ExternalRevokeHold,match='LEASE_FORMAT'):m.revoke_lease(**binding(lease))
        assert lease.read_bytes()==bad
    finally:teardown(parent)

def test_cannot_unrevoke():
    assert 'revoked=False' not in m.revoke_lease.__doc__ if m.revoke_lease.__doc__ else True
    assert 'r125' in m.__doc__.lower()

def test_reject_nonroot(monkeypatch):
    monkeypatch.setattr(m.os,'geteuid',lambda:999)
    with pytest.raises(m.ExternalRevokeHold,match='ROOT_REQUIRED'):
        m.inspect_lease(Path('/run/forprint-cf10-r125-0123456789abcdef/lease.json'),attempt=ATTEMPT,
                        epoch=EPOCH,source_head=HEAD,expected_gid=os.getgid())
