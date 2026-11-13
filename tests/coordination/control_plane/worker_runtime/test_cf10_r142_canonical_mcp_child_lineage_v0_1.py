"""R142 source-only: real Linux PIDFD/proc/stdio provenance, no Worker or systemd."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import secrets
import shutil
import signal
import socket
import subprocess
from unittest import mock

import pytest

from scripts.coordination.control_plane.worker_runtime import (
    cf10_r142_canonical_mcp_child_lineage_v0_1 as api,
)

BRIDGE=b'''import signal,socket,subprocess,sys,time
args=[sys.argv[2], '-I', '-B', sys.argv[3], '--attempt-id','cf10-r142lab', '--task-id','cf10-r142-disposable', '--work-front-id','cf10', '--decision-id','d'*64, '--workspace-repo',sys.argv[4], '--evidence-root',sys.argv[5]]
child=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,close_fds=True)
def end(signum,frame):
 child.terminate()
 try:child.wait(timeout=3)
 except subprocess.TimeoutExpired:child.kill();child.wait()
 sys.exit(0)
signal.signal(signal.SIGTERM,end)
s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
s.connect(sys.argv[1])
time.sleep(30)
'''
CHILD=b'import time\ntime.sleep(30)\n'
UNIT='forprint-cf10-worker-'+'a'*24+'.service'
PYTHON=Path('/usr/bin/python3')


@contextmanager
def fixture():
    """Kernel processes/pipes are genuine; systemd cgroup identity is MOCKED."""
    directory=Path('/run/forprint-cf10-r125-'+secrets.token_hex(8))
    directory.mkdir(mode=0o710)
    bridge_src=directory/'bridge.py';bridge_src.write_bytes(BRIDGE);bridge_src.chmod(0o440)
    source=directory/api.REL_MCP
    source.parent.mkdir(mode=0o755,parents=True)
    # Most intermediate root-owned dirs: 0755, no untrusted writer.
    source.write_bytes(CHILD);source.chmod(0o440)
    workspace=directory/'workspace/repo';workspace.mkdir(parents=True)
    evidence=directory/'evidence';evidence.mkdir()
    address=str(directory/'control.sock')
    listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    listener.bind(address);listener.listen(1);listener.settimeout(5)
    parent_argv=(str(PYTHON),'-I','-B',str(bridge_src),address,str(PYTHON),str(source),str(workspace),str(evidence))
    parent=subprocess.Popen(parent_argv,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    conn=None; pin=None; childpin=None
    try:
        conn,_=listener.accept()
        with mock.patch.multiple(api.binding,UID=os.getuid(),GID=os.getgid()),\
             mock.patch.object(api.session,'verify_peer',return_value={}),\
             mock.patch.object(api.session,'_proc_cgroup',return_value='0::/system.slice/'+UNIT):
            pin=api.bridge_lib.pin_backend_bridge(
                backend_socket=conn,expected_pid=parent.pid,unit=UNIT,
                expected_executable=PYTHON,source=bridge_src,
                source_sha256=hashlib.sha256(BRIDGE).hexdigest(),argv=parent_argv)
            child_argv=(str(PYTHON),'-I','-B',str(source),
                '--attempt-id','cf10-r142lab','--task-id','cf10-r142-disposable',
                '--work-front-id','cf10','--decision-id','d'*64,
                '--workspace-repo',str(workspace),'--evidence-root',str(evidence))
            yield (directory,source,parent,conn,pin,child_argv)
    finally:
        if childpin is not None:childpin.close()
        if pin is not None:pin.close()
        if conn is not None:conn.close()
        listener.close()
        if parent.poll() is None:
            parent.terminate()
        try:parent.wait(timeout=5)
        except subprocess.TimeoutExpired:parent.kill();parent.wait(timeout=3)
        shutil.rmtree(directory)


def pin(ctx,**overrides):
    directory,source,parent,conn,bridge_pin,argv=ctx
    opts=dict(bridge_pin=bridge_pin,backend_socket=conn,executable=PYTHON,
        source=source,source_sha256=hashlib.sha256(CHILD).hexdigest(),frozen_argv=argv)
    opts.update(overrides)
    return api.pin_mcp_child(**opts)


def test_source_check_closed():
    assert api.source_check()==0


def test_real_pidfd_parent_process_stdio_two_pipes():
    with fixture() as ctx:
        child=pin(ctx)
        try:
            record=api.verify_mcp_child(child_pin=child,bridge_pin=ctx[4],backend_socket=ctx[3])
            assert record['mcp_pid']==child.pid
            assert record['bridge_pid']==ctx[2].pid
            assert record['stdio_two_pipes_bound'] is True
            assert record['mcp_process_transport_lineage_proven'] is True
            for key in ('git_object_source_verified_by_independent_caller','copilot_egress_attested',
                        'credential_isolation_attested','copilot_process_tree_proven',
                        'g1_g5_closed','live_worker_authorized','worker_result_accepted',
                        'automatic_retry','terminal_ledger_written'):
                assert record[key] is False
        finally:child.close()


def test_join_post_release_never_authorizes():
    with fixture() as ctx:
        child=pin(ctx)
        try:
            post={'schema_version':api.bridge_lib.SCHEMA,'state':'POST_RELEASE_BRIDGE_PINNED_PRE_IPC_REVIEW_ONLY',
                  'backend_bridge_origin_pinned':True,'bridge_pid':ctx[2].pid,'unit':UNIT,
                  'root_release_readback_proven':False,'canonical_mcp_child_independently_proven':False,
                  'terminal_ledger_written':False,'g1_g5_closed':False,'live_worker_authorized':False,
                  'worker_result_accepted':False,'automatic_retry':False}
            answer=api.review_post_release_child(post_review=post,child_pin=child,bridge_pin=ctx[4],backend_socket=ctx[3])
            assert answer['root_release_readback_proven'] is False
            assert answer['canonical_mcp_child_independently_proven'] is False
            assert answer['mcp_lineage']['mcp_process_transport_lineage_proven'] is True
        finally:child.close()


@pytest.mark.parametrize('field,bad,reason',[
    ('source_sha256','0'*64,'SOURCE_SHA'),
    ('executable',Path('/usr/bin/false'),'FROZEN_CANONICAL_MCP_ARGV'),
    ('frozen_argv',('/usr/bin/python3','-c','evil'),'FROZEN_CHILD_ARGV_SIZE'),
])
def test_wrong_static_identity_denied(field,bad,reason):
    with fixture() as ctx:
        with pytest.raises((api.ChildHold,api.bridge_lib.OriginHold),match=reason):
            pin(ctx,**{field:bad})


def test_scope_escape_denied():
    with fixture() as ctx:
        with pytest.raises(api.ChildHold,match='FROZEN_CANONICAL_MCP_ARGV'):
            pin(ctx,source=ctx[0]/'outside.py')


def test_child_cgroup_drift_denied():
    with fixture() as ctx, mock.patch.object(api.session,'_proc_cgroup',return_value='0::/system.slice/other.service'):
        with pytest.raises(api.ChildHold,match='CHILD_NOT_IN_EXACT_UNIT_CGROUP'):
            pin(ctx)


def test_uid_drift_denied():
    with fixture() as ctx, mock.patch.object(api,'_proc_ids',return_value=(999999,999999)):
        with pytest.raises(api.ChildHold,match='CHILD_UID_GID'):
            pin(ctx)


def test_bridge_peer_drift_denied():
    with fixture() as ctx, mock.patch.object(api.bridge_lib,'verify_bridge_pin',side_effect=api.bridge_lib.OriginHold('bad')):
        with pytest.raises(api.ChildHold,match='BRIDGE_NO_LONGER_PINNED'):
            pin(ctx)


def test_unrelated_sibling_not_mistaken_for_child():
    with fixture() as ctx:
        second=subprocess.Popen([str(PYTHON),'-I','-B','-c','import time; time.sleep(9)'],
            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            # An unrelated sibling is not a child of the bridge; it does NOT
            # alter the trusted bridge's one-direct-child observation.
            child=pin(ctx)
            child.close()
        finally:
            second.terminate();second.wait(timeout=3)


def test_fake_extra_child_kernel_list_denied():
    with fixture() as ctx, mock.patch.object(api,'_children',return_value=(ctx[2].pid+1,ctx[2].pid+2)):
        with pytest.raises(api.ChildHold,match='EXACT_ONE_DIRECT_CHILD_REQUIRED'):
            pin(ctx)


def test_pipe_mismatch_denied():
    with fixture() as ctx, mock.patch.object(api,'_transport',side_effect=api.ChildHold('CF10_R142_HOLD_PARENT_STDIO_PIPE_MISMATCH')):
        with pytest.raises(api.ChildHold,match='PARENT_STDIO_PIPE_MISMATCH'):
            pin(ctx)


def test_source_mutation_rejected_on_recheck():
    with fixture() as ctx:
        child=pin(ctx)
        try:
            ctx[1].chmod(0o600)
            ctx[1].write_bytes(CHILD+b'# changed\n')
            with pytest.raises((api.bridge_lib.OriginHold,api.ChildHold),match='SOURCE_SHA|CHILD_READBACK_UNAVAILABLE'):
                api.verify_mcp_child(child_pin=child,bridge_pin=ctx[4],backend_socket=ctx[3])
        finally:child.close()


def test_child_exit_rejected():
    with fixture() as ctx:
        child=pin(ctx)
        try:
            os.kill(child.pid,signal.SIGTERM)
            # On Linux, a zombie child can remain until parent reaps it;
            # pidfd becomes readable and is never accepted as living.
            import time
            for _ in range(100):
                if not api._pidfd_alive(child.pidfd):break
                time.sleep(0.01)
            with pytest.raises(api.ChildHold,match='PIN_CLOSED_OR_EXITED'):
                api.verify_mcp_child(child_pin=child,bridge_pin=ctx[4],backend_socket=ctx[3])
        finally:child.close()


def test_closed_pin_rejected():
    with fixture() as ctx:
        child=pin(ctx)
        child.close()
        with pytest.raises(api.ChildHold,match='PIN_CLOSED_OR_EXITED'):
            api.verify_mcp_child(child_pin=child,bridge_pin=ctx[4],backend_socket=ctx[3])


def test_untrusted_post_join_denied():
    with fixture() as ctx:
        child=pin(ctx)
        try:
            with pytest.raises(api.ChildHold,match='R141_POST_PROOF_INVALID'):
                api.review_post_release_child(post_review={'state':'PASS'},child_pin=child,
                    bridge_pin=ctx[4],backend_socket=ctx[3])
        finally:child.close()


def test_nonroot_denied():
    with mock.patch.object(api.os,'geteuid',return_value=1000):
        with pytest.raises(api.ChildHold,match='ROOT_REQUIRED'):
            api.pin_mcp_child(bridge_pin=None,backend_socket=None,executable=PYTHON,
                source=Path('/run/unknown.py'),source_sha256='0'*64,frozen_argv=())


def test_no_live_cutover_source():
    with mock.patch.object(api.launcher,'LIVE_CUTOVER_ENABLED',True):
        with pytest.raises(api.ChildHold,match='SEALED_SOURCE_CHECK'):
            api.source_check()
