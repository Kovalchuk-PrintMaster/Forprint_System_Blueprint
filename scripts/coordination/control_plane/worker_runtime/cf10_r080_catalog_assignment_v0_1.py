"""CF10 R080: multi-READY catalog reader + explicit attempt selection, not dispatch.

All output is a candidate with source/catalog digests. It never freezes an
attempt, changes the selected provider in a live attempt, supplies secrets,
authorizes a launch, opens an operator claim, or executes a Worker.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from collections.abc import Mapping

from scripts.coordination.control_plane.worker_runtime import registry
from scripts.coordination.control_plane.worker_runtime import cf10_provider_neutral_boundary_v0_1 as neutral

SCHEMA = 'cf10_r080_attempt_provider_catalog_binding_v0_1'
INSPECT_SCHEMA = 'cf10_r080_multi_ready_registry_review_v0_1'
CATALOG_PATH = Path('coordination/registry/worker_runtime_adapters_v0_1.yaml')
CONFIG_PATH = Path('config/worker_runtime.yaml')

class AssignmentBlocked(RuntimeError):
    pass


def deny(code: str) -> None:
    raise AssignmentBlocked('CF10_R080_' + code)


def _json_bytes(value: Mapping) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def _digest(value: Mapping) -> str:
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def _file_sha(root: Path, relative: Path) -> str:
    p = root / relative
    if p.is_symlink() or not p.is_file():
        deny('SOURCE_FILE_MISSING_OR_SYMLINK:' + str(relative))
    return hashlib.sha256(p.read_bytes()).hexdigest()


def inspect_catalog(root: Path) -> dict:
    """Live Registry semantics, without creating a second READY provider."""
    catalog = registry.load_runtime_registry(root)
    declared = neutral.validate_registry_for_future(catalog)
    default = registry.resolve_default_runtime(root)
    ids = sorted(p['provider_id'] for p in declared)
    if default['provider_id'] not in ids or not ids:
        deny('DEFAULT_NOT_EXPLICIT_READY')
    return {
        'schema_version': INSPECT_SCHEMA,
        'status': 'MULTI_READY_REGISTRY_VALID_DEFAULT_COPILOT_DISPATCH_GUARDED',
        'ready_provider_ids': ids,
        'ready_provider_count': len(ids),
        'default_provider_id': default['provider_id'],
        'default_model_id': default['model_id'],
        'registry_sha256': _file_sha(root, CATALOG_PATH),
        'runtime_config_sha256': _file_sha(root, CONFIG_PATH),
        'candidate_only': True,
        'second_provider_ready_or_launched': False,
        'live_dispatch_provider_selection_wired': False,
        'automatic_fallback': False,
        'worker_launched': False,
        'claim_consumed': False,
        'ledger_written': False,
        'authorization_granted': False,
    }


def choose_attempt_candidate(root: Path, request: Mapping) -> dict:
    """Never implicitly select a default or use provider readiness as authority.

    The canonical published source/attempt freeze is a later trusted boundary.
    Catalog/config digests allow that later boundary to reject silent rebinding.
    """
    catalog = registry.load_runtime_registry(root)
    neutral.validate_registry_for_future(catalog)
    default = registry.resolve_default_runtime(root)
    if not isinstance(request, Mapping):
        deny('REQUEST_MAPPING_REQUIRED')
    try:
        chosen = neutral.select_candidate(catalog=catalog, request=request)
    except neutral.ProviderBoundaryBlocked as exc:
        raise AssignmentBlocked('CF10_R080_PROVIDER_SELECTION_BLOCKED:' + str(exc)) from exc
    selected_provider = next((p for p in catalog['providers'] if p['provider_id'] == chosen['provider_id']), None)
    if not isinstance(selected_provider, dict):
        deny('SELECTED_PROVIDER_DESCRIPTOR_MISSING')
    # The live default remains an independently configured selection: it cannot
    # silently turn into the requested nondefault provider.
    result = {
        **chosen,
        'schema_version': SCHEMA,
        'neutral_selection_schema_version': chosen['schema_version'],
        'registry_sha256': _file_sha(root, CATALOG_PATH),
        'runtime_config_sha256': _file_sha(root, CONFIG_PATH),
        'selected_provider_descriptor_sha256': _digest(selected_provider),
        'legacy_default_provider_id': default['provider_id'],
        'legacy_default_model_id': default['model_id'],
        'live_dispatch_wired': False,
        'candidate_only': True,
        'provider_ready_is_not_execution_authority': True,
        'provider_credentials_verified': False,
        'worker_launched': False,
        'owner_claim_consumed': False,
        'automatic_fallback': False,
        'automatic_retry': False,
        'authorization_granted': False,
        'result_accepted': False,
    }
    result['catalog_binding_sha256'] = _digest(result)
    return result


def validate_candidate_against_current_catalog(root: Path, candidate: Mapping) -> bool:
    """Reject missing/mutated source or candidate before any future use.

    Does not validate frozen HEAD or confer execution authorization.
    """
    if not isinstance(candidate, Mapping) or candidate.get('schema_version') != SCHEMA:
        deny('BINDING_SCHEMA')
    digest = candidate.get('catalog_binding_sha256')
    body = dict(candidate)
    body.pop('catalog_binding_sha256', None)
    if digest != _digest(body):
        deny('CANDIDATE_CONTENT_TAMPER')
    if candidate.get('registry_sha256') != _file_sha(root, CATALOG_PATH):
        deny('CATALOG_DRIFT')
    if candidate.get('runtime_config_sha256') != _file_sha(root, CONFIG_PATH):
        deny('RUNTIME_CONFIG_DRIFT')
    # Extra validation rejects a changed selected provider descriptor even if
    # caller gives an otherwise well-shaped mapping with a stale digest.
    catalog = registry.load_runtime_registry(root)
    selected = next((p for p in catalog['providers'] if p['provider_id'] == candidate.get('provider_id')), None)
    if not isinstance(selected, dict) or _digest(selected) != candidate.get('selected_provider_descriptor_sha256'):
        deny('PROVIDER_DESCRIPTOR_DRIFT')
    if candidate.get('candidate_only') is not True or candidate.get('authorization_granted') is not False:
        deny('AUTHORITY_WIDENED')
    if candidate.get('live_dispatch_wired') is not False or candidate.get('worker_launched') is not False:
        deny('LIVE_EXECUTION_WIDENED')
    if candidate.get('owner_claim_consumed') is not False or candidate.get('automatic_fallback') is not False:
        deny('CLAIM_OR_FALLBACK_WIDENED')
    # A content digest can be recomputed by an untrusted caller. Recreate the
    # exact deterministic candidate from the current trusted catalog as well.
    requested_keys = (
        'attempt_id', 'source_head', 'worker_id', 'task_id', 'work_front_id',
        'provider_id', 'model_id', 'capabilities_required',
    )
    request = {key: candidate.get(key) for key in requested_keys}
    try:
        expected = choose_attempt_candidate(root, request)
    except (AssignmentBlocked, neutral.ProviderBoundaryBlocked) as exc:
        raise AssignmentBlocked('CF10_R080_REBIND_SELECTION_BLOCKED') from exc
    if dict(candidate) != expected:
        deny('CANDIDATE_NOT_REPRODUCIBLE')
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mode', choices=('inspect',), required=True)
    ap.add_argument('--root', type=Path, required=True)
    args = ap.parse_args(argv)
    try:
        print(json.dumps(inspect_catalog(args.root), sort_keys=True, ensure_ascii=False, indent=2))
    except (AssignmentBlocked, registry.RuntimeRegistryError, neutral.ProviderBoundaryBlocked,
            OSError, ValueError, TypeError, KeyError) as exc:
        print('CF10_R080_BLOCKED=' + type(exc).__name__ + ':' + str(exc)[:180])
        print('CF10_R080_NO_WORKER_NO_CLAIM=true')
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
