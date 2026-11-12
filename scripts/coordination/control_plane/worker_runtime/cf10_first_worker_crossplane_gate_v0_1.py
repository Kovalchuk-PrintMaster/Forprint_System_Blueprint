#!/usr/bin/env python3
"""Read-only first-Worker end-to-end cross-plane readiness gate.

Exercises CURRENT canonical training task lookup, Y source review, R129
11-step lifecycle fixture and patched canonical KernelWitness shape.
It NEVER grants a claim, releases a unit, executes inference or writes ledger.
The point is to detect actual cross-plane drift in one Make invocation rather
than issuing independent passes from unrelated test fixtures.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from collections.abc import Mapping

SCHEMA='cf10_ab_first_worker_crossplane_readiness_v0_1'
TASK='cf10-verification-tier-self-hardening-v0-1'
OPEN=['G1','G2','G3','G4','G5']

class JoinHold(ValueError):pass

def deny(k):raise JoinHold('CF10_AB_HOLD_'+k)
def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def digest(obj):return hashlib.sha256(canonical(obj)).hexdigest()

def check_join(*, task:Mapping, review:Mapping, lifecycle:Mapping,
               kernel_anchor_implemented:bool, backend_closed:bool)->dict:
    if (not isinstance(task,Mapping) or task.get('work_id')!='u180j' or
        task.get('module')!='forprint_system_blueprint' or
        task.get('task_prompt_id')!=TASK or task.get('candidate_only') is not True):
        deny('CANONICAL_TASK')
    if (not isinstance(review,Mapping) or review.get('all_gates_open') is not True or
        review.get('worker_launched') is not False or review.get('owner_authority_granted') is not False or
        review.get('terminal_ledger_written') is not False or
        set(review.get('gates',{}))!=set(OPEN)):
        deny('SOURCE_REVIEW_AUTHORITY')
    if (not isinstance(lifecycle,Mapping) or lifecycle.get('source_only_trace_valid') is not True or
        lifecycle.get('mode')!='SYNTHETIC_ONLY_NON_AUTHORIZING' or
        lifecycle.get('synthetic_event_count')!=11 or
        lifecycle.get('authority')!={
          'live_worker_allowed':False, 'claim_consumed':False,'root_release_granted':False,
          'automatic_retry':False,'tool_cancellation_attested':False,'g1_g5_closed':False}):
        deny('CANONICAL_LIFECYCLE')
    if kernel_anchor_implemented is not True or backend_closed is not True:
        deny('KERNEL_OR_BACKEND_UNVERIFIED')
    result={'schema':SCHEMA,'task_id':TASK,'module':'forprint_system_blueprint',
      'canonical_task_resolved':True,'canonical_prelaunch_review_passed':True,
      'canonical_synthetic_11_step_lifecycle_passed':True,
      'kernel_anchor_source_integrated':True,'worker_started':False,
      'auth_proven':False,'real_upstream_proven':False,'live_result_accepted':False,
      'real_worker_terminal_proven':False,'owner_claim_consumed':False,
      'dispatcher_mutated':False,'production_systemd_modified':False,
      'live_cutover_enabled':False,'gates_open':OPEN,
      'next_blockers':[
        'PROVIDER_AUTH_AND_CHILD_SECRET_NONEXPOSURE',
        'REAL_PROVIDER_DESTINATION_EGRESS',
        'CANONICAL_NEW_ATTEMPT_CLAIM_AND_WORKER_EXECUTION',
        'REAL_KERNEL_1_TO_0_AND_TERMINAL_LEDGER',
      ]}
    result['report_sha256']=digest(result)
    return result

def current_readonly(root:Path)->dict:
    from scripts.coordination.control_plane import cf10_training_dispatch as dispatch
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_r129_canonical_lifecycle_convergence_v0_1 as r129,
        cf10_first_worker_critical_path_v0_1 as y,
        cf10_systemd_launcher_v0_1 as launcher,
        cf10_systemd_kernel_witness_v0_1 as kernel)
    t=dispatch.resolve_training_task(root=root,task_prompt_id=TASK)
    c,events=r129.synthetic_fixture()
    trace=r129.convergence(c,events)
    return check_join(task=t,review=y.source_check(),lifecycle=trace,
        kernel_anchor_implemented='anchor_fd' in kernel.KernelWitness.__dataclass_fields__,
        backend_closed=launcher.LIVE_CUTOVER_ENABLED is False)

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['source-check'],required=True)
    p.add_argument('--root',default='/srv/software_development/forprint-project/forprint_system_blueprint')
    a=p.parse_args(argv)
    try:
        r=current_readonly(Path(a.root))
        print('CF10_AB='+ 'PASS_CANONICAL_CROSSPLANE_READONLY')
        print('CF10_AB_REPORT_SHA256='+r['report_sha256'])
        print('CF10_AB_G1_G5=OPEN_NO_LIVE_WORKER')
    except (JoinHold,KeyError,ValueError,TypeError,ImportError,AttributeError) as exc:
        print('CF10_AB=HOLD_'+type(exc).__name__)
        return 3
    return 0
if __name__=='__main__':raise SystemExit(main())
