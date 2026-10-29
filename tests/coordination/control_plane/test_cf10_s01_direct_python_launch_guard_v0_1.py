"""Negative-only guard verification in private checkout. No Worker/ledger mutation."""
from __future__ import annotations
import ast
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'scripts/coordination/control_plane/governed_worker_cycle.py'
BLOCKER='CF10_S01_DIRECT_PYTHON_LAUNCH_QUARANTINED'


def test_source_pinned_s01_quarantine_is_early_in_both_routes():
    mod=ast.parse(SOURCE.read_text())
    functions={n.name:n for n in mod.body if isinstance(n,ast.FunctionDef)}
    helper=functions['require_bounded_s01_launch_authority']
    assert isinstance(helper.body[-1],ast.Raise)
    assert not any(isinstance(n,ast.Return) for n in ast.walk(helper))
    for name in ('launch_cycle','launch_authorized_worker_cycle'):
        body=functions[name].body
        if isinstance(body[0],ast.Expr) and isinstance(body[0].value,ast.Constant) and isinstance(body[0].value.value,str):body=body[1:]
        stmt=body[0]
        assert isinstance(stmt,ast.Expr) and isinstance(stmt.value,ast.Call)
        assert isinstance(stmt.value.func,ast.Name) and stmt.value.func.id=='require_bounded_s01_launch_authority'


def test_direct_python_launch_cycle_fails_before_any_attempt_read(tmp_path):
    from scripts.coordination.control_plane import governed_worker_cycle as cycle
    runtime=tmp_path/'nonexistent-worker-runtime'
    with pytest.raises(cycle.GovernedWorkerCycleError,match=BLOCKER):
        cycle.launch_cycle(root=tmp_path,runtime_root=runtime,
                           task_prompt_id='cf10-s01-pilot',attempt_id='cf10-u180j-a048',confirm=True)
    assert not runtime.exists()


def test_direct_python_authorized_worker_launch_fails_before_ledger_append(tmp_path):
    from scripts.coordination.control_plane import governed_worker_cycle as cycle
    runtime=tmp_path/'nonexistent-worker-runtime'
    with pytest.raises(cycle.GovernedWorkerCycleError,match=BLOCKER):
        cycle.launch_authorized_worker_cycle(root=tmp_path,runtime_root=runtime,
            task_prompt_id='cf10-s01-pilot',attempt_id='cf10-u180j-a048',started_record_data={})
    assert not runtime.exists()


def test_existing_corridor_ast_no_longer_reports_two_unguarded_routes():
    from scripts.coordination.control_plane import cf10_s01_controlled_launch_corridor_v0_1 as c
    assert c.launch_route_blockers(ROOT)==[]


def test_make_launch_targets_are_still_literal_quarantined():
    src=(ROOT/'Makefile').read_text()
    assert 'CF10_MAKE_RELEASE_BINDING=QUARANTINED_NEEDS_INDEPENDENT_REBIND' in src
    from scripts.coordination.control_plane import cf10_s01_controlled_launch_corridor_v0_1 as c
    assert c.launch_route_blockers(ROOT)==[]
