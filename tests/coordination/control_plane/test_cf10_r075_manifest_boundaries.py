"""R075: R013/backend/gate parity; never launch Worker or consume a claim."""
from __future__ import annotations
import json
from pathlib import Path
from unittest.mock import patch
import pytest
from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as r013
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_gate_entry_v0_1 as gate
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend

ATT='cf10-u180j-a054'
RUNTIME='/srv/software_development/forprint-worker-runtime'

def specimen(argv):
    return r013.BoundedInput(
        task_prompt_id='cf10-validation-check-pipeline-profile-and-optimization-v0-1',
        attempt_id=ATT,source_head='a'*40,handoff_sha256='b'*64,
        baseline_sha256='c'*64,
        workspace=f'{RUNTIME}/forprint_system_blueprint/worker-01/{ATT}/workspace/repo',
        runtime_root=RUNTIME,argv=tuple(argv),timeout_seconds=180)

def test_real_multiline_copilot_prompt_matches_isolated_gate():
    argv=['/usr/bin/env','-p','First line\n'+'x'*32000,
          '--additional-mcp-config','{"mcpServers":{"a":"'+ 'z'*2500 +'"}}']
    spec=specimen(argv)
    plan=r013.bind_plan(spec)
    assert r013.validate_plan(plan,spec)
    assert gate.validate_manifest_argv(list(spec.argv)) is True
    manifest=backend._manifest(spec,plan['identity']['unit'],'0'*64,1760000000.1)
    assert len(manifest)>16384
    assert len(manifest)<=backend.MANIFEST_MAX_BYTES==gate.MANIFEST_MAX_BYTES
    assert json.loads(manifest)['argv']==argv

@pytest.mark.parametrize('newline_count,expected_relation', [
    (65000, 'WITHIN_CAP_BUT_OUTSIDE_SAFETY_MARGIN'),
    (65536, 'OVER_GATE_CAP'),
])
def test_actual_manifest_budget_capped_for_json_escaping(newline_count, expected_relation):
    # R013 accepts both prompt lengths, but serialized JSON doubles newline bytes.
    # The preclaim margin must also reject a value slightly below the hard gate cap.
    argv=['/usr/bin/env','-p','\n'*newline_count]
    spec=specimen(argv)
    plan=r013.bind_plan(spec)
    manifest_size=len(backend._manifest(spec,plan['identity']['unit'],'0'*64,1760000000.1))
    if expected_relation == 'OVER_GATE_CAP':
        assert manifest_size > gate.MANIFEST_MAX_BYTES
    else:
        assert gate.MANIFEST_MAX_BYTES-512 < manifest_size <= gate.MANIFEST_MAX_BYTES
    with (patch.object(backend,'_root_directory') as root_check,
          patch.object(backend,'_runner_account') as runner,
          patch.object(backend,'build_command') as build):
        with pytest.raises(backend.SystemdLaunchBlocked,match='FROZEN_MANIFEST_TOO_LARGE_BEFORE_CLAIM'):
            backend.assert_frozen_manifest_preclaim(spec,plan)
        root_check.assert_not_called()
        runner.assert_not_called()
        build.assert_not_called()

def test_prompt_limit_and_mcp_limit_mirror_r013():
    cases=[
        ['/usr/bin/env','-p','\n'+'q'*65534],
        ['/usr/bin/env','--prompt','line1\nline2'],
        ['/usr/bin/env','-p','ok','--additional-mcp-config','{'+'x'*8000+'}'],
    ]
    for argv in cases:
        spec=specimen(argv)
        assert r013.validate_plan(r013.bind_plan(spec),spec)
        assert gate.validate_manifest_argv(argv) is True

def test_reject_unbounded_or_multiline_nonprompt():
    for argv in (
        ['/usr/bin/env','-p','x'*65537],
        ['/usr/bin/env','--model','bad\nline'],
        ['/usr/bin/env','--model','x'*2001],
        ['/usr/bin/env','-p','nul\x00inside'],
        ['/usr/bin/env','-p','cr\rinside'],
        ['/usr/bin/env','-p','p','--additional-mcp-config','x'*8193],
    ):
        with pytest.raises((r013.BoundaryBlocked,gate.GateBlocked)):
            # Both guards must reject; do not count a single failure as parity.
            r013.bind_plan(specimen(argv))
        with pytest.raises(gate.GateBlocked):
            gate.validate_manifest_argv(argv)

def test_source_must_preclaim_backend_budget_before_owner_claim():
    root=Path(__file__).resolve().parents[3]
    src=(root/'scripts/coordination/control_plane/cf10_pilot_cycle_v0_1.py').read_text()
    assert 'backend.assert_frozen_manifest_preclaim(spec, systemd_plan)' in src
    owner=(root/'scripts/coordination/control_plane/cf10_owner_pam_launch_v0_1.py').read_text()
    assert owner.index('pilot_cycle.assert_owner_preclaim_runtime(') < owner.index('_owner_claim(PROJECT,')

def test_sandbox_gate_is_standalone_and_signed_release_unchanged():
    root=Path(__file__).resolve().parents[3]
    gate_src=(root/'scripts/coordination/control_plane/worker_runtime/cf10_systemd_gate_entry_v0_1.py').read_text()
    assert 'from scripts.' not in gate_src
    assert 'os.execv(' in gate_src
    assert 'time.time()' in gate_src
    assert 'LIVE_CUTOVER_ENABLED=False' in (root/'scripts/coordination/control_plane/worker_runtime/cf10_systemd_launcher_v0_1.py').read_text()

def test_operator_doctor_and_abs_root_are_canonical_make_targets():
    root=Path(__file__).resolve().parents[3]
    make=(root/'Makefile').read_text()
    assert 'CF10_PILOT_ARGS = --root "$(CURDIR)"' in make
    assert 'cf10-pilot-operator-doctor:' in make
    assert 'cf10-pilot-launch-once:' in make
    assert '--launch-once' in make
