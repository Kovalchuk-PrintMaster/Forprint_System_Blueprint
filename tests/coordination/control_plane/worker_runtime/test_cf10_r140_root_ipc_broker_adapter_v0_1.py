"""R140 fail-closed root IPC adapter unit tests. Never starts a Worker."""
from __future__ import annotations

import os
from pathlib import Path
import socket
import tempfile
import threading
from unittest import mock

import pytest

from scripts.coordination.control_plane.worker_runtime import (
    cf10_r140_root_ipc_broker_adapter_v0_1 as api,
)

IDENTITY = {'unit': 'forprint-cf10-worker-' + 'a'*24 + '.service',
            'attempt_id': 'cf10-u180j-a900', 'epoch': 'epoch-01',
            'source_head': 'a'*40, 'capsule_id': 'capsule'}


def kwargs(lease):
    return dict(invocation={}, candidate={}, attempt=IDENTITY['attempt_id'],
                epoch=IDENTITY['epoch'], head=IDENTITY['source_head'], lease=lease)


def test_source_check_sealed_and_no_authority():
    assert api.source_check() == 0


def test_nonroot_denied_before_binding():
    with mock.patch.object(api.os, 'geteuid', return_value=1000):
        with pytest.raises(api.BrokerHold, match='ROOT_REQUIRED'):
            api._identity(**kwargs(Path('/run/forprint-cf10-r125-' + 'b'*16 + '/lease.json')))


def test_broken_frozen_binding_denied():
    with mock.patch.object(api.os, 'geteuid', return_value=0), \
         mock.patch.object(api.session_lib, 'verify_binding', side_effect=api.session_lib.SessionHold('fail')):
        with pytest.raises(api.BrokerHold, match='FROZEN_LEASE_OR_INVOCATION'):
            api._identity(**kwargs(Path('/run/forprint-cf10-r125-' + 'b'*16 + '/lease.json')))


def test_lab_scope_not_production_runtime():
    for value in ('/run/forprint-cf10-worker/lease.json',
                  '/tmp/forprint-cf10-r125-1234567890abcdef/lease.json'):
        with pytest.raises(api.BrokerHold, match='LAB_LEASE_SCOPE'):
            api._directory(Path(value))


def test_root_owned_socket_stat_denies_regular_file_and_symlink():
    with tempfile.TemporaryDirectory() as base:
        p=Path(base)/'mcp.sock'
        p.write_text('bad')
        with pytest.raises(api.BrokerHold, match='SOCKET_OWNER_MODE'):
            api._check_socket(p, gid=os.getgid())
        p.unlink()
        p.symlink_to('/tmp/nothing')
        with pytest.raises(api.BrokerHold, match='SOCKET_OWNER_MODE'):
            api._check_socket(p, gid=os.getgid())


def test_socket_inode_change_denied():
    with tempfile.TemporaryDirectory() as base:
        path=Path(base)/'mcp.sock'
        server=socket.socket(socket.AF_UNIX)
        try:
            server.bind(str(path))
            st=path.lstat()
            with mock.patch.object(api, '_check_socket', wraps=api._check_socket):
                with pytest.raises(api.BrokerHold):
                    api._check_socket(path, gid=os.getgid(), device=st.st_dev, inode=st.st_ino+1)
        finally:server.close()


def test_existing_socket_never_removed_or_rebound():
    with tempfile.TemporaryDirectory() as base:
        lease=Path(base)/'lease.json'
        path=lease.with_name('mcp.sock')
        existing=socket.socket(socket.AF_UNIX)
        existing.bind(str(path))
        before=path.lstat().st_ino
        fd=os.open(base, os.O_RDONLY|os.O_DIRECTORY)
        try:
            with mock.patch.object(api, '_identity', return_value=dict(IDENTITY)), \
                 mock.patch.object(api, '_directory', return_value=(os.dup(fd), os.getgid())):
                with pytest.raises(api.BrokerHold, match='SOCKET_OCCUPIED'):
                    api.bind_lab_listener(**kwargs(lease))
            assert path.lstat().st_ino == before
        finally:os.close(fd);existing.close()


def test_new_broker_socket_is_single_and_exact_scope():
    # Test user is not root; mock privileged owner operations and inode readback
    # only. Kernel socket bind/listen itself is real.
    with tempfile.TemporaryDirectory() as base:
        lease=Path(base)/'lease.json'
        fd=os.open(base, os.O_RDONLY|os.O_DIRECTORY)
        try:
            with mock.patch.object(api, '_identity', return_value=dict(IDENTITY)), \
                 mock.patch.object(api, '_directory', return_value=(os.dup(fd), os.getgid())), \
                 mock.patch.object(api.os, 'chown'), mock.patch.object(api.os, 'chmod'), \
                 mock.patch.object(api, '_check_socket'), \
                 mock.patch.object(api.session_lib, 'check_lease'):
                listener, obj=api.bind_lab_listener(**kwargs(lease))
            try:
                assert listener.getsockname()==str(lease.with_name('mcp.sock'))
                assert obj==IDENTITY
                assert lease.with_name('mcp.sock').is_socket()
            finally:listener.close()
        finally:os.close(fd)


def _server(base):
    lease=Path(base)/'lease.json'
    server=socket.socket(socket.AF_UNIX)
    server.bind(str(lease.with_name('mcp.sock')))
    server.listen(1)
    return server,lease


def _mock_serve(identity, fd, result=None, session_error=None):
    result = result if result is not None else {
        'read_only_calls': 1, 'lease_exhausted': True,
        'worker_result_accepted': False, 'terminal_ledger_written': False,
        'live_worker_authorized': False}
    return [mock.patch.object(api, '_identity',return_value=dict(identity)),
            mock.patch.object(api, '_directory',side_effect=lambda p:(os.dup(fd), os.getgid())),
            mock.patch.object(api, '_check_socket'),
            mock.patch.object(api.session_lib,'verify_peer',return_value={}),
            mock.patch.object(api.session_lib,'check_lease'),
            mock.patch.object(api.session_lib,'handle_session',side_effect=session_error,return_value=result)]


def test_real_local_socket_accept_exactly_one_client_and_no_authority():
    with tempfile.TemporaryDirectory() as base:
        listener, lease = _server(base)
        fd=os.open(base,os.O_RDONLY|os.O_DIRECTORY)
        backend,remote=socket.socketpair()
        threads=[]
        try:
            patches=_mock_serve(IDENTITY,fd)
            for patch in patches:patch.start()
            def connect():
                c=socket.socket(socket.AF_UNIX)
                try:c.connect(str(lease.with_name('mcp.sock')))
                finally:c.close()
            thread=threading.Thread(target=connect);thread.start();threads.append(thread)
            report=api.serve_one(listener=listener,trusted_mcp=backend,**kwargs(lease))
            assert report['state']=='ONE_READ_ONLY_MCP_SESSION_REVIEW_ONLY'
            assert report['lease_revoked'] is True
            assert report['worker_result_accepted'] is False
            assert report['backend_lineage_independently_proven'] is False
            assert report['g1_g5_closed'] is False
        finally:
            for thread in threads:thread.join(timeout=2)
            for patch in reversed(patches):patch.stop()
            fd and os.close(fd)
            listener.close();backend.close();remote.close()


def test_inflight_hold_fences_lease_and_never_returns_result():
    with tempfile.TemporaryDirectory() as base:
        listener, lease = _server(base)
        fd=os.open(base,os.O_RDONLY|os.O_DIRECTORY)
        backend,remote=socket.socketpair()
        patches=_mock_serve(IDENTITY,fd,session_error=api.session_lib.SessionHold('revoked'))
        patches.append(mock.patch.object(api,'_revoke_on_hold'))
        try:
            for patch in patches:patch.start()
            client=socket.socket(socket.AF_UNIX)
            client.connect(str(lease.with_name('mcp.sock')))
            with pytest.raises(api.BrokerHold, match='SESSION_KERNEL_QUARANTINE_REQUIRED'):
                api.serve_one(listener=listener,trusted_mcp=backend,**kwargs(lease))
            api._revoke_on_hold.assert_called_once()
            client.close()
        finally:
            for patch in reversed(patches):patch.stop()
            os.close(fd);listener.close();backend.close();remote.close()


def test_post_handshake_false_authority_denied_and_revoked():
    with tempfile.TemporaryDirectory() as base:
        listener, lease = _server(base)
        fd=os.open(base,os.O_RDONLY|os.O_DIRECTORY)
        backend,remote=socket.socketpair()
        bad={'read_only_calls':1,'lease_exhausted':True,
             'worker_result_accepted':True,'terminal_ledger_written':False,'live_worker_authorized':False}
        patches=_mock_serve(IDENTITY,fd,result=bad)
        patches.append(mock.patch.object(api,'_revoke_on_hold'))
        try:
            for patch in patches:patch.start()
            client=socket.socket(socket.AF_UNIX)
            client.connect(str(lease.with_name('mcp.sock')))
            with pytest.raises(api.BrokerHold, match='SESSION_KERNEL_QUARANTINE_REQUIRED'):
                api.serve_one(listener=listener,trusted_mcp=backend,**kwargs(lease))
            api._revoke_on_hold.assert_called_once()
            client.close()
        finally:
            for patch in reversed(patches):patch.stop()
            os.close(fd);listener.close();backend.close();remote.close()


def test_backend_peer_must_be_kernel_verified_before_client_accept():
    with tempfile.TemporaryDirectory() as base:
        listener,lease=_server(base)
        fd=os.open(base,os.O_RDONLY|os.O_DIRECTORY)
        a,b=socket.socketpair()
        patches=_mock_serve(IDENTITY,fd)
        try:
            for patch in patches:patch.start()
            with mock.patch.object(api.session_lib, 'verify_peer',side_effect=api.session_lib.SessionHold('wrong uid')):
                with pytest.raises(api.BrokerHold,match='BACKEND_PEER_UNTRUSTED'):
                    api.serve_one(listener=listener,trusted_mcp=a,**kwargs(lease))
        finally:
            for patch in reversed(patches):patch.stop()
            os.close(fd);listener.close();a.close();b.close()


def test_failed_revocation_never_claims_kernel_zero():
    with mock.patch.object(api.lease_lib, 'inspect_lease',side_effect=api.lease_lib.ExternalRevokeHold('corrupt')):
        with pytest.raises(api.BrokerHold,match='REVOKE_UNPROVEN'):
            api._revoke_on_hold(lease=Path('/run/forprint-cf10-r125-'+'e'*16+'/lease.json'),identity=dict(IDENTITY))


def test_revoke_is_monotonic_and_reads_back():
    with mock.patch.object(api.lease_lib,'inspect_lease',side_effect=[{'revoked':False},{'revoked':True}]) as inspect, \
         mock.patch.object(api.lease_lib,'revoke_lease',return_value={'revoked':True}) as revoke:
        api._revoke_on_hold(lease=Path('/run/forprint-cf10-r125-'+'e'*16+'/lease.json'),identity=dict(IDENTITY))
    assert inspect.call_count == 2
    assert revoke.call_count == 1
