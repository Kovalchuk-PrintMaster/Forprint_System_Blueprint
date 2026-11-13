"""R082: frozen per-attempt provider binding from trusted source + R080 catalog.

Provider selection is NOT authorization. Only existing Copilot CF10 pilot can
pass the current source-controlled dispatch/launch gates. The assignment must be
captured before ACK and repeated as an exact value through dispatch.
"""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
import re
from pathlib import Path

from scripts.coordination.control_plane.worker_runtime import registry
from scripts.coordination.control_plane.worker_runtime import cf10_r080_catalog_assignment_v0_1 as catalog

SCHEMA='cf10_r082_frozen_provider_assignment_v0_1'
KEY='cf10_frozen_provider_assignment_v0_1'
HEX64=re.compile(r'[0-9a-f]{64}\Z')
HEAD=re.compile(r'[0-9a-f]{40}\Z')
CURRENT_PILOT_PROVIDER='github_copilot_cli'
CURRENT_PILOT_MODEL='auto'
CAPABILITIES=['completion_capture','non_interactive_prompt']

class FrozenAssignmentBlocked(ValueError): pass

def deny(code): raise FrozenAssignmentBlocked('CF10_R082_'+code)

def digest(data:Mapping)->str:
    return hashlib.sha256(json.dumps(dict(data),sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()

def _source(root:Path,provider:str,model:str):
    selected=registry.resolve_default_runtime(root)
    if selected['provider_id']!=provider or selected['model_id']!=model:
        deny('SELECTED_PROVIDER_DIFFERS_FROM_SOURCE_CONTROLLED_DEFAULT')
    # Current pilot remains Copilot-only even if another provider is READY.
    if provider!=CURRENT_PILOT_PROVIDER or model!=CURRENT_PILOT_MODEL:
        deny('NON_COPILOT_PILOT_STILL_BLOCKED')
    return selected

def create(*,root:Path,task_id:str,work_front_id:str,worker_id:str,attempt_id:str,
           source_head:str,source_fingerprint:str,handoff_sha256:str)->dict:
    root=Path(root)
    if not isinstance(source_head,str) or not HEAD.fullmatch(source_head):deny('HEAD_INVALID')
    if not isinstance(source_fingerprint,str) or not HEX64.fullmatch(source_fingerprint):deny('SOURCE_FINGERPRINT')
    if not isinstance(handoff_sha256,str) or not HEX64.fullmatch(handoff_sha256):deny('HANDOFF_SHA256')
    selected=registry.resolve_default_runtime(root)
    provider=selected['provider_id'];model=selected['model_id']
    _source(root,provider,model)
    request={'attempt_id':attempt_id,'source_head':source_head,'worker_id':worker_id,
             'task_id':task_id,'work_front_id':work_front_id,'provider_id':provider,
             'model_id':model,'capabilities_required':list(CAPABILITIES)}
    choice=catalog.choose_attempt_candidate(root,request)
    if choice['provider_id']!=provider or choice['model_id']!=model or choice['live_dispatch_wired'] is not False:
        deny('CATALOG_CANDIDATE_UNEXPECTED')
    body={'schema_version':SCHEMA,'attempt_id':attempt_id,'worker_id':worker_id,
          'task_id':task_id,'work_front_id':work_front_id,'source_head':source_head,
          'source_state_fingerprint_sha256':source_fingerprint,
          'handoff_manifest_sha256':handoff_sha256,'provider_id':provider,'model_id':model,
          'catalog_candidate':choice,
          'selection_is_dispatch_authority':False,'automatic_fallback':False,
          'worker_launched':False,'owner_claim_consumed':False}
    return {**body,'frozen_assignment_sha256':digest(body)}

def verify(*,root:Path,assignment:Mapping,task_id:str,work_front_id:str,worker_id:str,
           attempt_id:str,source_head:str,source_fingerprint:str,handoff_sha256:str)->dict:
    if not isinstance(assignment,Mapping) or assignment.get('schema_version')!=SCHEMA:
        deny('FROZEN_SCHEMA_MISSING')
    actual=dict(assignment)
    proof=actual.pop('frozen_assignment_sha256',None)
    if not isinstance(proof,str) or not HEX64.fullmatch(proof) or digest(actual)!=proof:
        deny('FROZEN_CONTENT_DIGEST')
    expected=create(root=root,task_id=task_id,work_front_id=work_front_id,
                    worker_id=worker_id,attempt_id=attempt_id,
                    source_head=source_head,source_fingerprint=source_fingerprint,
                    handoff_sha256=handoff_sha256)
    if dict(assignment)!=expected:deny('FROZEN_SOURCE_OR_ATTEMPT_DRIFT')
    catalog.validate_candidate_against_current_catalog(Path(root),assignment['catalog_candidate'])
    if any(assignment.get(k) is not False for k in
           ('selection_is_dispatch_authority','automatic_fallback','worker_launched','owner_claim_consumed')):
        deny('AUTHORITY_WIDENING')
    return expected

def verify_prepared(*,root:Path,prepared:Mapping,assignment:Mapping,
                    source_head:str,source_fingerprint:str,attempt_id:str,worker_id:str)->dict:
    b=prepared.get('cf10_training_binding')
    if not isinstance(b,Mapping):deny('TRAINING_BINDING_MISSING')
    return verify(root=root,assignment=assignment,
                  task_id=b.get('task_prompt_id'),work_front_id=b.get('work_front_id'),
                  worker_id=worker_id,attempt_id=attempt_id,
                  source_head=source_head,source_fingerprint=source_fingerprint,
                  handoff_sha256=prepared.get('handoff_manifest_sha256'))

def verify_decision(*,root:Path,prepared:Mapping,decision:Mapping,
                    source_head:str,source_fingerprint:str,attempt_id:str,worker_id:str)->dict:
    binding=decision.get('binding')
    if not isinstance(binding,Mapping):deny('DECISION_BINDING_MISSING')
    frozen=prepared.get(KEY)
    if frozen is None:
        # Backward-compatible only with an already-made historic Copilot
        # decision. No other provider can use this path.
        if (binding.get('runtime_provider')!=CURRENT_PILOT_PROVIDER
                or binding.get('runtime_model')!=CURRENT_PILOT_MODEL
                or 'cf10_frozen_provider_assignment_sha256' in binding):
            deny('LEGACY_BINDING_NOT_PERMITTED')
        return {'legacy_copilot_only':True,'new_assignment_verified':False}
    verified=verify_prepared(root=root,prepared=prepared,assignment=frozen,
                    source_head=source_head,source_fingerprint=source_fingerprint,
                    attempt_id=attempt_id,worker_id=worker_id)
    if (binding.get('runtime_provider')!=verified['provider_id']
        or binding.get('runtime_model')!=verified['model_id']
        or binding.get('cf10_frozen_provider_assignment_sha256')!=verified['frozen_assignment_sha256']):
        deny('DECISION_FROZEN_BINDING_DRIFT')
    return {'legacy_copilot_only':False,'new_assignment_verified':True,
            'frozen_assignment_sha256':verified['frozen_assignment_sha256']}
