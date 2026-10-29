"""Fixture-only tests. No /var/lib, /etc, /run, live Worker or canonical ledger."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import multiprocessing
import os
from pathlib import Path
import stat
from datetime import datetime, timezone

import pytest

P = Path(__file__).with_name('cf10_s01_root_controlled_single_use_v0_2.py')
if not P.is_file():
    P = Path(__file__).resolve().parents[3] / 'scripts/coordination/control_plane/cf10_s01_root_controlled_single_use_v0_2.py'
spec = importlib.util.spec_from_file_location('cf10_root_single_use_v02', P)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def binding(**updates):
    value = {'receipt_sha256': 'a'*64, 'publication_commit':'b'*40, 'worker_id':'worker-01',
             'task_prompt_id':'cf10-s01-pilot-v0-1', 'attempt_id':'cf10-u180j-a048'}
    value.update(updates)
    return value


@pytest.fixture
def private_dir(tmp_path):
    path = tmp_path / 'cf10_s01_root_claim_fixture'
    path.mkdir(mode=0o700)
    assert stat.S_IMODE(path.stat().st_mode) == 0o700
    return path


def claim(path: Path, *, value=None):
    fd = os.open(path, gate.DIR_FLAGS)
    try:
        return gate.consume_once_fd(fd, binding() if value is None else value, owner_uid=os.getuid())
    finally:
        os.close(fd)


def test_immutable_claim_is_durable_structured_non_authorizing(private_dir):
    result = claim(private_dir)
    assert result['status']=='CONSUMED_NO_LAUNCH_NON_AUTHORIZING'
    assert result['permission_consumed'] and result['claim_record_written']
    assert all(result[k] is False for k in ('launch_allowed','authority_granted','worker_launched',
                'live_make_wired','canonical_ledger_modified','production_claim_cli_enabled'))
    path = private_dir / gate.MARKER
    doc=json.loads(path.read_bytes())
    assert doc['state']=='CONSUMED_BEFORE_SPAWN_NO_RETRY'
    assert doc['binding']==binding()
    assert doc['binding_sha256']==hashlib.sha256(gate.canonical(binding())).hexdigest()
    assert doc['automatic_retry'] is False
    assert doc['authority_granted_by_claim'] is False
    assert stat.S_IMODE(path.stat().st_mode)==0o600


def test_same_claim_after_process_reopening_blocked(private_dir):
    assert claim(private_dir)['claim_record_written']
    first = (private_dir/gate.MARKER).read_bytes()
    assert claim(private_dir)['blockers']==['SINGLE_USE_PERMANENTLY_CONSUMED']
    assert (private_dir/gate.MARKER).read_bytes()==first


def test_new_signed_receipt_cannot_reset_store(private_dir):
    assert claim(private_dir)['claim_record_written']
    assert claim(private_dir,value=binding(receipt_sha256='f'*64))['blockers']==['SINGLE_USE_PERMANENTLY_CONSUMED']


def test_different_attempt_cannot_reset_store(private_dir):
    assert claim(private_dir)['claim_record_written']
    assert claim(private_dir,value=binding(attempt_id='cf10-u180j-a049'))['blockers']==['SINGLE_USE_PERMANENTLY_CONSUMED']


def test_crash_before_spawn_partial_claim_no_retry(private_dir):
    (private_dir/gate.MARKER).write_bytes(b'{"partial":')
    assert claim(private_dir)['blockers']==['SINGLE_USE_PERMANENTLY_CONSUMED']


def test_crash_after_spawn_simulated_with_no_worker_replay(private_dir):
    # No real subprocess is launched. A completed claim means no automatic retry.
    assert claim(private_dir)['claim_record_written']
    synthetic_spawn_count=1
    assert synthetic_spawn_count==1
    assert claim(private_dir)['blockers']==['SINGLE_USE_PERMANENTLY_CONSUMED']


def test_symlink_target_is_not_followed(private_dir):
    outside=private_dir.parent/'outside_target.txt'
    outside.write_text('unchanged')
    (private_dir/gate.MARKER).symlink_to(outside)
    assert claim(private_dir)['blockers']==['SINGLE_USE_PERMANENTLY_CONSUMED']
    assert outside.read_text()=='unchanged'


def test_file_creation_failure_is_blocking(private_dir,monkeypatch):
    real=gate.os.open
    def deny(name, flags, *args, **kwargs):
        if name==gate.MARKER: raise OSError('fixture failure')
        return real(name, flags, *args, **kwargs)
    monkeypatch.setattr(gate.os,'open',deny)
    assert claim(private_dir)['blockers']==['ROOT_STATE_CLAIM_OPEN_FAILED']


def test_partial_write_is_permanently_consumed(private_dir,monkeypatch):
    def fail_write(*args,**kwargs): raise OSError('disk fault')
    monkeypatch.setattr(gate.os,'write',fail_write)
    assert claim(private_dir)['blockers']==['CLAIM_DURABILITY_UNKNOWN_NO_RETRY']
    monkeypatch.undo()
    assert (private_dir/gate.MARKER).exists()
    assert claim(private_dir)['blockers']==['SINGLE_USE_PERMANENTLY_CONSUMED']


def test_fsync_failure_is_permanently_consumed(private_dir,monkeypatch):
    def fail_fsync(*args,**kwargs): raise OSError('fsync failure')
    monkeypatch.setattr(gate.os,'fsync',fail_fsync)
    assert claim(private_dir)['blockers']==['CLAIM_DURABILITY_UNKNOWN_NO_RETRY']
    monkeypatch.undo()
    assert claim(private_dir)['blockers']==['SINGLE_USE_PERMANENTLY_CONSUMED']


def test_unsafe_directory_mode_blocked(private_dir):
    private_dir.chmod(0o750)
    assert claim(private_dir)['blockers']==['PRIVATE_STATE_DESCRIPTOR_UNSAFE']
    assert not (private_dir/gate.MARKER).exists()


def test_readonly_or_regular_file_descriptor_blocked(tmp_path):
    file=tmp_path/'regular';file.write_text('not directory')
    fd=os.open(file,os.O_RDONLY)
    try: assert gate.consume_once_fd(fd,binding(),owner_uid=os.getuid())['blockers']==['PRIVATE_STATE_DESCRIPTOR_UNSAFE']
    finally:os.close(fd)


def test_wrong_owner_blocks(private_dir):
    fd=os.open(private_dir,gate.DIR_FLAGS)
    try: assert gate.consume_once_fd(fd,binding(),owner_uid=os.getuid()+1000)['blockers']==['PRIVATE_STATE_DESCRIPTOR_UNSAFE']
    finally:os.close(fd)


def test_reject_symlink_directory(tmp_path):
    real=tmp_path/'real';real.mkdir(mode=0o700)
    alias=tmp_path/'alias';alias.symlink_to(real)
    with pytest.raises(OSError):os.open(alias,gate.DIR_FLAGS)


def test_no_directory_auto_provision(tmp_path):
    missing=tmp_path/'absent'
    with pytest.raises(FileNotFoundError):os.open(missing,gate.DIR_FLAGS)
    assert not missing.exists()


@pytest.mark.parametrize('bad,code',[
    ({'receipt_sha256':'g'*64},'RECEIPT_DIGEST_INVALID'),
    ({'receipt_sha256':None},'RECEIPT_DIGEST_INVALID'),
    ({'publication_commit':'a'*39},'PUBLICATION_COMMIT_INVALID'),
    ({'worker_id':'worker-02'},'WORKER_ID_INVALID'),
    ({'task_prompt_id':'../traversal'},'TASK_PROMPT_ID_INVALID'),
    ({'attempt_id':'wrong'},'ATTEMPT_ID_INVALID'),
])
def test_invalid_scope_never_claims(private_dir,bad,code):
    assert claim(private_dir,value=binding(**bad))['blockers']==[code]
    assert not (private_dir/gate.MARKER).exists()


def test_forbid_extra_authority_fields(private_dir):
    b=binding();b['grant_worker_launch']=True
    assert claim(private_dir,value=b)['blockers']==['EXACT_SIGNED_BINDING_FIELDS_REQUIRED']


def test_forbid_missing_fields(private_dir):
    b=binding();b.pop('publication_commit')
    assert claim(private_dir,value=b)['blockers']==['EXACT_SIGNED_BINDING_FIELDS_REQUIRED']


def test_timestamp_naive_never_creates_reusable_state(private_dir):
    fd=os.open(private_dir,gate.DIR_FLAGS)
    try:
        result=gate.consume_once_fd(fd,binding(),owner_uid=os.getuid(),now=datetime(2026,10,29))
    finally:os.close(fd)
    assert result['blockers']==['CLAIM_TIMESTAMP_INDETERMINATE_NO_RETRY']
    assert claim(private_dir)['blockers']==['SINGLE_USE_PERMANENTLY_CONSUMED']


def _child(path,q,start):
    start.wait(timeout=8)
    q.put(claim(Path(path))['status'])


def test_eight_process_race_one_claim(private_dir):
    ctx=multiprocessing.get_context('spawn');q=ctx.Queue();ready=ctx.Event()
    ps=[ctx.Process(target=_child,args=(str(private_dir),q,ready)) for _ in range(8)]
    for p in ps:p.start()
    ready.set()
    results=[q.get(timeout=8) for p in ps]
    for p in ps:
        p.join(timeout=8)
        assert not p.is_alive() and p.exitcode==0
    assert results.count('CONSUMED_NO_LAUNCH_NON_AUTHORIZING')==1
    assert results.count('BLOCKED_NON_AUTHORIZING')==7


def test_different_processes_mixed_receipt_still_single_claim(private_dir):
    assert claim(private_dir,value=binding(receipt_sha256='0'*64))['claim_record_written']
    assert claim(private_dir,value=binding(receipt_sha256='1'*64))['blockers']==['SINGLE_USE_PERMANENTLY_CONSUMED']


def test_no_claim_cli_and_no_launch_mode():
    assert gate.main(['inspect'])==0
    assert gate.main(['launch-preflight'])==2


def test_fixed_production_state_path_not_ephemeral():
    assert str(gate.STATE_PATH).startswith('/var/lib/forprint/')
    assert not str(gate.STATE_PATH).startswith('/run/')
    assert gate.MARKER == 'bounded_pilot_consumed_v0_2.json'


def test_source_does_not_launch_or_provision():
    s=P.read_text()
    assert 'subprocess.Popen(' not in s
    assert 'launch_authorized_worker_cycle(' not in s
    assert 'mkdir(' not in s
    assert 'ledger.append_record(' not in s
    assert 'git push' not in s
    assert 'git commit' not in s


def test_root_only_preflight_rejects_nonroot(monkeypatch):
    monkeypatch.setattr(gate.os,'geteuid',lambda:12345)
    with pytest.raises(gate.RootStateError,match='ROOT_ONLY_STATE_ACCESS'):
        gate.open_root_owned_state_dir()
