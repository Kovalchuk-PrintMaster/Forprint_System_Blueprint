"""R143 kernel-child + immutable Git-object capsule source review, never live."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
from unittest import mock

import pytest

from scripts.coordination.control_plane.worker_runtime import (
    cf10_r143_git_mcp_capsule_origin_v0_1 as api,
)


def git(root,*argv):
    cp=subprocess.run(('git','-C',str(root),*argv),stdin=subprocess.DEVNULL,
                      stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,
                      env={**os.environ,'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null',
                           'GIT_AUTHOR_NAME':'fixture','GIT_AUTHOR_EMAIL':'fixture@invalid.local',
                           'GIT_COMMITTER_NAME':'fixture','GIT_COMMITTER_EMAIL':'fixture@invalid.local'})
    return cp.stdout.decode().strip()


@contextmanager
def fixture():
    lab=Path('/run/forprint-cf10-r125-'+secrets.token_hex(8))
    lab.mkdir(mode=0o700)
    try:
        with tempfile.TemporaryDirectory(prefix='cf10-r143-fixture-') as work:
            repo=Path(work)
            git(repo,'init','-q')
            cap=lab/'source_capsule'
            for rel in api.CAPSULE_FILES:
                data=bytes() if rel.endswith('/__init__.py') else ('canonical git source for '+rel+'\n').encode()
                for home in (repo,cap):
                    file=home/rel;file.parent.mkdir(parents=True,exist_ok=True)
                    file.write_bytes(data);file.chmod(0o400)
            git(repo,'add','.')
            git(repo,'commit','-q','-m','fixture')
            commit=git(repo,'rev-parse','HEAD')
            bridge_source=lab/'bridge.py'
            bridge_source.write_bytes(b'# bridge source\n');bridge_source.chmod(0o400)
            pin=api.bridge_api.BridgePin(
                pid=18765,pidfd=98,unit='forprint-cf10-worker-'+'f'*24+'.service',
                start_ticks='2028',executable=Path('/usr/bin/python3'),
                executable_dev_ino=(1,2),source=bridge_source,
                source_inode=(1,2,16,'b'*64),source_sha256='b'*64,
                argv=('/usr/bin/python3','-I','-B',str(bridge_source)))
            mcp=cap/api.MCP
            child=api.child_api.MCPChildPin(
                pid=18766,pidfd=99,bridge_pid=pin.pid,unit=pin.unit,
                start_ticks='2029',exe_dev_ino=(1,2),source=mcp,
                source_inode=(1,2,mcp.stat().st_size,hashlib.sha256(mcp.read_bytes()).hexdigest()),
                argv=('/usr/bin/python3','-I','-B',str(mcp)),pipes=('pipe:[1]','pipe:[2]'))
            status={'schema_version':api.child_api.SCHEMA,
               'state':'R142_MCP_CHILD_PIDFD_STDIO_ORIGIN_REVIEW_ONLY',
               'unit':pin.unit,'bridge_pid':pin.pid,'mcp_pid':child.pid,
               'mcp_process_transport_lineage_proven':True,
               'git_object_source_verified_by_independent_caller':False,
               'g1_g5_closed':False,'worker_result_accepted':False}
            with mock.patch.object(api,'ROOT',repo),\
                 mock.patch.object(api.child_api,'verify_mcp_child',return_value=status) as verify:
                yield repo,lab,cap,pin,child,commit,verify
    finally:shutil.rmtree(lab)


def verify(ctx,**kwargs):
    repo,_,_,bridge,child,commit,_=ctx
    opts=dict(bridge_pin=bridge,child_pin=child,
              backend_socket=None,frozen_source_commit=commit,root=repo)
    opts.update(kwargs)
    return api.review_git_pinned_mcp(**opts)


def test_source_sealed():
    assert api.source_check()==0


def test_git_head_capsule_child_review_success():
    with fixture() as x:
        value=verify(x)
        assert value['source_commit']==x[5]
        assert value['capsule_file_count']==14
        assert value['mcp_process_transport_lineage_proven'] is True
        assert value['git_object_source_verified_by_independent_caller'] is True
        assert x[-1].call_count==2
        for label in ('live_worker_authorized','root_release_readback_proven',
            'g1_g5_closed','worker_result_accepted','terminal_ledger_written',
            'copilot_egress_attested','credential_isolation_attested','automatic_retry'):
            assert value[label] is False


def test_empty_tracked_python_init_files_legitimate():
    with fixture() as x:
        assert (x[2]/'scripts/__init__.py').stat().st_size == 0
        assert verify(x)['capsule_file_count']==14


def test_dirty_worktree_source_not_imported():
    with fixture() as x:
        changed=x[0]/api.MCP
        changed.chmod(0o600);changed.write_bytes(b'dirty and not in capsule')
        assert verify(x)['git_object_source_verified_by_independent_caller'] is True
        assert (x[2]/api.MCP).read_bytes()!=changed.read_bytes()


@pytest.mark.parametrize('index',[0,4,8,13])
def test_capsule_file_tamper_denied(index):
    with fixture() as x:
        p=x[2]/api.CAPSULE_FILES[index]
        p.chmod(0o600);p.write_bytes(p.read_bytes()+b'TAMPER')
        with pytest.raises(api.CapsuleHold,match='CAPSULE_CONTENT_DIFFERS_FROM_GIT'):
            verify(x)


def test_capsule_file_symlink_denied():
    with fixture() as x:
        p=x[2]/api.CAPSULE_FILES[-1]
        original=p.with_name('unexpected');p.rename(original)
        p.symlink_to(original)
        with pytest.raises(api.CapsuleHold,match='CAPSULE_SYMLINK'):
            verify(x)


def test_capsule_unknown_file_denied():
    with fixture() as x:
        (x[2]/'__pycache__').mkdir()
        (x[2]/'__pycache__/mcp.pyc').write_bytes(b'injected')
        with pytest.raises(api.CapsuleHold,match='CAPSULE_EXTRA_FILE'):
            verify(x)


def test_capsule_extra_empty_directory_does_not_modify_code():
    # Empty directories do not affect Python imports; ensure the exact file set.
    with fixture() as x:
        (x[2]/'unexpected_empty').mkdir()
        assert verify(x)['capsule_file_count']==14


def test_source_deleted_denied():
    with fixture() as x:
        (x[2]/api.CAPSULE_FILES[-1]).unlink()
        with pytest.raises(api.CapsuleHold,match='CAPSULE_FILESET'):
            verify(x)


def test_group_writable_directory_denied():
    with fixture() as x:
        p=x[2]/'scripts/coordination'
        p.chmod(0o770)
        with pytest.raises(api.CapsuleHold,match='CAPSULE_PARENT_UNSAFE'):
            verify(x)


def test_group_writable_file_denied():
    with fixture() as x:
        (x[2]/api.MCP).chmod(0o660)
        with pytest.raises(api.CapsuleHold,match='CAPSULE_FILE_INODE'):
            verify(x)


def test_non_git_file_cannot_be_used():
    with fixture() as x:
        git(x[0],'rm','-q','--',api.MCP)
        git(x[0],'commit','-q','-m','removed mcp')
        with pytest.raises(api.CapsuleHold,match='SOURCE_COMMIT_NOT_CURRENT_HEAD'):
            verify(x)


def test_commit_drift_fails_closed():
    with fixture() as x:
        extra=x[0]/'new.txt';extra.write_text('next')
        git(x[0],'add','new.txt');git(x[0],'commit','-q','-m','drift')
        with pytest.raises(api.CapsuleHold,match='SOURCE_COMMIT_NOT_CURRENT_HEAD'):
            verify(x)


@pytest.mark.parametrize('bad',[True,'a'*40,'',None])
def test_frozen_commit_bad_denied(bad):
    with fixture() as x:
        with pytest.raises((api.CapsuleHold,TypeError),match='SOURCE_COMMIT|BLOB_SCOPE'):
            verify(x,frozen_source_commit=bad)


def test_wrong_child_source_path_denied():
    with fixture() as x:
        x[4].source=x[1]/'other.py'
        with pytest.raises(api.CapsuleHold,match='CHILD_PIN_SCOPE'):
            verify(x)


def test_wrong_child_source_digest_denied():
    with fixture() as x:
        x[4].source_inode=(1,2,3,'0'*64)
        with pytest.raises(api.CapsuleHold,match='CHILD_SOURCE_NOT_GIT_BLOB'):
            verify(x)


def test_transport_recheck_fails_closed():
    with fixture() as x:
        x[-1].side_effect=[x[-1].return_value,api.child_api.ChildHold('lost')]
        with pytest.raises(api.CapsuleHold,match='CHILD_POST_GIT_RECHECK'):
            verify(x)


def test_transport_identity_changed_during_git_read_denied():
    with fixture() as x:
        wrong={**x[-1].return_value,'mcp_pid':-1}
        x[-1].side_effect=[x[-1].return_value,wrong]
        with pytest.raises(api.CapsuleHold,match='CHILD_CHANGED_DURING_GIT_READBACK'):
            verify(x)


def test_bad_initial_transport_denied():
    with fixture() as x:
        x[-1].return_value={**x[-1].return_value,'mcp_process_transport_lineage_proven':False}
        with pytest.raises(api.CapsuleHold,match='CHILD_TRANSPORT_UNTRUSTED'):
            verify(x)


def test_closed_bridge_denied():
    with fixture() as x:
        x[3].closed=True
        with pytest.raises(api.CapsuleHold,match='BRIDGE_PIN_REQUIRED'):
            verify(x)


def test_no_root_denied():
    with fixture() as x, mock.patch.object(api.os,'geteuid',return_value=1001):
        with pytest.raises(api.CapsuleHold,match='ROOT_REQUIRED'):
            verify(x)


def test_unsafe_source_git_symlink_denied():
    with fixture() as x:
        p=x[0]/api.MCP
        p.unlink();p.symlink_to('other.py')
        git(x[0],'add','--',api.MCP);git(x[0],'commit','-q','-m','malicious symlink')
        with pytest.raises(api.CapsuleHold,match='BLOB_NOT_CANONICAL_REGULAR'):
            verify(x,frozen_source_commit=git(x[0],'rev-parse','HEAD'))


def test_no_new_ledger_writer_or_release_source():
    source=Path(api.__file__).read_text()
    assert 'append_record(' not in source
    assert 'systemctl start' not in source
    assert 'launch_after_owner_claim(' not in source
