"""Global path-boundary tests: no live filesystem mutation."""
from pathlib import Path
import os
import pytest
from scripts.coordination.control_plane import blueprint_durable_storage_v0_1 as m

PROJECT=Path('/srv/software_development/forprint-project/forprint_system_blueprint')
ATTEMPT='cf10-u180j-a050'

def test_existing_worker_runtime_root():
    assert m.require_runtime_root(str(m.RUNTIME_ROOT),blueprint_root=PROJECT)==m.RUNTIME_ROOT

@pytest.mark.parametrize('value',[
    '/tmp', '/tmp/abc', '/var/tmp/a', '/srv/software_development/forprint-project/forprint_system_blueprint/tmp/staging',
    '/srv/software_development/forprint-project/forprint_system_blueprint/scripts',
    '/srv/software_development/forprint-worker-runtime/../tmp',
    '/srv/software_development/forprint-worker-runtime//bad',
    'tmp/relative', '/other/persistent/runtime', '/', '/run/forprint',
])
def test_invalid_runtime_roots(value):
    with pytest.raises(m.StorageBoundaryBlocked):m.require_runtime_root(value,blueprint_root=PROJECT)

def test_workspace_is_exact_and_durable():
    p=m.RUNTIME_ROOT/'forprint_system_blueprint'/'worker-01'/ATTEMPT/'workspace'/'repo'
    assert m.require_worker_workspace(p,blueprint_root=PROJECT,attempt_id=ATTEMPT)==p
    for other in (str(p)+'/../../input',str(p)+'/tmp',str(p).replace('/workspace/repo','/input')):
        with pytest.raises(m.StorageBoundaryBlocked):m.require_worker_workspace(other,blueprint_root=PROJECT,attempt_id=ATTEMPT)

def test_receipt_scope_uses_existing_runtime_not_worker_tree():
    p=m.RUNTIME_ROOT/'forprint_system_blueprint'/'control_plane'/'root_receipts'
    assert m.require_root_receipt_store(p,blueprint_root=PROJECT)==p
    for bad in ('/tmp/receipts',m.RUNTIME_ROOT/'forprint_system_blueprint'/'worker-01'/ATTEMPT/'receipt'):
        with pytest.raises(m.StorageBoundaryBlocked):m.require_root_receipt_store(bad,blueprint_root=PROJECT)

def test_no_permission_or_authority_granted():
    assert not hasattr(m,'launch') and not hasattr(m,'claim')
    assert m.RUNTIME_ROOT.is_absolute()
