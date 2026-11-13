"""R089: pinned Codex binary installer pure fixtures. Never downloads or installs."""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import stat
import tarfile
from types import SimpleNamespace
from unittest.mock import Mock
import pytest

from scripts.coordination.control_plane.worker_runtime import cf10_r089_codex_pinned_install_v0_1 as m


def sample_asset(machine='x86_64'):
    return m.selected_asset(machine)


def elf(machine=62):
    x=bytearray(1_000_123)
    x[:20]=b'\x7fELF'+bytes([2,1,1])+bytes(11)+machine.to_bytes(2,'little')
    return bytes(x)


def make_tar(path, name='codex-x86_64-unknown-linux-musl', data=None, symlink=False):
    data=elf() if data is None else data
    with tarfile.open(path,'w:gz') as tar:
        entry=tarfile.TarInfo(name)
        if symlink:
            entry.type=tarfile.SYMTYPE
            entry.linkname='/etc/passwd'
            entry.size=0
            tar.addfile(entry)
        else:
            entry.size=len(data)
            tar.addfile(entry,io.BytesIO(data))


def test_pinned_release_and_digests_do_not_use_latest():
    assert m.RELEASE=='0.166.0'
    assert m.TAG=='rust-v0.166.0'
    for arch in ('x86_64','aarch64'):
        asset=sample_asset(arch)
        assert asset['url']=='https://github.com/openai/codex/releases/download/'+m.TAG+'/'+asset['name']
        assert len(asset['sha256'])==64
        assert asset['bytes']>100_000_000
        assert asset['member']==asset['name'].removesuffix('.tar.gz')


@pytest.mark.parametrize('arch',['i386','x86','armv7l','',None,'../bad'])
def test_unsupported_architecture_is_denied(arch):
    # None means current architecture; don't assume local CI hardware.
    if arch is None:
        assert sample_asset('x86_64')['arch']=='x86_64'
    else:
        with pytest.raises(m.InstallBlocked,match='HOST_ARCH_NOT_SUPPORTED'):
            m.selected_asset(arch)


def test_readonly_inspect_does_not_call_install(monkeypatch):
    from scripts.coordination.control_plane.worker_runtime import cf10_r088_codex_offline_attestation_v0_1 as r088
    monkeypatch.setattr(r088,'inspect_candidates',lambda:{'status':'CODEX_CLI_NOT_INSTALLED_IN_ALLOWED_PATHS','selected_executable':None})
    monkeypatch.setattr(m,'install_once',lambda:pytest.fail('no install in inspect'))
    assert m.main(['--mode','inspect'])==0


def test_confirmation_required_before_preflight(monkeypatch):
    monkeypatch.delenv('CF10_CONFIRM_CODEX_INSTALL',raising=False)
    monkeypatch.setattr(m,'install_once',lambda:pytest.fail('must not install'))
    assert m.main(['--mode','install'])==2


def test_exact_confirmation_not_near_miss(monkeypatch):
    monkeypatch.setenv('CF10_CONFIRM_CODEX_INSTALL',m.CONFIRM+'-EXTRA')
    monkeypatch.setattr(m,'install_once',lambda:pytest.fail('must not install'))
    assert m.main(['--mode','install'])==2


def test_nonroot_blocks_before_git_or_network(monkeypatch):
    monkeypatch.setattr(m.os,'geteuid',lambda:1000)
    monkeypatch.setattr(m.os,'isatty',lambda i:True)
    with pytest.raises(m.InstallBlocked,match='EXPLICIT_ROOT'):
        m.preflight_for_install()


def test_no_tty_blocks_before_git(monkeypatch):
    monkeypatch.setattr(m.os,'geteuid',lambda:0)
    monkeypatch.setattr(m.os,'isatty',lambda i:False)
    with pytest.raises(m.InstallBlocked,match='EXPLICIT_ROOT'):
        m.preflight_for_install()


def test_no_overwrite_even_if_symlink(tmp_path):
    d=tmp_path/'codex'
    m._must_not_exist(d,'EXISTS')
    d.symlink_to('/etc/passwd')
    with pytest.raises(m.InstallBlocked,match='EXISTS'):
        m._must_not_exist(d,'EXISTS')


def test_no_overwrite_regular(tmp_path):
    d=tmp_path/'codex';d.write_text('original')
    with pytest.raises(m.InstallBlocked): m._must_not_exist(d,'TARGET_ALREADY_PRESENT')
    assert d.read_text()=='original'


def test_sha_file_digest(tmp_path):
    f=tmp_path/'x';f.write_bytes(b'abc')
    assert m.sha_file(f)==hashlib.sha256(b'abc').hexdigest()


def test_tar_single_elf_member_succeeds(tmp_path):
    path=tmp_path/'release.tar.gz'; out=tmp_path/'codex'
    make_tar(path)
    assert m._extract_checked(path,out,sample_asset())==hashlib.sha256(elf()).hexdigest()
    assert out.read_bytes()[:4]==b'\x7fELF'


@pytest.mark.parametrize('name',['../../tmp/bad','./codex-x86_64-unknown-linux-musl','other','/absolute'])
def test_tar_rejects_nonexact_name(tmp_path,name):
    path=tmp_path/'archive';out=tmp_path/'out'
    make_tar(path,name=name)
    with pytest.raises(m.InstallBlocked,match='TAR_MEMBER_SCOPE'):
        m._extract_checked(path,out,sample_asset())


def test_tar_symlink_rejected(tmp_path):
    path=tmp_path/'archive';out=tmp_path/'out'
    make_tar(path,symlink=True)
    with pytest.raises(m.InstallBlocked,match='TAR_MEMBER_SCOPE'):
        m._extract_checked(path,out,sample_asset())


def test_non_elf_rejected(tmp_path):
    path=tmp_path/'archive';out=tmp_path/'out'
    make_tar(path,data=b'Z'*1_000_123)
    with pytest.raises(m.InstallBlocked,match='NOT_EXPECTED_ELF_ARCH'):
        m._extract_checked(path,out,sample_asset())


def test_wrong_elf_arch_rejected(tmp_path):
    path=tmp_path/'archive';out=tmp_path/'out'
    make_tar(path,data=elf(183))
    with pytest.raises(m.InstallBlocked,match='NOT_EXPECTED_ELF_ARCH'):
        m._extract_checked(path,out,sample_asset())


def test_tar_multiple_members_rejected(tmp_path):
    path=tmp_path/'archive';out=tmp_path/'out'
    make_tar(path)
    with tarfile.open(tmp_path/'two.tar.gz','w:gz') as tar:
        for i in (1,2):
            data=elf()
            entry=tarfile.TarInfo('codex-x86_64-unknown-linux-musl' if i==1 else 'surprise')
            entry.size=len(data);tar.addfile(entry,io.BytesIO(data))
    with pytest.raises(m.InstallBlocked,match='TAR_MEMBER_SCOPE'):
        m._extract_checked(tmp_path/'two.tar.gz',out,sample_asset())


def test_download_sanitized_env_and_fixed_url(monkeypatch,tmp_path):
    asset={'name':'test.tar.gz','url':sample_asset()['url'],
           'bytes':5,'sha256':'f'*64}
    destination=tmp_path/'output'
    def fake(argv,**kw):
        assert argv[0]=='/usr/bin/curl'
        assert argv[-1]==asset['url']
        assert '--location' in argv and '--proto-redir' in argv
        assert '--output' in argv and str(destination) in argv
        assert '--' not in argv
        assert kw['env']=={'PATH':'/usr/bin:/bin','LANG':'C'}
        assert kw['stdin']==m.subprocess.DEVNULL
        assert 'shell' not in kw
        destination.write_bytes(b'abcde')
        return SimpleNamespace(returncode=0,stdout=b'',stderr=b'')
    monkeypatch.setattr(m.subprocess,'run',fake)
    monkeypatch.setattr(m,'sha_file',lambda p:'f'*64)
    m._download_pinned(asset,destination)


def test_download_hash_mismatch_blocks(monkeypatch,tmp_path):
    asset={'name':'test.tar.gz','url':sample_asset()['url'],
           'bytes':5,'sha256':'f'*64}
    destination=tmp_path/'output'
    def fake(argv,**kw):
        destination.write_bytes(b'abcde')
        return SimpleNamespace(returncode=0,stdout=b'',stderr=b'')
    monkeypatch.setattr(m.subprocess,'run',fake)
    with pytest.raises(m.InstallBlocked,match='ARCHIVE_SHA256_MISMATCH'):
        m._download_pinned(asset,destination)


def test_download_nonzero_no_fallback(monkeypatch,tmp_path):
    asset=sample_asset()
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=22,stdout=b'',stderr=b'SECRET'))
    with pytest.raises(m.InstallBlocked,match='FAILED_NO_RETRY'):
        m._download_pinned(asset,tmp_path/'f')


def test_timeout_is_fail_closed(monkeypatch,tmp_path):
    def fake(*args,**kwargs):raise m.subprocess.TimeoutExpired('curl',750)
    monkeypatch.setattr(m.subprocess,'run',fake)
    with pytest.raises(m.InstallBlocked,match='TIMEOUT_NO_RETRY'):
        m._download_pinned(sample_asset(),tmp_path/'f')


def test_receipt_has_no_authority_flags():
    x=m._receipt_body(pinned=sample_asset(),binary_sha256='a'*64,source_head='b'*40)
    assert not x['registry_ready'] and not x['provider_auth_verified']
    assert not x['worker_launched'] and not x['owner_claim_consumed']
    assert x['asset_sha256']==sample_asset()['sha256']


def test_receipt_created_exclusive_private_mode(tmp_path,monkeypatch):
    destination=tmp_path/'receipt.json'
    monkeypatch.setattr(m,'RECEIPT',destination)
    m._record_receipt_once({'evidence':True})
    assert json.loads(destination.read_text())=={'evidence':True}
    assert stat.S_IMODE(destination.stat().st_mode)==0o600
    with pytest.raises(FileExistsError):m._record_receipt_once({'evidence':False})
    assert json.loads(destination.read_text())=={'evidence':True}


def test_module_no_unsafe_auto_execution():
    source=Path(m.__file__).read_text()
    assert 'os.system(' not in source
    assert 'shell=True' not in source
    assert 'os.replace(' not in source
    assert 'os.link(executable, DESTINATION' in source
    assert "'--version'" not in source
    assert 'npm install' not in source
    assert 'curl|sh' in source  # only a negated docstring description


def test_receipt_root_is_permanent():
    assert str(m.RECEIPT).startswith('/var/lib/')
    assert not str(m.RECEIPT).startswith('/tmp/')
    assert not str(m.RECEIPT).startswith('/srv/software_development/forprint-project/')


def test_synthetic_atomic_install_with_receipt_never_touches_real_system(tmp_path, monkeypatch):
    """Only a fake binary inside tmp_path is ever linked; no curl, systemd, auth."""
    from scripts.coordination.control_plane.worker_runtime import cf10_r088_codex_offline_attestation_v0_1 as r088
    private_bin=tmp_path/'fake-system-bin';private_bin.mkdir()
    destination=private_bin/'codex'
    monkeypatch.setattr(m,'DESTINATION',destination)
    monkeypatch.setattr(m,'OTHER',tmp_path/'other-system-bin'/'codex')
    monkeypatch.setattr(m,'_receipt_directory',lambda:None)
    monkeypatch.setattr(m,'preflight_for_install',lambda:{'head':'a'*40,'asset':sample_asset()})
    monkeypatch.setattr(m,'_download_pinned',lambda asset,path:path.write_bytes(b'fake-test-archive'))
    test_bin=elf()
    def fake_extract(archive,target,asset):
        target.write_bytes(test_bin)
        return hashlib.sha256(test_bin).hexdigest()
    monkeypatch.setattr(m,'_extract_checked',fake_extract)
    write=Mock()
    monkeypatch.setattr(m,'_record_receipt_once',write)
    original=m.tempfile.TemporaryDirectory
    def sandbox_dir(*,prefix,dir):
        if dir=='/var/tmp':
            dir=tmp_path/'scratch'
            dir.mkdir(exist_ok=True)
        return original(prefix=prefix,dir=dir)
    monkeypatch.setattr(m.tempfile,'TemporaryDirectory',sandbox_dir)
    monkeypatch.setattr(r088,'inspect_candidates',lambda:{'selected_executable':str(destination)})
    result=m.install_once()
    assert result['status']=='PINNED_OFFICIAL_CODEX_BINARY_INSTALLED_NONAUTHORIZING'
    assert destination.read_bytes()==test_bin
    assert stat.S_IMODE(destination.stat().st_mode)==0o755
    assert result['provider_ready'] is False
    assert result['offline_version_probe_executed'] is False
    assert not result['worker_launched'] and not result['claim_consumed']
    write.assert_called_once()
    assert write.call_args.args[0]['binary_sha256']==hashlib.sha256(test_bin).hexdigest()


def test_synthetic_install_existing_destination_never_overwritten(tmp_path,monkeypatch):
    from scripts.coordination.control_plane.worker_runtime import cf10_r088_codex_offline_attestation_v0_1 as r088
    private_bin=tmp_path/'fake-system-bin'; private_bin.mkdir()
    destination=private_bin/'codex';destination.write_bytes(b'original-binary')
    monkeypatch.setattr(m,'DESTINATION',destination)
    monkeypatch.setattr(m,'OTHER',tmp_path/'other-bin'/'codex')
    monkeypatch.setattr(m,'_receipt_directory',lambda:None)
    monkeypatch.setattr(m,'preflight_for_install',lambda:{'head':'a'*40,'asset':sample_asset()})
    monkeypatch.setattr(m,'_download_pinned',lambda asset,path:path.write_bytes(b'fake-archive'))
    monkeypatch.setattr(m,'_extract_checked',lambda archive,target,asset:(target.write_bytes(b'fake-binary') or 'a'*64))
    monkeypatch.setattr(m,'_record_receipt_once',lambda body:pytest.fail('must not issue receipt'))
    original=m.tempfile.TemporaryDirectory
    def sandbox_dir(*,prefix,dir):
        if dir=='/var/tmp':
            dir=tmp_path/'scratch';dir.mkdir(exist_ok=True)
        return original(prefix=prefix,dir=dir)
    monkeypatch.setattr(m.tempfile,'TemporaryDirectory',sandbox_dir)
    monkeypatch.setattr(r088,'inspect_candidates',lambda:{'selected_executable':str(destination)})
    with pytest.raises(m.InstallBlocked,match='CONCURRENT_INSTALL_TARGET_EXISTS'):
        m.install_once()
    assert destination.read_bytes()==b'original-binary'
