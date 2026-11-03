"""CF10 r047: bind r046 claims to exact root-owned machine evidence bytes.

This is NOT an evidence issuer, attestor, launcher, authority or cutover.
Raw source records must be independently produced and reviewed; schema validity
alone is not evidence that an experiment actually occurred.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping

SCHEMA = 'cf10_r047_raw_pilot_source_v0_1'
STATUS = 'PASS_NON_AUTHORIZING_SOURCE_RECORD'

# Each raw source is outcome-specific, never a generic "tests passed" flag.
REQUIRED_OBSERVATIONS = {
    'DISPOSABLE_SYSTEMD_CONTROLLER_LOSS_RECOVERY': frozenset({
        'real_systemd_controller_sigkill_observed',
        'service_survived_controller_death',
        'recovery_without_terminal_witness_fail_closed',
        'automatic_retry_absent',
        'unit_retired_after_proof',
        'fixture_cleanup_verified',
    }),
    'TMP_UNAVAILABLE_END_TO_END': frozenset({
        'project_tmp_unavailable_during_disposable_execution',
        'disposable_execution_completed',
        'recovery_completed_without_project_tmp',
        'canonical_durable_state_independent_of_project_tmp',
        'project_tmp_unavailability_isolated_from_live_server',
    }),
    'INDEPENDENT_FINALIZER_GATE_FIXTURE': frozenset({
        'preterminal_root_claim_crosschecked',
        'kernel_systemd_readback_crosschecked',
        'candidate_result_independently_validated',
        'invalid_result_did_not_append_success_terminal',
        'immutable_terminal_replay_not_refinalized',
    }),
    'SOURCE_AND_WRITER_BOUNDARY': frozenset({
        'canonical_task70_and_work_front_bound',
        'published_head_and_frozen_source_equal',
        'writer_protocol_enforced',
        'one_shot_claim_unconsumed',
        'canonical_ledger_has_no_started_record_for_attempt',
        'cf10_systemd_quiescence_observed',
    }),
}


def raw_name(kind: str, attempt: str) -> str:
    """Canonical deterministic name in the existing root-owned release store."""
    from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as r046
    if kind not in r046.PROOF_TYPES or not isinstance(attempt, str) or r046.ATTEMPT.fullmatch(attempt) is None:
        raise ValueError('UNKNOWN_KIND_OR_ATTEMPT')
    return 'raw_source_' + r046._attempt_key(attempt) + '_' + kind.lower() + '.json'


def verify_source_record(raw: bytes, *, kind: str, head: str,
                         task: str, attempt: str, worker: str,
                         decode: Callable[[bytes], dict]) -> list[str]:
    """Strict bytes+scope+outcome check. Does not authenticate a producer."""
    errors: list[str] = []
    if kind not in REQUIRED_OBSERVATIONS:
        return ['RAW_SOURCE_KIND_UNKNOWN']
    try:
        doc = decode(raw)
    except (ValueError, TypeError, KeyError, RuntimeError):
        return ['RAW_SOURCE_INVALID_JSON_OR_DUPLICATE_KEYS:' + kind]
    if not isinstance(doc, Mapping):
        return ['RAW_SOURCE_NOT_OBJECT:' + kind]
    expected = {
        'schema_version': SCHEMA,
        'status': STATUS,
        'proof_type': kind,
        'source_head': head,
        'task_prompt_id': task,
        'attempt_id': attempt,
        'worker_id': worker,
        'production_worker_launched': False,
        'automatic_retry': False,
        'scope': ('READ_ONLY_EXACT_ATTEMPT' if kind == 'SOURCE_AND_WRITER_BOUNDARY'
                  else 'DISPOSABLE_NON_AUTHORIZING'),
    }
    if set(doc) != set(expected) | {'observations'}:
        errors.append('RAW_SOURCE_EXACT_FIELDS_REQUIRED:' + kind)
    for field, value in expected.items():
        if type(doc.get(field)) is not type(value) or doc.get(field) != value:
            errors.append('RAW_SOURCE_SCOPE_MISMATCH:' + kind + ':' + field)
    observations = doc.get('observations')
    if not isinstance(observations, Mapping) or set(observations) != REQUIRED_OBSERVATIONS[kind]:
        errors.append('RAW_SOURCE_EXACT_OBSERVATIONS_REQUIRED:' + kind)
    elif any(type(value) is not bool or value is not True for value in observations.values()):
        errors.append('RAW_SOURCE_UNVERIFIED_OUTCOME:' + kind)
    return sorted(set(errors))


def verify_sources(*, folder_fd: int, proofs: Mapping[str, Mapping],
                   head: str, task: str, attempt: str, worker: str,
                   read: Callable[[int, str], bytes],
                   decode: Callable[[bytes], dict]) -> list[str]:
    """Read the actual root-owned raw proof bytes, not a self-asserted SHA string.

    Neither this function nor its r046 caller creates any source evidence.
    The caller supplies the existing O_NOFOLLOW, root:root, 0600 dirfd reader.
    """
    from scripts.coordination.control_plane import cf10_r046_pilot_cutover_review_v0_1 as r046
    if not isinstance(proofs, Mapping) or set(proofs) != set(r046.PROOF_TYPES):
        return ['RAW_SOURCE_PROOFS_INCOMPLETE']
    errors: list[str] = []
    for kind in r046.PROOF_TYPES:
        try:
            raw = read(folder_fd, raw_name(kind, attempt))
        except (OSError, ValueError, TypeError, RuntimeError, KeyError):
            errors.append('RAW_SOURCE_NOT_AVAILABLE:' + kind)
            continue
        proof = proofs.get(kind)
        if not isinstance(proof, Mapping):
            errors.append('RAW_SOURCE_NO_BOUND_PROOF:' + kind)
            continue
        claimed_sha = proof.get('source_evidence_sha256')
        if not isinstance(claimed_sha, str) or hashlib.sha256(raw).hexdigest() != claimed_sha:
            errors.append('RAW_SOURCE_SHA256_MISMATCH:' + kind)
            continue
        errors.extend(verify_source_record(raw, kind=kind, head=head, task=task,
                                           attempt=attempt, worker=worker, decode=decode))
    return sorted(set(errors))
