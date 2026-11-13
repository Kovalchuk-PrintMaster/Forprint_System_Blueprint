"""R141: genuine kernel peer/PIDFD tests plus fail-closed held-boundary fixtures."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import types
from unittest import mock

import pytest

from scripts.coordination.control_plane.worker_runtime import (
    cf10_r141_held_ipc_bridge_origin_v0_1 as api,
)

SOURCE=b'import socket,sys,time\ns=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)\ns.connect(sys.argv[1])\ntime.sleep(15)\n'

@contextmanager
def child_fixture():
    """One disposable root-owned Python bridge; no systemd or Worker/Copilot."""
    path=Path('/run/forprint-cf10-r125-'+secrets.token_hex(8))
    path.mkdir(mode=0o710)
    source=path/'bridge.py'
    source.write_bytes(SOURCE)
    source.chmod(0o440)
    address=str(path/'peer.sock')
    listener=socket.socket(socket.AF_UNIX)
    listener.bind(address); listener.listen(1);listener.settimeout(4)
    argv=('/usr/bin/python3','-I','-B',str(source),address)
    process=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    connection=None
    try:
        connection,_=listener.accept()
        yield (path,source,process,connection,argv)
    finally:
        if connection is not None:connection.close()
        listener.close()
        process.terminate()
        try:process.wait(timeout=2)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=2)
        shutil.rmtree(path)


def kwargs(source,process,socket_conn,argv):
    return dict(backend_socket=socket_conn,expected_pid=process.pid,
        unit='forprint-cf10-worker-'+'a'*24+'.service',
        expected_executable=Path('/usr/bin/python3'),source=source,
        source_sha256=hashlib.sha256(SOURCE).hexdigest(),argv=argv)


def root_identity():
    return mock.patch.multiple(api.binding,UID=os.getuid(),GID=os.getgid())


def test_source_check_sealed():
    assert api.source_check()==0


def test_kernel_peer_exact_pidfd_and_source_snapshot():
    with child_fixture() as (_,source,p,conn,argv),root_identity(),\
         mock.patch.object(api.session,'verify_peer',return_value={'kernel_peer_readback':True}):
        pin=api.pin_backend_bridge(**kwargs(source,p,conn,argv))
        try:
            record=api.verify_bridge_pin(pin,conn)
            assert record['backend_bridge_pid']==p.pid
            assert record['kernel_peer_verified'] is True
            assert record['pidfd_alive_verified'] is True
            assert record['canonical_mcp_child_independently_proven'] is False
            assert record['live_worker_authorized'] is False
        finally:pin.close()


def test_expected_different_pid_denied():
    with child_fixture() as (_,source,p,conn,argv),root_identity(),\
         mock.patch.object(api.session,'verify_peer',return_value={}):
        with pytest.raises(api.OriginHold,match='EXECUTABLE_IDENTITY|BRIDGE_PEER_NOT_SPAWNED_PID|BRIDGE_ARGV_CHANGED'):
            api.pin_backend_bridge(**{**kwargs(source,p,conn,argv),'expected_pid':os.getpid()})


def test_pin_wrong_sha_denied_before_attestation():
    with child_fixture() as (_,source,p,conn,argv),root_identity(),\
         mock.patch.object(api.session,'verify_peer',return_value={}):
        with pytest.raises(api.OriginHold,match='SOURCE_SHA'):
            api.pin_backend_bridge(**{**kwargs(source,p,conn,argv),'source_sha256':'0'*64})


def test_pin_wrong_argv_denied():
    with child_fixture() as (_,source,p,conn,argv),root_identity(),\
         mock.patch.object(api.session,'verify_peer',return_value={}):
        with pytest.raises(api.OriginHold,match='BRIDGE_ARGV_CHANGED'):
            api.pin_backend_bridge(**{**kwargs(source,p,conn,argv),'argv':argv+('surprise',)})


def test_pin_closes_fd_on_failed_peer():
    with child_fixture() as (_,source,p,conn,argv),root_identity(),\
         mock.patch.object(api.session,'verify_peer',side_effect=api.session.SessionHold('bad peer')):
        with pytest.raises(api.OriginHold,match='KERNEL_PEER_NOT_VERIFIED'):
            api.pin_backend_bridge(**kwargs(source,p,conn,argv))


def test_pin_source_symlink_denied():
    with child_fixture() as (directory,source,p,conn,argv),root_identity(),\
         mock.patch.object(api.session,'verify_peer',return_value={}):
        shadow=directory/'shadow.txt';source.rename(shadow);source.symlink_to(shadow)
        with pytest.raises(api.OriginHold,match='SOURCE_UNAVAILABLE'):
            api.pin_backend_bridge(**kwargs(source,p,conn,argv))


def test_pin_source_mutation_denied():
    with child_fixture() as (_,source,p,conn,argv),root_identity(),\
         mock.patch.object(api.session,'verify_peer',return_value={}):
        pin=api.pin_backend_bridge(**kwargs(source,p,conn,argv))
        try:
            source.chmod(0o640)
            source.write_bytes(SOURCE+b'# modified\n')
            with pytest.raises(api.OriginHold,match='SOURCE_SHA'):
                api.verify_bridge_pin(pin,conn)
        finally:pin.close()


def test_pin_pidfd_process_exit_denied():
    with child_fixture() as (_,source,p,conn,argv),root_identity(),\
         mock.patch.object(api.session,'verify_peer',return_value={}):
        pin=api.pin_backend_bridge(**kwargs(source,p,conn,argv))
        try:
            p.terminate();p.wait(timeout=2)
            with pytest.raises(api.OriginHold,match='PIN_CLOSED_OR_EXITED'):
                api.verify_bridge_pin(pin,conn)
        finally:pin.close()


def test_pin_closed_denied():
    with child_fixture() as (_,source,p,conn,argv),root_identity(),\
         mock.patch.object(api.session,'verify_peer',return_value={}):
        pin=api.pin_backend_bridge(**kwargs(source,p,conn,argv));pin.close()
        with pytest.raises(api.OriginHold,match='PIN_CLOSED_OR_EXITED'):
            api.verify_bridge_pin(pin,conn)


@pytest.mark.parametrize('invalid',[-1,0,1,'pid',True])
def test_invalid_pid_denied(invalid):
    with pytest.raises(api.OriginHold,match='PIN_PID'):
        api.pin_backend_bridge(backend_socket=None,expected_pid=invalid,
            unit='x',expected_executable=Path('/usr/bin/python3'),
            source=Path('/run/bridge.py'),source_sha256='a'*64,
            argv=('/usr/bin/python3','-I','-B','/run/bridge.py'))


@pytest.mark.parametrize('source',[
    '/tmp/source.py','/run/forprint-cf10-r125-0000000000000000/../../evil.py',
    '/run/forprint-cf10-r125-0000000000000000/source_capsule/data.txt',
])
def test_source_scope_denied(source):
    with pytest.raises(api.OriginHold,match='SOURCE_SCOPE_OR_HASH'):
        api._source_identity(Path(source),'a'*64)


def test_nonroot_denied_without_socket():
    with mock.patch.object(api.os,'geteuid',return_value=1001):
        with pytest.raises(api.OriginHold,match='ROOT_REQUIRED'):
            api.pin_backend_bridge(backend_socket=None,expected_pid=99,unit='x',
                expected_executable=Path('/usr/bin/python3'),
                source=Path('/run/foo'),source_sha256='a'*64,argv=('a','b','c'))


def fake_route():
    module=types.ModuleType('scripts.coordination.control_plane.cf10_r030_canonical_systemd_route_v0_1')
    module._trusted_runner=lambda command:None
    return module

def frozen_spec():
    return api.binding.BoundedInput(task_prompt_id='cf10-task',
        attempt_id='cf10-u180j-a900',source_head='a'*40,
        baseline_sha256='b'*64,handoff_sha256='c'*64,
        workspace='/tmp/fixture',runtime_root='/srv/software_development/forprint-worker-runtime',
        argv=('/usr/bin/false',),timeout_seconds=10)


def test_held_readback_fails_closed_on_untrusted_plan():
    with mock.patch.object(api.binding,'validate_plan',side_effect=api.binding.BoundaryBlocked('invalid')):
        with pytest.raises(api.OriginHold,match='FROZEN_HELD_LEASE_JOIN'):
            api.review_held_handoff(spec=frozen_spec(),
               plan={'identity':{'unit':'bad'}},invocation={},candidate={'epoch':'x'},
               lease=Path('/run/forprint-cf10-r125-'+'1'*16+'/lease.json'),
               witness=None)


def test_held_refuses_if_kernel_witness_absent_even_if_lease_verified():
    spec=frozen_spec()
    unit='forprint-cf10-worker-'+'a'*24+'.service'
    held={'ControlGroup':'/system.slice/'+unit}
    with mock.patch.object(api.binding,'validate_plan',return_value=None),\
         mock.patch.object(api.session,'verify_binding',return_value={'unit':unit}),\
         mock.patch.object(api.session,'check_lease',return_value=None),\
         mock.patch.object(api.systemd,'_verify_held',return_value=held),\
         mock.patch.object(api.kernel,'show',return_value={'InvocationID':'b'*32,'ControlGroup':'/system.slice/'+unit,'ActiveState':'active','MainPID':'777'}),\
         mock.patch.object(api,'verify_bridge_pin') as attest,\
         mock.patch.dict(sys.modules,{'scripts.coordination.control_plane.cf10_r030_canonical_systemd_route_v0_1':fake_route()}):
        with pytest.raises(api.OriginHold,match='HELD_WITNESS_IDENTITY'):
            api.review_held_handoff(spec=spec,plan={'identity':{'unit':unit}},
                invocation={},candidate={'epoch':'x'},lease=Path('/run/forprint-cf10-r125-'+'2'*16+'/lease.json'),
                witness=None)
        attest.assert_not_called()


def test_held_success_projection_never_grants_authority():
    spec=frozen_spec()
    unit='forprint-cf10-worker-'+'a'*24+'.service'
    fake=mock.Mock(unit=unit,closed=False,armed_populated='1',invocation_id='b'*32)
    with mock.patch.object(api.binding,'validate_plan',return_value=None),\
         mock.patch.object(api.session,'verify_binding',return_value={'unit':unit}),\
         mock.patch.object(api.session,'check_lease',return_value=None),\
         mock.patch.object(api.systemd,'_verify_held',return_value={'ControlGroup':'/system.slice/'+unit,'MainPID':'777'}),\
         mock.patch.object(api.kernel,'show',return_value={'Id':unit,'InvocationID':'b'*32,'ControlGroup':'/system.slice/'+unit,'ActiveState':'active','MainPID':'777','User':'forprint-runner','Group':'forprint-runner','KillMode':'control-group'}),\
         mock.patch.object(api.kernel,'read_fd',return_value='1'),\
         mock.patch.object(api.kernel,'KernelWitness',type(fake)),\
         mock.patch.object(api,'verify_bridge_pin',return_value={'backend_bridge_pid':1009}),\
         mock.patch.dict(sys.modules,{'scripts.coordination.control_plane.cf10_r030_canonical_systemd_route_v0_1':fake_route()}):
        record=api.review_held_handoff(spec=spec,plan={'identity':{'unit':unit}},
            invocation={},candidate={'epoch':'x'},lease=Path('/run/forprint-cf10-r125-'+'3'*16+'/lease.json'),
            witness=fake)
    assert record['backend_bridge_origin_pinned'] is False
    assert record['canonical_mcp_child_independently_proven'] is False
    assert record['live_worker_authorized'] is False
    assert record['terminal_ledger_written'] is False
    with mock.patch.object(api.kernel,'KernelWitness',type(fake)),\
         mock.patch.object(api.kernel,'show',return_value={'Id':unit,'InvocationID':'b'*32,'ControlGroup':'/system.slice/'+unit,'ActiveState':'active','User':'forprint-runner','Group':'forprint-runner','KillMode':'control-group'}),\
         mock.patch.object(api.kernel,'read_fd',return_value='1'),\
         mock.patch.object(api,'verify_bridge_pin',return_value={'backend_bridge_pid':1009}),\
         mock.patch.dict(sys.modules,{'scripts.coordination.control_plane.cf10_r030_canonical_systemd_route_v0_1':fake_route()}):
        post=api.review_post_release_bridge(held_review=record,spec=spec,plan={'identity':{'unit':unit}},witness=fake,bridge_pin=api.BridgePin(pid=1009,pidfd=-1,unit=unit,start_ticks='1',executable=Path('/usr/bin/python3'),executable_dev_ino=(1,2),source=Path('/run/x'),source_inode=(1,2,3,'a'*64),source_sha256='a'*64,argv=('python',)),backend_socket=None)
        assert post['backend_bridge_origin_pinned'] is True
        assert post['canonical_mcp_child_independently_proven'] is False


def test_cutover_source_gate_must_be_false():
    with mock.patch.object(api.systemd,'LIVE_CUTOVER_ENABLED',True):
        with pytest.raises(api.OriginHold,match='LIVE_CUTOVER_DRIFT'):
            api.source_check()
