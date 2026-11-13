"""CF10 AA: AST inventory reports metadata, not source or credential values."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path
import pytest
from scripts.coordination.control_plane.worker_runtime import cf10_repository_risk_inventory_v0_1 as mod

@pytest.mark.parametrize('src,code',[
    (b'import subprocess\nsubprocess.run("echo hi",shell=True)\n','SUBPROCESS_SHELL_TRUE'),
    (b'eval("2+2")','DYNAMIC_EXECUTION_OR_UNSAFE_LOAD'),
    (b'LIVE_CUTOVER_ENABLED = True\n','LIVE_CUTOVER_SOURCE_NOT_FALSE'),
    (b'import yaml\nyaml.load("foo")\n','YAML_LOAD_CHECK_LOADER'),
])
def test_security_findings(src,code):
    rows,ok=mod.analyze_source(src,'example.py')
    assert ok and any(row['code']==code for row in rows)
    assert all('source' not in row for row in rows)

def test_negative_source_parse():
    rows,ok=mod.analyze_source(b'def bad(:','bad.py')
    assert not ok and rows[0]['code']=='PYTHON_PARSE_FAILED'

def test_safe_source_no_findings():
    rows,ok=mod.analyze_source(b'LIVE_CUTOVER_ENABLED=False\nprint(3)\n','safe.py')
    assert ok and rows==[]

def test_git_tracked_python_inventory(tmp_path):
    subprocess.run(['git','init','-q',str(tmp_path)],check=True)
    (tmp_path/'a.py').write_text('LIVE_CUTOVER_ENABLED = False\n')
    (tmp_path/'b.py').write_text('import subprocess\nsubprocess.run("true",shell=True)\n')
    (tmp_path/'readme.md').write_text('hello')
    subprocess.run(['git','-C',str(tmp_path),'add','.'],check=True)
    subprocess.run(['git','-C',str(tmp_path),'-c','user.name=Test','-c','user.email=t@example.invalid',
                    'commit','-qm','fixture'],check=True)
    row=mod.inventory(tmp_path)
    assert row['tracked_files']==3 and row['python_tracked']==2
    assert row['python_ast_parsed']==2
    assert row['risk_counts']=={'SUBPROCESS_SHELL_TRUE':1}
    assert row['full_python_tracked_scan_completed'] is True
    assert row['source_text_in_evidence'] is False and row['g1_g5_open'] is True
    assert all('shell=True' not in json.dumps(v) for v in row['risk_findings_sample'])

def test_inventory_requires_git(tmp_path):
    with pytest.raises(mod.InventoryHold):mod.inventory(tmp_path)
