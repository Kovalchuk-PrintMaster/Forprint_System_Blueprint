"""Large Batch L: retained kernel 1->0 terminal proof for a disposable systemd unit.

This is a non-authorizing lab-to-canonical-contract crosswalk. The only
production witness implementation reused is cf10_systemd_kernel_witness_v0_1.
A successful lab cannot close G5 for an actual Copilot Worker or write ledger.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from collections.abc import Mapping

SCHEMA='cf10_batch_l_retained_kernel_terminal_contract_v0_1'
UNIT_RE=re.compile(r'forprint-cf10-batchl-[0-9a-f]{16}\.service\Z')
INV_RE=re.compile(r'[0-9a-f]{32}\Z')
OPEN_GATES=('G1','G2','G3','G4','G5')
PROPERTIES={
    'User':'forprint-runner','Group':'forprint-runner',
    'KillMode':'control-group','RemainAfterExit':'yes',
    'ExitType':'cgroup','NoNewPrivileges':'yes',
    'ProtectHome':'yes','ProtectSystem':'strict',
    'PrivateNetwork':'yes','RestrictAddressFamilies':'AF_UNIX',
}

class TerminalHold(ValueError): pass

def deny(code): raise TerminalHold('CF10_BATCH_L_HOLD_'+code)

def check_unit(unit):
    if type(unit) is not str or UNIT_RE.fullmatch(unit) is None:deny('UNIT')
    return unit

def canonical(doc):
    return json.dumps(doc,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')

def digest(doc): return hashlib.sha256(canonical(doc)).hexdigest()

def inspect_running(*,unit,rows,peer_pid,peer_uid,peer_gid):
    check_unit(unit)
    if not isinstance(rows,Mapping):deny('ROWS')
    if type(peer_pid) is not int or peer_pid<2 or peer_uid!=996 or peer_gid!=992:deny('PEER_IDENTITY')
    needed={'Id','LoadState','ActiveState','SubState','MainPID','ControlGroup',
            'InvocationID','RemainAfterExit','ExitType','User','Group','KillMode',
            'NoNewPrivileges','ProtectHome','ProtectSystem','PrivateNetwork',
            'RestrictAddressFamilies','ReadWritePaths','Result','ExecMainStatus'}
    if set(rows)!=needed:deny('SHOW_SCHEMA')
    if (rows['Id']!=unit or rows['LoadState']!='loaded' or
        rows['ActiveState']!='active' or rows['SubState']!='running' or
        rows['MainPID']!=str(peer_pid) or rows['ControlGroup']!='/system.slice/'+unit or
        INV_RE.fullmatch(rows['InvocationID']) is None):deny('HELD_SYSTEMD_IDENTITY')
    if any(rows[k]!=v for k,v in PROPERTIES.items()):deny('EFFECTIVE_PROFILE_DRIFT')
    if rows['ReadWritePaths']!='/run/'+unit.removesuffix('.service')+'/home':deny('WRITABLE_HOME_DRIFT')
    return {'unit':unit,'invocation_id':rows['InvocationID'],'pid':peer_pid,
            'cgroup':rows['ControlGroup'],'profile_sha256':digest(dict(PROPERTIES))}

def inspect_retained(*,unit,rows,invocation_id):
    check_unit(unit)
    if not isinstance(rows,Mapping) or set(rows)!={
        'Id','LoadState','ActiveState','SubState','MainPID','ControlGroup',
        'InvocationID','RemainAfterExit','ExitType','User','Group','KillMode',
        'NoNewPrivileges','ProtectHome','ProtectSystem','PrivateNetwork',
        'RestrictAddressFamilies','ReadWritePaths','Result','ExecMainStatus'}:deny('RETAINED_SCHEMA')
    if (rows['Id']!=unit or rows['InvocationID']!=invocation_id or
        rows['LoadState']!='loaded' or rows['ActiveState']!='active' or
        rows['SubState']!='exited' or rows['MainPID']!='0' or
        rows['Result']!='success' or rows['ExecMainStatus']!='0' or
        rows['ControlGroup'] not in ('','/system.slice/'+unit)):
        deny('RETAINED_TERMINAL_NOT_PROVEN')
    if any(rows[k]!=v for k,v in PROPERTIES.items()):deny('RETAINED_PROFILE_DRIFT')
    if rows['ReadWritePaths']!='/run/'+unit.removesuffix('.service')+'/home':deny('RETAINED_WRITABLE_HOME_DRIFT')
    return {'retained':True,'systemd_result':'success','invocation_id':invocation_id}

def attest(*,unit,held,terminal,kernel,post):
    check_unit(unit)
    if not isinstance(held,Mapping) or not isinstance(terminal,Mapping) or not isinstance(kernel,Mapping) or not isinstance(post,Mapping):deny('EVIDENCE_TYPE')
    if (held.get('unit')!=unit or kernel.get('unit')!=unit or
        held.get('invocation_id')!=kernel.get('invocation_id') or
        terminal.get('invocation_id')!=held.get('invocation_id') or
        kernel.get('kernel_observation')!='PINNED_FD_READ' or
        kernel.get('transition')!='1_TO_0' or
        kernel.get('samples')!=['1','0'] or
        terminal.get('retained') is not True or
        post.get('stop_rc')!=0 or post.get('active_state')!='inactive' or
        post.get('main_pid')!='0'):
        deny('INDEPENDENT_TERMINAL_EVIDENCE_UNPROVEN')
    record={'schema':SCHEMA,'status':'PASS_RETAINED_LAB_KERNEL_TRANSITION_ONLY',
        'unit':unit,'held_invocation_id':held['invocation_id'],
        'kernel_observation':'PINNED_FD_READ','kernel_transition':'1_TO_0',
        'retained_unit_observed_before_stop':True,'stop_readback_proven':True,
        'gates_open':list(OPEN_GATES),'production_kernel_terminal_proven':False,
        'production_ledger_written':False,'worker_claim_consumed':False,
        'live_copilot_inference_executed':False,'worker_admission_authorized':False}
    record['report_sha256']=digest(record)
    return record

def source_check():
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_systemd_kernel_witness_v0_1 as witness,
        cf10_systemd_launcher_v0_1 as launcher,
    )
    if launcher.LIVE_CUTOVER_ENABLED is not False:deny('LIVE_SWITCH_OPEN')
    if not callable(witness.KernelWitness.wait_zero) or not callable(witness.read_fd):deny('KERNEL_IMPLEMENTATION_MISSING')
    if PROPERTIES['ExitType']!='cgroup' or PROPERTIES['RemainAfterExit']!='yes':deny('NOT_RETAINED')
    return {'source':'PASS_NON_AUTHORIZING_RETAINED_KERNEL_PLAN','gates_open':list(OPEN_GATES)}

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--mode',required=True,choices=('source-check',));p.parse_args(argv)
    try:
        result=source_check()
        print('CF10_BATCH_L_SOURCE='+result['source'])
        print('CF10_BATCH_L_G1_G5=OPEN_NO_LIVE_AUTHORITY')
        return 0
    except (TerminalHold,ImportError,AttributeError,ValueError,TypeError) as exc:
        print(str(exc) if isinstance(exc,TerminalHold) else 'CF10_BATCH_L_HOLD_'+type(exc).__name__)
        return 3
if __name__=='__main__':raise SystemExit(main())
