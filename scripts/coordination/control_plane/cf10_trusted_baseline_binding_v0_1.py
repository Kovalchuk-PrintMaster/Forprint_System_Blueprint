"""Non-authorizing candidate binding of root-controlled baseline identifiers.

The function validates shape and deterministic equality only. Signatures,
filesystem ownership, replay protection, locked ledger and process exit
are distinct mandatory controls that this module DOES NOT implement.
"""
from __future__ import annotations
import hashlib
import json
import re

HEX64 = re.compile(r'^[0-9a-f]{64}$')
HEAD40 = re.compile(r'^[0-9a-f]{40}$')
TOKEN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]{4,127}$')

class BindingBlocked(ValueError):
    pass


def _check(v, r, code):
    if not isinstance(v,str) or r.fullmatch(v) is None:
        raise BindingBlocked('CF10_BINDING_'+code)


def assemble_binding(*, attempt_id: str, task_prompt_id: str,
                     source_head: str, handoff_sha256: str,
                     baseline_sha256: str) -> dict:
    _check(attempt_id,TOKEN,'ATTEMPT')
    _check(task_prompt_id,TOKEN,'TASK')
    _check(source_head,HEAD40,'HEAD')
    _check(handoff_sha256,HEX64,'HANDOFF')
    _check(baseline_sha256,HEX64,'BASELINE')
    fields={
        'schema':'cf10_non_authorizing_baseline_binding_v0_1',
        'attempt_id': attempt_id,
        'task_prompt_id': task_prompt_id,
        'source_head': source_head,
        'handoff_sha256': handoff_sha256,
        'baseline_sha256': baseline_sha256,
        'authorization_issued':False,
        'process_quiescence_proven':False,
        'promotion_allowed':False,
    }
    fields['content_sha256'] = hashlib.sha256(json.dumps(fields, sort_keys=True,
        separators=(',',':')).encode()).hexdigest()
    return fields


def match_binding(binding:dict, *, attempt_id:str,task_prompt_id:str,
                  source_head:str,handoff_sha256:str,baseline_sha256:str) -> bool:
    expected=assemble_binding(attempt_id=attempt_id,task_prompt_id=task_prompt_id,
        source_head=source_head,handoff_sha256=handoff_sha256,baseline_sha256=baseline_sha256)
    if binding != expected:
        raise BindingBlocked('CF10_BINDING_MISMATCH_OR_TAMPER')
    return True
