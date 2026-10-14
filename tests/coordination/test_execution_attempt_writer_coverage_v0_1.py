"""Fixture-only; never writes production ledger, /etc, /run or Git remote."""
import json
from pathlib import Path

import pytest
from scripts.coordination import execution_attempt_writer_coverage_v0_1 as m
from scripts.coordination import execution_attempt_writer_activation_v0_1 as gate


def fixture_plan():
    return {
        "schema_version": m.SCHEMA, "status": "READY_FOR_INDEPENDENT_REVIEW",
        "gate_publication": {"commit": "a" * 40, "remote": m.PUBLISHED_REMOTE, "ref": m.GATE_REF},
        "writer_publication": {"commit": m.PUBLISHED_COMMIT, "remote": m.PUBLISHED_REMOTE, "ref": m.PUBLISHED_REF},
        "known_writer_entrypoints": list(m.REQUIRED),
        "static_callsite_candidates": [{"file": m.REQUIRED[0], "line": 12, "classification": "STATIC_CALLSITE_REQUIRES_REVIEW"}], "observed_writer_processes": [],
        "observed_scheduler_references": [], "unreviewed_scheduler_symlinks": [], "technical_blockers": [],
        "unproven_boundaries": ["short_lived_writers"],
        "independent_operator_review_required": True,
        "deployment_coverage_verified": False, "external_provisioning_performed": False,
        "git_mutation_performed": False,
    }


def patch_technical(monkeypatch):
    monkeypatch.setattr(m, "release_checks", lambda *a, **k: [])
    monkeypatch.setattr(m, "publication_bindings", lambda *a, **k: {
        "gate_publication": {"commit": "a" * 40, "remote": m.PUBLISHED_REMOTE, "ref": m.GATE_REF},
        "writer_publication": {"commit": m.PUBLISHED_COMMIT, "remote": m.PUBLISHED_REMOTE, "ref": m.PUBLISHED_REF},
    })
    monkeypatch.setattr(m, "git", lambda *a, **k: "a" * 40 if k == {} and len(a) >= 3 and a[-2:] == ('rev-parse','HEAD') else "")
    monkeypatch.setattr(m, "scan_processes", lambda *a, **k: ([], []))
    monkeypatch.setattr(m, "scan_schedules", lambda *a, **k: ([], []))
    monkeypatch.setattr(m, "scan_call_sites", lambda *a, **k: ([{"file": m.REQUIRED[0], "line": 12, "classification": "STATIC_CALLSITE_REQUIRES_REVIEW"}], []))


def save(tmp_path, plan):
    (tmp_path / 'tmp').mkdir(exist_ok=True)
    path, _ = m.write_plan(tmp_path, Path('tmp/evidence.json'), plan)
    return path


def test_required_entrypoints_match_activation_contract():
    assert set(m.REQUIRED) == {
        "scripts/coordination/control_plane/governed_worker_cycle.py",
        "scripts/coordination/control_plane/dispatch_intent.py",
        "scripts/coordination/execution_attempt_ledger_v0_1.py"}
    assert m.PUBLISHED_COMMIT == '628dd60542c9eefce9db001086ff80fd848e182d'


def test_ast_static_writer_candidates(tmp_path):
    source = tmp_path / 'scripts/coordination/inner.py'
    source.parent.mkdir(parents=True)
    source.write_text("def do(ledger):\n    return ledger.append_record({})\n")
    rows, errors = m.scan_call_sites(tmp_path)
    assert errors == []
    assert rows == [{"file": 'scripts/coordination/inner.py', "line": 2,
                     "classification": 'STATIC_CALLSITE_REQUIRES_REVIEW'}]


def test_scan_rejects_python_parse_error(tmp_path):
    source = tmp_path / 'scripts/coordination/broken.py'
    source.parent.mkdir(parents=True)
    source.write_text('x =(\n')
    _, errors = m.scan_call_sites(tmp_path)
    assert errors == ["SOURCE_PARSE_FAILED:scripts/coordination/broken.py"]


def test_process_inventory_identifies_writer_but_not_generic(tmp_path):
    for n, raw in [('101', b'python\x00-m\x00scripts.coordination.control_plane.governed_worker_cycle\x00'),
                   ('202', b'python\x00--version\x00')]:
        folder = tmp_path / n
        folder.mkdir()
        (folder / 'cmdline').write_bytes(raw)
    rows, errors = m.scan_processes(tmp_path)
    assert errors == [] and len(rows) == 1 and rows[0]['pid'] == 101


def test_schedule_inventory_reports_ref_and_symlink(tmp_path):
    file = tmp_path / 'worker.service'
    file.write_text('ExecStart=python -m scripts.coordination.control_plane.dispatch_intent')
    (tmp_path / 'ln.service').symlink_to(file)
    matches, errors = m.scan_schedules((tmp_path,))
    assert len(matches) == 1 and matches[0]['matching_terms'] == ['dispatch_intent']
    assert errors == []  # A safe, resolved alias is scanned, not left unreviewed.
    assert matches[0]['path'] == str(file.resolve())


def test_plan_always_non_authorizing(monkeypatch, tmp_path):
    patch_technical(monkeypatch)
    doc = m.build_plan(tmp_path, writer_release_root=tmp_path / "writer")
    assert doc['status'] == 'READY_FOR_INDEPENDENT_REVIEW'
    assert doc['deployment_coverage_verified'] is False
    assert doc['independent_operator_review_required'] is True
    assert doc['static_callsite_candidates']


def test_plan_blocked_when_technical_probes_fail(monkeypatch, tmp_path):
    patch_technical(monkeypatch)
    monkeypatch.setattr(m, 'release_checks', lambda *a, **k: ['PUBLISHED_REF_DRIFT'])
    assert m.build_plan(tmp_path, writer_release_root=tmp_path / "writer")['status'] == 'BLOCKED'


def test_output_only_direct_project_tmp(tmp_path):
    (tmp_path / 'tmp').mkdir()
    with pytest.raises(m.CoverageBlocked, match='OUTPUT_MUST_BE'):
        m.write_plan(tmp_path, Path('outside.json'), fixture_plan())
    with pytest.raises(m.CoverageBlocked, match='OUTPUT_MUST_BE'):
        m.write_plan(tmp_path, Path('tmp/../outside.json'), fixture_plan())


def test_output_create_only(tmp_path):
    path = save(tmp_path, fixture_plan())
    with pytest.raises(m.CoverageBlocked, match='OUTPUT_EXISTS'):
        m.write_plan(tmp_path, path, fixture_plan())


def test_check_returns_only_review_ready(monkeypatch, tmp_path):
    patch_technical(monkeypatch)
    path = save(tmp_path, fixture_plan())
    got = m.check_plan(tmp_path, path, writer_release_root=tmp_path / "writer")
    assert got['status'] == 'READY_FOR_INDEPENDENT_REVIEW'
    assert got['deployment_coverage_verified'] is False
    assert got['evidence_sha256'] == m.sha(path.read_bytes())


def test_check_rejects_unsigned_authority_in_plan(monkeypatch, tmp_path):
    patch_technical(monkeypatch)
    doc = fixture_plan()
    doc['deployment_coverage_verified'] = True
    path = save(tmp_path, doc)
    with pytest.raises(m.CoverageBlocked, match='PLAN_FALSE_AUTHORITY'):
        m.check_plan(tmp_path, path, writer_release_root=tmp_path / "writer")


def test_check_rejects_process_drift(monkeypatch, tmp_path):
    patch_technical(monkeypatch)
    path = save(tmp_path, fixture_plan())
    monkeypatch.setattr(m, 'scan_processes', lambda *a, **k: ([{'pid': 77}], []))
    assert 'PROCESS_INVENTORY_CHANGED_REGENERATE_PLAN' in m.check_plan(tmp_path, path, writer_release_root=tmp_path / "writer")['blockers']


def test_check_blocks_unresolved_technical_problems(monkeypatch, tmp_path):
    patch_technical(monkeypatch)
    doc = fixture_plan()
    doc['technical_blockers'] = ['SCHEDULE_UNREADABLE:/etc/cron.d']
    path = save(tmp_path, doc)
    assert m.check_plan(tmp_path, path, writer_release_root=tmp_path / "writer")['status'] == 'BLOCKED'


def test_verify_fails_closed_when_external_evidence_missing(monkeypatch, tmp_path):
    patch_technical(monkeypatch)
    path = save(tmp_path, fixture_plan())
    monkeypatch.setattr(gate, 'trusted_json', lambda *a, **k: (_ for _ in ()).throw(gate.ActivationBlocked('NO_EXTERNAL_COVERAGE')))
    result = m.verify_coverage(tmp_path, path, writer_release_root=tmp_path / "writer")
    assert result['status'] == 'BLOCKED'
    assert result['activation_authorized'] is False


def test_verify_rejects_unbound_external_coverage(monkeypatch, tmp_path):
    patch_technical(monkeypatch)
    path = save(tmp_path, fixture_plan())
    doc = {'gate_publication_commit': "a" * 40, 'gate_publication_remote': m.PUBLISHED_REMOTE,
           'gate_publication_ref': m.GATE_REF,
           'publication_commit':m.PUBLISHED_COMMIT, 'publication_remote':m.PUBLISHED_REMOTE,
           'publication_ref':m.PUBLISHED_REF, 'technical_evidence_sha256': 'wrong',
           'writer_entrypoints':list(m.REQUIRED)}
    monkeypatch.setattr(gate, 'trusted_json', lambda *a, **k:(doc,b''))
    monkeypatch.setattr(gate, 'validate_coverage', lambda *a, **k:None)
    got = m.verify_coverage(tmp_path, path, writer_release_root=tmp_path / "writer")
    assert got['status'] == 'BLOCKED'
    assert 'EXTERNAL_COVERAGE_BINDING_DRIFT:technical_evidence_sha256' in got['blockers']


def test_verify_valid_independent_attestation_still_no_authority(monkeypatch, tmp_path):
    patch_technical(monkeypatch)
    path = save(tmp_path, fixture_plan())
    doc = {'gate_publication_commit': "a" * 40, 'gate_publication_remote': m.PUBLISHED_REMOTE,
           'gate_publication_ref': m.GATE_REF,
           'publication_commit':m.PUBLISHED_COMMIT, 'publication_remote':m.PUBLISHED_REMOTE,
           'publication_ref':m.PUBLISHED_REF, 'technical_evidence_sha256':m.sha(path.read_bytes()),
           'writer_entrypoints':list(m.REQUIRED)}
    monkeypatch.setattr(gate, 'trusted_json', lambda *a, **k:(doc,b''))
    monkeypatch.setattr(gate, 'validate_coverage', lambda *a, **k:None)
    got = m.verify_coverage(tmp_path, path, writer_release_root=tmp_path / "writer")
    assert got['status'] == 'INDEPENDENTLY_ATTESTED_NON_AUTHORIZING'
    assert got['activation_authorized'] is False
    assert got['external_provisioning_performed'] is False


def test_release_check_preserves_published_blob_newline(monkeypatch, tmp_path):
    """Both published Git trees use raw bytes, including trailing newline."""
    import hashlib
    import subprocess
    gate_root, writer_root = tmp_path / "gate", tmp_path / "writer"
    gate_root.mkdir(); writer_root.mkdir()
    def init(repo, names):
        subprocess.run(['git', 'init', '-q'], cwd=repo, check=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.invalid'], cwd=repo, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test'], cwd=repo, check=True)
        for name in names:
            file = repo / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(b'print("example")\n')
        subprocess.run(['git', 'add', '.'], cwd=repo, check=True)
        subprocess.run(['git', 'commit', '-qm', 'fixture'], cwd=repo, check=True)
        subprocess.run(['git', 'remote', 'add', 'origin', m.PUBLISHED_REMOTE], cwd=repo, check=True)
        return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
    writer_paths = dict.fromkeys(list(m.REQUIRED) + ['scripts/coordination/execution_attempt_writer_lock_v0_1.py'])
    writer_sha = init(writer_root, writer_paths)
    gate_sha = init(gate_root, m.GATE_SOURCE_FILES)
    monkeypatch.setattr(m, 'PUBLISHED_COMMIT', writer_sha)
    monkeypatch.setattr(gate, 'SOURCES', {
        p: hashlib.sha256(b'print("example")\n').hexdigest() for p in writer_paths})
    probe = lambda url, ref: gate_sha if ref == m.GATE_REF else writer_sha
    assert m.release_checks(gate_root, writer_root, remote_probe=probe) == []
    bindings = m.publication_bindings(gate_root, writer_root)
    assert bindings['gate_publication']['source_sha256'][m.GATE_SOURCE_FILES[0]] == hashlib.sha256(b'print("example")\n').hexdigest()
    assert bindings['writer_publication']['source_sha256'][m.REQUIRED[0]] == hashlib.sha256(b'print("example")\n').hexdigest()
    (writer_root / m.REQUIRED[0]).write_bytes(b'print("tampered")\n')
    assert 'WRITER_ENTRYPOINT_WORKTREE_DRIFT:' + m.REQUIRED[0] in m.release_checks(
        gate_root, writer_root, remote_probe=probe)
    (writer_root / m.REQUIRED[0]).write_bytes(b'print("example")\n')
    (gate_root / m.GATE_SOURCE_FILES[0]).write_bytes(b'print("unpublished")\n')
    assert 'GATE_SOURCE_NOT_PUBLISHED:' + m.GATE_SOURCE_FILES[0] in m.release_checks(
        gate_root, writer_root, remote_probe=probe)
    assert 'GATE_REF_NOT_EQUAL_CHECKOUT_HEAD' in m.release_checks(
        gate_root, writer_root, remote_probe=lambda u, r: writer_sha if r == m.GATE_REF else writer_sha)


def test_unreviewed_systemd_symlink_keeps_operator_review_required(monkeypatch, tmp_path):
    patch_technical(monkeypatch)
    monkeypatch.setattr(m, 'scan_schedules', lambda *a, **k: (
        [], ['SCHEDULE_SYMLINK_UNREVIEWED:/etc/systemd/system/alias.service']))
    report = m.build_plan(tmp_path, writer_release_root=tmp_path / "writer")
    assert report['status'] == 'READY_FOR_INDEPENDENT_REVIEW'
    assert report['deployment_coverage_verified'] is False
    assert report['unreviewed_scheduler_symlinks']


def test_python_from_blueprint_venv_is_not_a_writer(tmp_path):
    """The coverage CLI itself must not cause plan/check PID drift."""
    for pid, argv in (
        ('101', [
            '/srv/software_development/forprint-project/forprint_system_blueprint/.venv_blueprint/bin/python',
            '-B', '-m', 'scripts.coordination.execution_attempt_writer_coverage_v0_1',
            'plan']),
        ('102', ['make', 'shared-ledger-writer-coverage-check']),
        ('103', ['/bin/bash', '-c', 'python -m scripts.coordination.control_plane.governed_worker_cycle launch']),
    ):
        folder = tmp_path / pid
        folder.mkdir()
        (folder / 'cmdline').write_bytes(b'\0'.join(x.encode() for x in argv) + b'\0')
    rows, errors = m.scan_processes(tmp_path)
    assert rows == []
    assert errors == []


def test_direct_python_writer_is_detected_with_exact_argv(tmp_path):
    variants = [
        ('401', ['python3.11', '-B', '-m', 'scripts.coordination.control_plane.governed_worker_cycle', 'launch'], 'governed_worker_cycle'),
        ('402', ['/usr/bin/python3', 'scripts/coordination/control_plane/dispatch_intent.py', 'prepare'], 'dispatch_intent'),
        ('403', ['/repo/scripts/coordination/execution_attempt_ledger_v0_1.py', 'append'], 'execution_attempt_ledger'),
        ('404', ['python', '-m', 'scripts.coordination.control_plane.cf10_training_dispatch'], 'cf10_training_dispatch'),
    ]
    for pid, args, _ in variants:
        folder = tmp_path / pid
        folder.mkdir()
        (folder / 'cmdline').write_bytes(b'\0'.join(x.encode() for x in args) + b'\0')
    rows, errors = m.scan_processes(tmp_path)
    assert errors == []
    assert rows == [{'pid': int(pid), 'matching_terms': [term]} for pid, _, term in variants]


def test_entrypoint_mentioned_only_in_arguments_not_treated_as_executed():
    assert m.process_writer_terms([
        'python3', '-m', 'scripts.coordination.execution_attempt_writer_coverage_v0_1',
        '--report', '/tmp/governed_worker_cycle.py']) == []
    assert m.process_writer_terms([
        'python', 'ordinary_script.py', '--arg', 'scripts.coordination.control_plane.dispatch_intent']) == []


def test_real_writer_process_drift_remains_blocking(monkeypatch, tmp_path):
    patch_technical(monkeypatch)
    path = save(tmp_path, fixture_plan())
    monkeypatch.setattr(m, 'scan_processes', lambda *a, **k: (
        [{'pid': 510, 'matching_terms': ['dispatch_intent']}], []))
    result = m.check_plan(tmp_path, path, writer_release_root=tmp_path / "writer")
    assert result['status'] == 'BLOCKED'
    assert 'PROCESS_INVENTORY_CHANGED_REGENERATE_PLAN' in result['blockers']


def test_ast_local_workfront_history_append_is_not_execution_ledger(tmp_path):
    source = tmp_path / 'scripts/coordination/workfront_history_v0_1.py'
    source.parent.mkdir(parents=True)
    source.write_text('def append_record(root, record, store_override=None):\n    return root\n'
                      'def main(root, record):\n    return append_record(root, record)\n')
    rows, errors = m.scan_call_sites(tmp_path)
    assert errors == []
    assert rows == []


def test_ast_ledger_local_append_is_real_writer(tmp_path):
    source = tmp_path / 'scripts/coordination/execution_attempt_ledger_v0_1.py'
    source.parent.mkdir(parents=True)
    source.write_text('def append_record(root, record):\n    return root\n'
                      'def main(root, record):\n    return append_record(root, record)\n')
    rows, errors = m.scan_call_sites(tmp_path)
    assert errors == []
    assert rows == [{'file': str(source.relative_to(tmp_path)), 'line': 4,
                     'classification': 'EXECUTION_LEDGER_LOCAL_APPEND'}]


def test_ast_imported_ledger_aliases_resolve_to_writer(tmp_path):
    source = tmp_path / 'scripts/coordination/control_plane/use.py'
    source.parent.mkdir(parents=True)
    source.write_text(
        'from scripts.coordination import execution_attempt_ledger_v0_1 as ledger\n'
        'from scripts.coordination.execution_attempt_ledger_v0_1 import append_record as save\n'
        'def write():\n'
        '    ledger.append_record(1, 2)\n'
        '    save(1, 2)\n')
    rows, errors = m.scan_call_sites(tmp_path)
    assert errors == []
    assert [r['classification'] for r in rows] == [
        'EXECUTION_LEDGER_IMPORT_BOUND', 'EXECUTION_LEDGER_IMPORTED_APPEND']


def test_ast_history_module_alias_not_ledger_writer(tmp_path):
    source = tmp_path / 'scripts/coordination/control_plane/use.py'
    source.parent.mkdir(parents=True)
    source.write_text(
        'from scripts.coordination import workfront_history_v0_1 as history\n'
        'from scripts.coordination.workfront_history_v0_1 import append_record as save\n'
        'def write():\n    history.append_record(1, 2)\n    save(1, 2)\n')
    rows, errors = m.scan_call_sites(tmp_path)
    assert rows == [] and errors == []


def test_ast_unknown_dynamic_ledger_object_stays_under_review(tmp_path):
    source = tmp_path / 'scripts/coordination/control_plane/dispatch_intent.py'
    source.parent.mkdir(parents=True)
    source.write_text('def write(load_ledger):\n    ledger = load_ledger()\n'
                      '    ledger.append_record(1, 2)\n')
    rows, errors = m.scan_call_sites(tmp_path)
    assert errors == []
    assert rows[0]['classification'] == 'STATIC_CALLSITE_REQUIRES_REVIEW'


def test_resolved_systemd_aliases_deduplicated_and_scanned(tmp_path):
    base = tmp_path / 'systemd'
    base.mkdir()
    target = base / 'actual.service'
    target.write_text('ExecStart=python -m scripts.coordination.control_plane.dispatch_intent')
    (base / 'alias1.service').symlink_to(target)
    wants = base / 'multi-user.target.wants'
    wants.mkdir()
    (wants / 'alias2.service').symlink_to(target)
    rows, errors = m.scan_schedules((base,))
    assert errors == []
    assert rows == [{'path': str(target.resolve()), 'matching_terms': ['dispatch_intent']}]


def test_unresolved_or_out_of_scope_systemd_alias_requires_review(tmp_path):
    base = tmp_path / 'systemd'
    base.mkdir()
    (base / 'broken.service').symlink_to(base / 'missing.service')
    outside = tmp_path / 'out.service'
    outside.write_text('ExecStart=/bin/true')
    (base / 'external.service').symlink_to(outside)
    rows, errors = m.scan_schedules((base,))
    assert rows == []
    assert any('SCHEDULE_SYMLINK_UNREVIEWED:' + str(base / 'broken.service') == e for e in errors)
    assert any('SCHEDULE_SYMLINK_UNREVIEWED:' + str(base / 'external.service') == e for e in errors)


def test_safe_root_symlink_alias_does_not_duplicate_results(tmp_path):
    real = tmp_path / 'usr/systemd'
    real.mkdir(parents=True)
    (real / 'writer.service').write_text('ExecStart=python -m scripts.coordination.control_plane.governed_worker_cycle')
    alias = tmp_path / 'libsystemd'
    alias.symlink_to(real, target_is_directory=True)
    rows, errors = m.scan_schedules((alias, real))
    assert errors == []
    assert rows == [{'path': str((real / 'writer.service').resolve()), 'matching_terms': ['governed_worker_cycle']}]


def test_shadowed_history_import_is_not_silently_excluded(tmp_path):
    file = tmp_path / 'scripts/coordination/control_plane/mixed.py'
    file.parent.mkdir(parents=True)
    file.write_text('from scripts.coordination import workfront_history_v0_1 as history\n'
                    'def run(history):\n    return history.append_record(1, 2)\n')
    rows, errors = m.scan_call_sites(tmp_path)
    assert errors == []
    assert len(rows) == 1 and rows[0]['classification'] == 'STATIC_CALLSITE_REQUIRES_REVIEW'


def test_workfront_history_rebound_append_remains_review_candidate(tmp_path):
    file = tmp_path / 'scripts/coordination/workfront_history_v0_1.py'
    file.parent.mkdir(parents=True)
    file.write_text('def append_record(a):\n    return a\n'
                    'def run(append_record):\n    return append_record(1)\n')
    rows, errors = m.scan_call_sites(tmp_path)
    assert errors == []
    assert len(rows) == 1 and rows[0]['classification'] == 'STATIC_CALLSITE_REQUIRES_REVIEW'


def test_dual_release_plan_records_distinct_publications(monkeypatch, tmp_path):
    patch_technical(monkeypatch)
    result = m.build_plan(tmp_path, writer_release_root=tmp_path / "writer")
    assert result['schema_version'].endswith('_v0_2')
    assert result['gate_publication']['commit'] == 'a'*40
    assert result['writer_publication']['commit'] == m.PUBLISHED_COMMIT
    assert 'publication' not in result
    assert result['deployment_coverage_verified'] is False


def test_scan_writer_sources_not_gate_sources(monkeypatch, tmp_path):
    patch_technical(monkeypatch)
    seen = []
    monkeypatch.setattr(m, 'scan_call_sites', lambda root: (seen.append(root) or [], []))
    m.build_plan(tmp_path, writer_release_root=tmp_path / "writer")
    assert seen == [tmp_path / "writer"]


def test_legacy_v01_plan_is_rejected(monkeypatch, tmp_path):
    patch_technical(monkeypatch)
    plan = fixture_plan()
    plan['schema_version'] = 'forprint_execution_attempt_writer_deployment_evidence_v0_1'
    path = save(tmp_path, plan)
    with pytest.raises(m.CoverageBlocked, match='PLAN_NOT_CANONICAL'):
        m.check_plan(tmp_path, path, writer_release_root=tmp_path / "writer")


def test_gate_publication_binding_drift_rejected(monkeypatch, tmp_path):
    patch_technical(monkeypatch)
    plan = fixture_plan()
    plan['gate_publication']['commit'] = 'f'*40
    path = save(tmp_path, plan)
    with pytest.raises(m.CoverageBlocked, match='PLAN_GATE_PUBLICATION_BINDING_DRIFT'):
        m.check_plan(tmp_path, path, writer_release_root=tmp_path / "writer")


def test_writer_publication_binding_drift_rejected(monkeypatch, tmp_path):
    patch_technical(monkeypatch)
    plan = fixture_plan()
    plan['writer_publication']['commit'] = 'f'*40
    path = save(tmp_path, plan)
    with pytest.raises(m.CoverageBlocked, match='PLAN_WRITER_PUBLICATION_BINDING_DRIFT'):
        m.check_plan(tmp_path, path, writer_release_root=tmp_path / "writer")


def test_missing_gate_attestation_binding_blocks_verify(monkeypatch, tmp_path):
    patch_technical(monkeypatch)
    path = save(tmp_path, fixture_plan())
    doc = {'publication_commit': m.PUBLISHED_COMMIT, 'publication_remote': m.PUBLISHED_REMOTE,
           'publication_ref': m.PUBLISHED_REF, 'technical_evidence_sha256': m.sha(path.read_bytes()),
           'writer_entrypoints': list(m.REQUIRED)}
    monkeypatch.setattr(gate, 'trusted_json', lambda *a, **k: (doc, b''))
    monkeypatch.setattr(gate, 'validate_coverage', lambda *a, **k: None)
    got = m.verify_coverage(tmp_path, path, writer_release_root=tmp_path / "writer")
    assert got['status'] == 'BLOCKED'
    assert 'EXTERNAL_COVERAGE_BINDING_DRIFT:gate_publication_commit' in got['blockers']


def test_cli_requires_explicit_distinct_writer_release_root(monkeypatch, tmp_path, capsys):
    # argv is intentionally self-contained: no Git or /etc readback.
    with pytest.raises(SystemExit):
        m.main(['plan', '--root', str(tmp_path), '--report', 'tmp/test.json'])
    assert m.main(['plan', '--root', str(tmp_path), '--writer-release-root',
                   str(tmp_path), '--report', 'tmp/test.json']) == 2
    assert 'GATE_AND_WRITER_ROOT_MUST_DIFFER' in capsys.readouterr().out


def test_technical_ready_still_never_authorizes_activation(monkeypatch, tmp_path):
    patch_technical(monkeypatch)
    path = save(tmp_path, fixture_plan())
    check = m.check_plan(tmp_path, path, writer_release_root=tmp_path / "writer")
    assert check['deployment_coverage_verified'] is False
    assert check['status'] == 'READY_FOR_INDEPENDENT_REVIEW'
