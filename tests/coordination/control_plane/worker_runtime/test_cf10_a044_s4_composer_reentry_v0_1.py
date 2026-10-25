"""A044-shaped S4 regressions; synthetic data, no historical artifact mutation."""
from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.coordination.assistant_handoff_v2_freshness_resume_v0_1 import validate_resume
from scripts.coordination.control_plane.worker_runtime.s4_result_composer_v0_1 import (
    S4ResultComposerError, compose_s4_result_candidate,
)

ATTEMPT = 'cf10-u180j-a044'
ORIGIN_SHA = 'b' * 64
FINGERPRINT = 'a' * 64


def _origin():
    cursor = {
        'roadmap_sync': 'IN_SYNC',
        'roadmap_status': 'ROADMAP_STATUS=control_foundation_near_horizon:previous=CF-09:current=CF-10:next=CF-11:ready=CF-11',
        'open_work': {'u180j': {'state': 'ACTIVE', 'event_id': 'evt-u180j-activate-20260921t102955259861',
                               'event_type': 'WORK_ACTIVATED', 'sequence': 67}},
        'lifecycle_status_sha256': 'bf6fc3158f1607ef3be280618615cfe5f7865c385660022363e0483c01931c08',
        'roadmap_status_sha256': '6aa036e2f9e0fd1561d8a7692cc6225d966128ac0835b379e09c5ced1983749e',
    }
    manifest = {'handoff_manifest_sha256': ORIGIN_SHA, 'source_state_fingerprint': FINGERPRINT,
                'lifecycle_roadmap_cursor': cursor}
    governed = {
        'schema_version': 'forprint_governed_worker_context_projection_v0_1',
        'handoff_manifest_sha256': ORIGIN_SHA,
        'handoff_source_state_fingerprint': FINGERPRINT,
        'lifecycle_roadmap_cursor': deepcopy(cursor),
        'execution_bindings': {'attempt_id': ATTEMPT},
        'authority': {'context_grants_authority': False, 'dispatch_authority_granted': False,
                      'release_authority_granted': False, 'cross_repository_write_authority_granted': False},
    }
    return manifest, governed


def _worker_completion():
    return {
        'status': 'BLOCKED',
        'changed_paths': [],
        'validation_evidence': [{'check': 'validation suite', 'outcome': 'UNVERIFIED_BY_WORKER'}],
        'self_repair_attempts': [],
        'unresolved_findings': [{'code': 'VALIDATION_TOOL_RESULT_NOT_RETURNED', 'status': 'BLOCKED'}],
        'partial_resume': {'latest_completed_node': 'bounded_preflight_review',
                           'latest_accepted_ref': 'NONE_NO_MUTATION_OR_ARTIFACT_ACCEPTED',
                           'replay_forbidden_refs': ['u180j-preflight: do not replay or infer any project mutation; none was performed']},
    }


def test_a044_shapes_reproduce_original_two_failures():
    origin, _ = _origin()
    completion = _worker_completion()
    result = {
        'attempt_id': ATTEMPT, 'handoff_manifest_sha256': ORIGIN_SHA, 'status': 'BLOCKED',
        'resume_coordinates': {
            'attempt_id': ATTEMPT, 'handoff_manifest_sha256': ORIGIN_SHA,
            'source_state_fingerprint': FINGERPRINT,
            'lifecycle_roadmap_cursor': deepcopy(origin['lifecycle_roadmap_cursor']),
            'latest_completed_node': completion['partial_resume']['latest_completed_node'],
            'latest_accepted_ref': completion['partial_resume']['latest_accepted_ref'],
            'replay_forbidden_refs': [{'u180j-preflight': 'do not replay or infer any project mutation; none was performed'}],
        },
    }
    result['resume_coordinates']['lifecycle_roadmap_cursor']['roadmap_status_sha256'] = (
        '6aa036e2f9e0fd1561d8d7692cc6225d966128ac0835b379e09c5ced1983749e'
    )
    codes = {x['code'] for x in validate_resume(result, origin)}
    assert codes == {'STALE_LIFECYCLE_ROADMAP_CURSOR', 'RESUME_COORDINATES_INCOMPLETE'}


def test_composer_binds_exact_origin_without_worker_retyping():
    origin, governed = _origin()
    original = deepcopy((origin, governed))
    result = compose_s4_result_candidate(
        origin_manifest=origin, governed_worker_context=governed,
        expected_attempt_id=ATTEMPT, worker_completion=_worker_completion(),
    )
    assert validate_resume(result, origin) == []
    assert result['status'] == 'BLOCKED'
    assert result['changed_paths'] == []
    assert result['resume_coordinates']['lifecycle_roadmap_cursor'] == origin['lifecycle_roadmap_cursor']
    assert isinstance(result['resume_coordinates']['replay_forbidden_refs'][0], str)
    assert (origin, governed) == original


def test_composer_refuses_worker_supplied_immutable_cursor():
    origin, governed = _origin()
    draft = _worker_completion()
    draft['resume_coordinates'] = {'lifecycle_roadmap_cursor': origin['lifecycle_roadmap_cursor']}
    with pytest.raises(S4ResultComposerError, match='strict field contract'):
        compose_s4_result_candidate(origin_manifest=origin, governed_worker_context=governed,
                                    expected_attempt_id=ATTEMPT, worker_completion=draft)


def test_composer_refuses_yaml_map_instead_of_replay_string():
    origin, governed = _origin()
    draft = _worker_completion()
    draft['partial_resume']['replay_forbidden_refs'] = [{'u180j-preflight': 'no replay'}]
    with pytest.raises(S4ResultComposerError, match='non-empty list'):
        compose_s4_result_candidate(origin_manifest=origin, governed_worker_context=governed,
                                    expected_attempt_id=ATTEMPT, worker_completion=draft)


def test_composer_refuses_forged_frozen_origin():
    origin, governed = _origin()
    governed['handoff_manifest_sha256'] = 'f' * 64
    with pytest.raises(S4ResultComposerError, match='origin Handoff'):
        compose_s4_result_candidate(origin_manifest=origin, governed_worker_context=governed,
                                    expected_attempt_id=ATTEMPT, worker_completion=_worker_completion())
