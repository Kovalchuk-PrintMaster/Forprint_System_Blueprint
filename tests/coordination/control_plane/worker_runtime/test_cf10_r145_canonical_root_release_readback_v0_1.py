"""R145 real inode/manifest/release readback plus non-authorizing root gate.

No real systemd, lease, Worker, Copilot, claim or root release occurs.
"""
from __future__ import annotations
from contextlib import contextmanager
import json
import os
import sys
from types import SimpleNamespace
from pathlib import Path
from unittest import mock
import pytest

from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as binding
from scripts.coordination.control_plane.worker_runtime import (
    cf10_r145_canonical_root_release_readback_v0_1 as api,
    cf10_systemd_launcher_v0_1 as backend,
    cf10_systemd_kernel_witness_v0_1 as kernel,
    cf10_r141_held_ipc_bridge_origin_v0_1 as r141,
)

HEAD='a'*40
ATTEMPT='cf10-u180j-a930'
UNIT=binding.unit_for(ATTEMPT,HEAD)
NONCE='1'*64


@pytest.fixture(autouse=True)
def local_r030_runner_adapter(monkeypatch):
    # Local curated snapshot lacks R030's old R026 dependency. On s01 the
    # canonical real module is present and loaded. Only the runner callback
    # is replaced in this isolated test; kernel.show is independently mocked.
    module='scripts.coordination.control_plane.cf10_r030_canonical_systemd_route_v0_1'
    monkeypatch.setitem(sys.modules,module,SimpleNamespace(_trusted_runner=lambda argv: None))



def make_spec():
    return binding.BoundedInput(task_prompt_id='test-r145',attempt_id=ATTEMPT,
        source_head=HEAD,handoff_sha256='b'*64,baseline_sha256='c'*64,
        workspace='/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/worker-01/'+ATTEMPT+'/workspace/repo',
        runtime_root='/srv/software_development/forprint-worker-runtime',
        argv=('/usr/local/bin/forprint-copilot-1.0.107','-p','hello'),timeout_seconds=60)


def write_pair(root:Path,spec=None,nonce=NONCE,release=True):
    spec=make_spec() if spec is None else spec
    raw=backend._manifest(spec,UNIT,nonce,1000.0)
    m=root/('manifest-'+nonce+'.json')
    m.write_bytes(raw);m.chmod(0o644)
    if release:
        blob=backend._json({'schema':'cf10_root_release_v0_1',
            'manifest_sha256':backend._sha(raw)})
        r=root/('release-'+nonce+'.json')
        r.write_bytes(blob);r.chmod(0o644)
    return m,root/('release-'+nonce+'.json')


@contextmanager
def files(tmp_path):
    root=tmp_path/'launch_gates'
    root.mkdir();root.chmod(0o711)
    try:
        yield root
    finally:
        # Fixture owns directory; chmod only this disposable test path.
        root.chmod(0o700)


def inspect(root):
    return api._inspect_root_release_files(spec=make_spec(),unit=UNIT,
        gate_root=root,owner_uid=os.geteuid())


def test_exact_real_manifest_release_inodes(tmp_path):
    with files(tmp_path) as root:
        write_pair(root)
        p=inspect(root)
        assert p['root_owned_manifest_and_release_readback'] is True
        assert len(p['manifest_sha256'])==64
        assert len(p['gate_nonce_sha256'])==64
        assert len(p['release_marker_sha256'])==64


def test_unrelated_historical_manifest_is_ignored(tmp_path):
    with files(tmp_path) as root:
        write_pair(root)
        other=make_spec()
        object.__setattr__(other,'attempt_id','cf10-u180j-a931')
        write_pair(root,other,'2'*64)
        assert inspect(root)['root_owned_manifest_and_release_readback']


@pytest.mark.parametrize('kind',[
    'missing_release','wrong_release_digest','release_extra_fields','release_symlink',
    'manifest_symlink','manifest_mode','release_mode','manifest_duplicate_key',
    'manifest_wrong_source','manifest_wrong_argv','release_not_json',
    'manifest_nonce_mismatch','manifest_wrong_uid','release_hardlink',
    'missing_manifest','ambiguous_manifest','extra_untrusted_manifest',
])
def test_invalid_canonical_pair_denied(tmp_path,kind):
    with files(tmp_path) as root:
        m,r=write_pair(root)
        if kind=='missing_release':r.unlink()
        if kind=='wrong_release_digest':r.write_bytes(backend._json({'schema':'cf10_root_release_v0_1','manifest_sha256':'0'*64}))
        if kind=='release_extra_fields':r.write_bytes(backend._json({'schema':'cf10_root_release_v0_1','manifest_sha256':'0'*64,'authorize':True}))
        if kind=='release_symlink':r.unlink();r.symlink_to(m)
        if kind=='manifest_symlink':m.unlink();m.symlink_to(r)
        if kind=='manifest_mode':m.chmod(0o666)
        if kind=='release_mode':r.chmod(0o600)
        if kind=='manifest_duplicate_key':m.write_bytes(m.read_bytes().replace(b'{',b'{"schema":"extra",',1))
        if kind=='manifest_wrong_source':
            d=json.loads(m.read_bytes());d['source_head']='f'*40;m.write_bytes(backend._json(d))
        if kind=='manifest_wrong_argv':
            d=json.loads(m.read_bytes());d['argv']=['/usr/bin/false'];m.write_bytes(backend._json(d))
        if kind=='release_not_json':r.write_bytes(b'NOT JSON\n')
        if kind=='manifest_nonce_mismatch':
            d=json.loads(m.read_bytes());d['gate_nonce']='f'*64;m.write_bytes(backend._json(d))
        if kind=='manifest_wrong_uid':
            d=json.loads(m.read_bytes());d['runner_uid']=-1;m.write_bytes(backend._json(d))
        if kind=='release_hardlink':os.link(r,root/'copy-release')
        if kind=='missing_manifest':m.unlink()
        if kind=='ambiguous_manifest':write_pair(root,nonce='3'*64)
        if kind=='extra_untrusted_manifest':(root/('manifest-'+'4'*64+'.json')).symlink_to(m)
        with pytest.raises(api.ReleaseHold):inspect(root)


def test_root_dir_symlink_and_untrusted_mode_denied(tmp_path):
    with files(tmp_path) as root:
        write_pair(root)
        root.chmod(0o777)
        with pytest.raises(api.ReleaseHold,match='OWNER_MODE'):inspect(root)
        root.chmod(0o711)
        link=tmp_path/'linked'
        link.symlink_to(root,target_is_directory=True)
        with pytest.raises(api.ReleaseHold,match='GATE_DIRECTORY'):inspect(link)


def held():
    return {'schema_version':r141.SCHEMA,
        'state':'HELD_R030_R135_PRE_RELEASE_REVIEW_ONLY',
        'attempt_id':ATTEMPT,'source_head':HEAD,'unit':UNIT,
        'systemd_invocation_id':'f'*32,
        'live_worker_authorized':False,'worker_result_accepted':False,
        'terminal_ledger_written':False,'g1_g5_closed':False,'automatic_retry':False}


def witness():
    return kernel.KernelWitness(unit=UNIT,invocation_id='f'*32,fd=404,
        armed_populated='1',closed=False)


def kernel_show():
    return {'Id':UNIT,'InvocationID':'f'*32,'ControlGroup':'/system.slice/'+UNIT,
        'ActiveState':'active','User':'forprint-runner','Group':'forprint-runner',
        'KillMode':'control-group'}


def test_live_public_rechecks_pair_and_pinned_kernel():
    spec=make_spec()
    plan=binding.bind_plan(spec)
    args={'spec':spec,'plan':plan,'witness':witness(),'held_review':held()}
    with mock.patch.object(api.os,'geteuid',return_value=0),\
         mock.patch.object(api,'_inspect_root_release_files',return_value={
             'gate_nonce_sha256':'1'*64,'manifest_sha256':'2'*64,
             'release_marker_sha256':'3'*64,'root_owned_manifest_and_release_readback':True}) as files,\
         mock.patch.object(kernel,'show',return_value=kernel_show()) as shown,\
         mock.patch.object(kernel,'read_fd',return_value='1'):
        result=api.review_pre_forward(**args)
        assert result['root_owned_manifest_and_release_readback'] is True
        assert result['worker_executed_proven'] is False
        assert result['live_worker_authorized'] is False
        assert result['terminal_ledger_written'] is False
        assert files.call_args.kwargs['gate_root']==backend.GATES
        assert files.call_args.kwargs['owner_uid']==0
        shown.assert_called_once()


@pytest.mark.parametrize('problem',[
    'not_root','closed','bad_arm','different_invocation','bad_held','kernel_zero',
    'systemd_changed','missing_marker',
])
def test_live_root_rejects_incomplete_or_changed_proof(problem):
    spec=make_spec();plan=binding.bind_plan(spec)
    pin=witness();h=held()
    if problem=='closed':pin.closed=True
    if problem=='bad_arm':pin.armed_populated='0'
    if problem=='different_invocation':h['systemd_invocation_id']='0'*32
    if problem=='bad_held':h['live_worker_authorized']=True
    observed=kernel_show()
    if problem=='systemd_changed':observed['InvocationID']='e'*32
    with mock.patch.object(api.os,'geteuid',return_value=(1000 if problem=='not_root' else 0)),\
         mock.patch.object(api,'_inspect_root_release_files',side_effect=(api.ReleaseHold('missing') if problem=='missing_marker' else None),
             return_value={'root_owned_manifest_and_release_readback':True}),\
         mock.patch.object(kernel,'show',return_value=observed),\
         mock.patch.object(kernel,'read_fd',return_value=('0' if problem=='kernel_zero' else '1')):
        with pytest.raises(api.ReleaseHold):
            api.review_pre_forward(spec=spec,plan=plan,witness=pin,held_review=h)


def test_source_check_reports_no_cutover():
    assert api.source_check()==0
    assert backend.LIVE_CUTOVER_ENABLED is False
