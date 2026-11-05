from __future__ import annotations
from pathlib import Path
import pytest

from scripts.coordination.control_plane import cf10_r078_copilot_cli_smoke_v0_1 as r078
from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as binding


def props():
    return {
        **binding.EXPECTED_PROPERTIES,
        'WorkingDirectory': '/var/lib/forprint-runner',
        'Environment': 'HOME=/var/lib/forprint-runner',
        'Restart': 'no',
        'Type': 'exec',
        'RuntimeMaxSec': '25s',
        'IPAddressDeny': 'any',
    }


def test_fixed_command_no_prompts_secrets_or_network():
    a = r078.build_probe_argv(Path('/usr/local/bin/copilot'), props(),
                              'forprint-cf10-clismoke-' + 'a'*16)
    assert a[-3:] == ['--', '/usr/local/bin/copilot', '--version']
    assert '--wait' in a and '--collect' in a and '--pipe' in a
    assert '--property=IPAddressDeny=any' in a
    assert '--property=StateDirectory=forprint-runner' in a
    assert '--property=StateDirectoryMode=0700' in a
    assert '--property=ProtectSystem=strict' in a
    assert '--property=ProtectHome=yes' in a
    assert '--property=Environment=HOME=/var/lib/forprint-runner' in a
    assert not any('ReadWritePaths' in arg for arg in a)
    assert '-p' not in a and '--allow-all-tools' not in a

@pytest.mark.parametrize('unit',[
    'forprint-cf10-worker-'+'a'*24+'.service',
    'forprint-cf10-clismoke-BAD',
    'forprint-cf10-clismoke-'+'x'*16,
    'forprint-cf10-clismoke-'+'a'*17,
])
def test_reject_unscoped_unit(unit):
    with pytest.raises(r078.SmokeBlocked):
        r078.build_probe_argv(Path('/usr/local/bin/copilot'),props(),unit)

@pytest.mark.parametrize('field,value',[
    ('StateDirectory', 'other'),
    ('StateDirectoryMode', '0777'),
    ('ProtectSystem', 'no'),
    ('ProtectHome', 'no'),
    ('User', 'root'),
    ('IPAddressDeny', 'none'),
    ('Restart', 'always'),
    ('WorkingDirectory', '/srv/software_development/forprint-project/forprint_system_blueprint'),
    ('Environment', 'HOME=/root'),
    ('RuntimeMaxSec', '7200s'),
])
def test_reject_sandbox_drift(field,value):
    p=props();p[field]=value
    with pytest.raises(r078.SmokeBlocked):
        r078.build_probe_argv(Path('/usr/local/bin/copilot'),p,'forprint-cf10-clismoke-'+'b'*16)


def test_reject_broad_rw_exception():
    p=props();p['ReadWritePaths']='/var/lib'
    with pytest.raises(Exception):
        r078.build_probe_argv(Path('/usr/local/bin/copilot'),p,'forprint-cf10-clismoke-'+'c'*16)

@pytest.mark.parametrize('output,category',[
    (b'ENOENT cache', 'CLI_CACHE_OR_BUNDLE_INIT_ERROR'),
    (b'permission denied', 'CLI_SANDBOX_PERMISSION_ERROR'),
    (b'no such file', 'CLI_DEPENDENCY_MISSING'),
    (b'authorization failed', 'CLI_AUTH_OR_CREDENTIAL_MESSAGE_NOT_VERIFIED'),
    (b'unexpected', 'CLI_OTHER_FAILURE_OUTPUT_WITHHELD'),
])
def test_error_category_never_contains_raw_output(output,category):
    assert r078.classify_output(b'',output)==category
