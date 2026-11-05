"""R086 exact operator-plan provenance through ACK / dispatch / preclaim.

Only an R085 explicit operator preview carries this digest. Missing markers on
ordinary, source-controlled Copilot attempts preserve existing R082/R083 gates.
No selection creates authorization, launch, claim, retry or ledger writes.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import hashlib
import re

from scripts.coordination.control_plane.worker_runtime import (
    cf10_r084_operator_assignment_plan_v0_1 as plan,
    cf10_r082_frozen_assignment_v0_1 as frozen,
)

SCHEMA = 'cf10_r086_operator_provenance_v0_1'
KEY = 'cf10_operator_assignment_preview_sha256'
DECISION_KEY = 'cf10_operator_assignment_preview_sha256'
HEX64 = re.compile(r'[a-f0-9]{64}\Z')


class OperatorProvenanceBlocked(ValueError):
    pass


def deny(code: str) -> None:
    raise OperatorProvenanceBlocked('CF10_R086_' + code)


def _verified_sha(value: object) -> str:
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        deny('OPERATOR_PREVIEW_SHA_REQUIRED')
    return value


def verify_prepared(*, root: Path, prepared: Mapping, source_state: Mapping,
                    attempt_id: str, worker_id: str) -> str | None:
    """Rebuild R084 preview from trusted R082 selection, no attacker plan input.

    An absence means the existing nonoperator Copilot prepare route; an empty,
    malformed or tampered explicit marker never gets interpreted as absence.
    """
    if not isinstance(prepared, Mapping) or not isinstance(source_state, Mapping):
        deny('PREPARED_OR_SOURCE_NOT_MAPPING')
    if KEY not in prepared:
        return None
    observed = _verified_sha(prepared[KEY])
    binding = prepared.get('cf10_training_binding')
    if not isinstance(binding, Mapping):
        deny('CANONICAL_TASK_BINDING_MISSING')
    assignment = prepared.get(frozen.KEY)
    if not isinstance(assignment, Mapping):
        deny('FROZEN_ASSIGNMENT_MISSING')
    head = source_state.get('git_head')
    fingerprint = source_state.get('fingerprint_sha256')
    selected = frozen.verify_prepared(
        root=Path(root), prepared=prepared, assignment=assignment,
        source_head=head, source_fingerprint=fingerprint,
        attempt_id=attempt_id, worker_id=worker_id,
    )
    if (selected.get('provider_id') != frozen.CURRENT_PILOT_PROVIDER
            or selected.get('model_id') != frozen.CURRENT_PILOT_MODEL):
        deny('NON_COPILOT_OPERATOR_DISPATCH_STILL_BLOCKED')
    rebuilt = plan.build_preview(
        root=Path(root), task_binding=binding, source_state=source_state,
        attempt_id=attempt_id, worker_id=worker_id,
        provider_id=selected['provider_id'], model_id=selected['model_id'],
    )
    if (observed != rebuilt.get('preview_sha256')
            or rebuilt.get('catalog_candidate') != selected.get('catalog_candidate')
            or rebuilt.get('candidate_only') is not True
            or rebuilt.get('eligible_for_live_dispatch') is not False):
        deny('OPERATOR_SELECTION_PROVENANCE_DRIFT')
    return observed


def verify_ack(*, prepared: Mapping, ready: Mapping) -> bool:
    """Reject an inserted/removed/changed operator marker across CF09 ACK."""
    if not isinstance(prepared, Mapping) or not isinstance(ready, Mapping):
        deny('ACK_INPUT_MAPPING_REQUIRED')
    if (KEY in prepared) != (KEY in ready):
        deny('ACK_OPERATOR_MARKER_PRESENCE_DRIFT')
    if KEY in prepared:
        if _verified_sha(prepared[KEY]) != ready.get(KEY):
            deny('ACK_OPERATOR_PREVIEW_SHA_DRIFT')
    return True


def verify_decision(*, root: Path, prepared: Mapping, decision: Mapping,
                    source_state: Mapping, attempt_id: str, worker_id: str) -> dict:
    """One exact operator digest required in hashed dispatch decision if selected.

    Called by explicit dispatch and the R083 epoch gate before owner claim and
    at launch. Does not validate the owner's independent launch authority.
    """
    if not isinstance(decision, Mapping):
        deny('DISPATCH_DECISION_MAPPING_REQUIRED')
    binding = decision.get('binding')
    if not isinstance(binding, Mapping):
        deny('DISPATCH_BINDING_MAPPING_REQUIRED')
    observed = verify_prepared(
        root=Path(root), prepared=prepared, source_state=source_state,
        attempt_id=attempt_id, worker_id=worker_id,
    )
    if observed is None:
        if DECISION_KEY in binding:
            deny('INJECTED_OPERATOR_DECISION_MARKER')
        return {
            'schema_version': SCHEMA,
            'operator_provenance_present': False,
            'operator_provenance_verified': False,
            'launch_authorized': False,
            'worker_launched': False,
            'automatic_fallback': False,
        }
    if (binding.get(DECISION_KEY) != observed
            or binding.get('attempt_id') != attempt_id
            or binding.get('worker_id') != worker_id):
        deny('DISPATCH_OPERATOR_PROVENANCE_DRIFT')
    selection = prepared[frozen.KEY]
    if (binding.get('runtime_provider') != selection.get('provider_id')
            or binding.get('runtime_model') != selection.get('model_id')
            or binding.get('cf10_frozen_provider_assignment_sha256') !=
                selection.get('frozen_assignment_sha256')):
        deny('DISPATCH_OPERATOR_FROZEN_PROVIDER_DRIFT')
    return {
        'schema_version': SCHEMA,
        'operator_provenance_present': True,
        'operator_provenance_verified': True,
        'operator_preview_sha256': observed,
        'launch_authorized': False,
        'worker_launched': False,
        'automatic_fallback': False,
    }
