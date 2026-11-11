#!/usr/bin/env python3
"""CF10 V: independent lab terminal-coherence fence (not a kernel observer).

Only canonical root-side KernelWitness can supply the kernel observation.
This function never treats process exit, MainPID 0, a synthetic record, or a
lab PASS as G5 proof for a real Worker. No root/systemd mutation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from collections.abc import Mapping

SCHEMA='cf10_terminal_proof_fence_v0_1'
UNIT=re.compile(r'forprint-cf10-(?:batch[a-z]|worker)-[0-9a-f]{16,24}\.service\Z')
SHA=re.compile(r'[0-9a-f]{64}\Z')
INV=re.compile(r'[0-9a-f]{32}\Z')
OPEN_GATES=['G1','G2','G3','G4','G5']
class TerminalHold(ValueError):pass
def deny(s):raise TerminalHold('CF10_V_TERMINAL_HOLD_'+s)
def _exact(value,required,label):
    if not isinstance(value,Mapping) or set(value)!=set(required):deny(label+'_SHAPE')
    return value

def coherent_lab(*, start:Mapping, kernel:Mapping, retained:Mapping, final:Mapping, context:Mapping):
    _exact(context,{'unit','invocation_id','attachment_sha256','attempt_id','worker_claim_consumed'},'CONTEXT')
    unit=context['unit'];inv=context['invocation_id'];attach=context['attachment_sha256']
    if (type(unit) is not str or UNIT.fullmatch(unit) is None or
        type(inv) is not str or INV.fullmatch(inv) is None or
        type(attach) is not str or SHA.fullmatch(attach) is None or
        type(context['attempt_id']) is not str or not context['attempt_id'] or
        context['worker_claim_consumed'] is not False):deny('CONTEXT_ID')
    _exact(start,{'unit','invocation_id','main_pid','uid','gid','state'},'START')
    if (start['unit']!=unit or start['invocation_id']!=inv or
        type(start['main_pid']) is not int or start['main_pid']<2 or
        start['uid']!=996 or start['gid']!=992 or start['state']!='active/running'):
        deny('START_IDENTITY')
    _exact(kernel,{'unit','invocation_id','observation','samples','arm_pid'},'KERNEL')
    if (kernel['unit']!=unit or kernel['invocation_id']!=inv or
        kernel['observation']!='PINNED_FD_READ' or kernel['samples']!=['1','0'] or
        kernel['arm_pid']!=start['main_pid']):deny('KERNEL_1_TO_0_UNPROVEN')
    _exact(retained,{'unit','invocation_id','active','substate','main_pid',
                     'result','exec_main_status','exit_type','remain_after_exit'},'RETAINED')
    if (retained['unit']!=unit or retained['invocation_id']!=inv or
        retained['active']!='active' or retained['substate']!='exited' or
        retained['main_pid']!=0 or retained['result']!='success' or
        retained['exec_main_status']!=0 or retained['exit_type']!='cgroup' or
        retained['remain_after_exit'] is not True):deny('RETAINED_TERMINAL')
    _exact(final,{'unit','stop_rc','active','main_pid','result'},'POSTSTOP')
    if (final['unit']!=unit or final['stop_rc']!=0 or final['active']!='inactive' or
        final['main_pid']!=0 or final['result']!='success'):deny('FINAL_READBACK')
    row={'schema':SCHEMA,'lab_kernel_terminal_confirmed':True,
         'observed_unit':unit,'invocation_id':inv,'attachment_sha256':attach,
         'kernel_samples':['1','0'],'kernel_read':'PINNED_FD_READ',
         'retained_before_stop':True,'poststop_inactive':True,
         'live_worker_kernel_terminal_proven':False,'provider_auth_used':False,
         'claim_consumed':False,'terminal_ledger_written':False,
         'gates_open':OPEN_GATES,'automatic_retry':False}
    row['report_sha256']=hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')).hexdigest()
    return row

def fixture():
    unit='forprint-cf10-batchv-'+'a'*16+'.service'; inv='b'*32
    ctx={'unit':unit,'invocation_id':inv,'attachment_sha256':'c'*64,
         'attempt_id':'cf10-u180j-a055','worker_claim_consumed':False}
    return dict(context=ctx,
       start={'unit':unit,'invocation_id':inv,'main_pid':32768,'uid':996,'gid':992,'state':'active/running'},
       kernel={'unit':unit,'invocation_id':inv,'observation':'PINNED_FD_READ','samples':['1','0'],'arm_pid':32768},
       retained={'unit':unit,'invocation_id':inv,'active':'active','substate':'exited',
         'main_pid':0,'result':'success','exec_main_status':0,'exit_type':'cgroup','remain_after_exit':True},
       final={'unit':unit,'stop_rc':0,'active':'inactive','main_pid':0,'result':'success'})

def source_check():
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_systemd_kernel_witness_v0_1 as witness,
        cf10_systemd_launcher_v0_1 as launcher)
    if launcher.LIVE_CUTOVER_ENABLED is not False:deny('LIVE_SWITCH')
    if not callable(witness.KernelWitness.wait_zero):deny('KERNEL_WITNESS_ABSENT')
    result=coherent_lab(**fixture())
    if result['live_worker_kernel_terminal_proven'] is not False:deny('FALSE_LIVE_CLAIM')
    return result

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--mode',choices=['source-check'],required=True);p.parse_args(argv)
    try:
        result=source_check()
        print('CF10_V_TERMINAL=PASS_COHERENCE_FENCE_LAB_ONLY')
        print('CF10_V_TERMINAL_FIXTURE_SHA256='+result['report_sha256'])
        print('CF10_V_TERMINAL_G1_G5=OPEN_NO_LIVE_ATTESTATION')
        return 0
    except (TerminalHold,AssertionError,ImportError,AttributeError,ValueError,KeyError,TypeError):
        print('CF10_V_TERMINAL=HOLD_SOURCE_CHECK')
        return 3
if __name__=='__main__':raise SystemExit(main())
