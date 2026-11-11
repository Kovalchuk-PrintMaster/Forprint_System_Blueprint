"""Source-bound canonical systemd Worker route; never authorizes its own activation.

The old subprocess launcher is intentionally not a production fallback. The
existing PAM owner session, immutable claim, frozen Handoff/baseline, ledger and
independent Worker Result verifier remain independent authorities. Until the
systemd backend's source-controlled live gate is released this route blocks
BEFORE any production attempt can be consumed by the operator console.
"""
from __future__ import annotations
import os
import re
import hashlib
from pathlib import Path
import stat
import subprocess

from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as binding
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_terminal_bridge_v0_1 as terminal
from scripts.coordination.control_plane import cf10_r026_trusted_systemd_readback_v0_1 as kernel
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_kernel_witness_v0_1 as witness
from scripts.coordination.control_plane.worker_runtime import cf10_r035_durable_witness_boundary_v0_1 as durable
from scripts.coordination.control_plane.worker_runtime import cf10_r138_canonical_terminal_handoff_v0_1 as handoff

class CanonicalCutoverBlocked(RuntimeError):
    pass

def deny(code: str):
    raise CanonicalCutoverBlocked('CF10_R030_' + code)

def assert_cutover_ready() -> None:
    """Legacy quarantine; only a private exact post-PAM pilot may pass."""
    if backend.LIVE_CUTOVER_ENABLED is not True:
        from scripts.coordination.control_plane import cf10_owner_pam_launch_v0_1 as owner
        from scripts.coordination.control_plane import cf10_r055_pilot_launch_corridor_v0_1 as pilot
        session = owner._SESSION.get()
        if session is None or session.phase != 'INNER_ENTERED':
            deny('LIVE_SYSTEMD_ROUTE_NOT_RELEASED')
        try:
            pilot.assert_after_owner_claim(root=backend.BLUEPRINT, runtime=backend.RUNTIME,
                                           task=session.task, attempt=session.attempt, head=session.head)
        except Exception:
            deny('EXACT_PILOT_AFTER_CLAIM_GATE_DENIED')

def bind_contract(*, root:Path, runtime_root:Path, task_prompt_id:str,
                  attempt_id:str, source_head:str, baseline_sha256:str,
                  handoff_sha256:str, launch_values:dict) -> tuple[binding.BoundedInput,dict]:
    """Bind only canonical frozen evidence; caller must independently validate it."""
    if Path(root) != backend.BLUEPRINT or Path(runtime_root) != backend.RUNTIME:
        deny('CANONICAL_ROOT_MISMATCH')
    if not isinstance(launch_values,dict):deny('INVOCATION_INVALID')
    if any(k not in launch_values for k in ('argv','cwd','stdout_path','stderr_path','timeout_seconds')):
        deny('INVOCATION_FIELDS')
    attempt_root=backend.RUNTIME/'forprint_system_blueprint'/'worker-01'/attempt_id
    cwd=attempt_root/'workspace'/'repo'
    if Path(launch_values['cwd'])!=cwd:deny('WORKSPACE_MISMATCH')
    if Path(launch_values['stdout_path'])!=attempt_root/'logs'/'stdout.log':deny('STDOUT_MISMATCH')
    if Path(launch_values['stderr_path'])!=attempt_root/'logs'/'stderr.log':deny('STDERR_MISMATCH')
    if not isinstance(launch_values['argv'],list):deny('ARGV_TYPE')
    spec=binding.BoundedInput(task_prompt_id=task_prompt_id,attempt_id=attempt_id,
        source_head=source_head,baseline_sha256=baseline_sha256,
        handoff_sha256=handoff_sha256,workspace=str(cwd),
        runtime_root=str(backend.RUNTIME),argv=tuple(launch_values['argv']),
        timeout_seconds=launch_values['timeout_seconds'])
    plan=binding.bind_plan(spec)
    binding.validate_plan(plan,spec)
    return spec,plan

def review_guarded_ipc_handoff(*,spec:binding.BoundedInput,plan:dict,
                               invocation:dict,candidate:dict)->dict:
    """Canonical R030 source-only preclaim seam for a *future* IPC mode.

    Shares the existing canonical R013 plan and R134 R115/R127 crosswalk;
    cannot open root broker, call owner/PAM, consume a claim, or start systemd.
    Production run_once() remains the sole launch route and remains gated.
    """
    if backend.LIVE_CUTOVER_ENABLED is not False:
        deny('IPC_REVIEW_LIVE_SWITCH_UNEXPECTED')
    if type(spec) is not binding.BoundedInput or type(plan) is not dict:
        deny('IPC_REVIEW_INPUTS')
    try:
        binding.validate_plan(plan,spec)
    except (binding.BoundaryBlocked,TypeError,ValueError,KeyError):
        deny('IPC_REVIEW_R013_PLAN')
    if (type(invocation) is not dict or type(candidate) is not dict or
        invocation.get('attempt_id') != spec.attempt_id or
        invocation.get('task_id') != spec.task_prompt_id or
        invocation.get('workspace_repo') != spec.workspace or
        invocation.get('argv') != list(spec.argv) or
        candidate.get('source_head') != spec.source_head or
        candidate.get('attempt_id') != spec.attempt_id or
        plan['identity']['argv_sha256'] != hashlib.sha256('\0'.join(spec.argv).encode()).hexdigest()):
        deny('IPC_REVIEW_FROZEN_ATTEMPT_DRIFT')
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_r134_ipc_preclaim_crosswalk_v0_1 as crosswalk,
    )
    try:
        checked=crosswalk.verify_source_only(invocation=invocation,candidate=candidate)
    except (crosswalk.IPCPreclaimHold,ValueError,TypeError,KeyError):
        deny('IPC_REVIEW_R134_CROSSWALK')
    if checked['candidate_sha256'] != candidate['candidate_sha256']:
        deny('IPC_REVIEW_CANDIDATE_DIGEST')
    return {
        'schema_version':'cf10_r030_guarded_ipc_handoff_review_v0_1',
        'state':'CANONICAL_R030_IPC_REVIEW_ONLY_BEFORE_CLAIM',
        'attempt_id':spec.attempt_id,'source_head':spec.source_head,
        'unit':plan['identity']['unit'],
        'canonical_argv_sha256':plan['identity']['argv_sha256'],
        'candidate_sha256':checked['candidate_sha256'],
        'crosswalk_report_sha256':checked['report_sha256'],
        'model_tools':['ForPrintValidation-run_repo_head'],
        'live_worker_authorized':False, 'claim_consumed':False,
        'worker_started':False, 'terminal_ledger_written':False,
        'g1_g5_closed':False,'automatic_retry':False,
    }

def _trusted_runner(argv:list[str]):
    if (not isinstance(argv,list) or len(argv)<3 or
            argv[:3]!=['/usr/bin/systemctl','show','--no-pager']):
        deny('SYSTEMCTL_COMMAND_SCOPE')
    return subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,timeout=12,check=False,
                          env={'PATH':'/usr/bin:/bin','LANG':'C'})

def _retire_after_durable_terminal(unit:str)->None:
    """Retire only the exact retained CF10 unit AFTER fsynced terminal evidence.

    Never stop an active/unverified worker: the caller reaches this only
    after a successful pinned-kernel 1->0 and durable terminal record. A
    failed stop/readback requires operator reconciliation, never retry.
    """
    if not isinstance(unit,str) or not re.fullmatch(r'forprint-cf10-worker-[0-9a-f]{24}\.service',unit):
        deny('RETIRE_UNIT_IDENTITY')
    try:
        result=subprocess.run(['/usr/bin/systemctl','stop','--',unit],
            stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            timeout=12,check=False,env={'PATH':'/usr/bin:/bin','LANG':'C'})
    except (OSError,subprocess.SubprocessError):
        deny('RETAINED_UNIT_STOP_UNAVAILABLE')
    if result.returncode!=0:deny('RETAINED_UNIT_STOP_FAILED')
    try:observation=backend._show(unit,_trusted_runner)
    except Exception:deny('RETAINED_UNIT_STOP_READBACK_UNAVAILABLE')
    if (observation.get('Id')!=unit or observation.get('LoadState')!='not-found'
            or observation.get('ActiveState')!='inactive'
            or observation.get('MainPID')!='0'):
        deny('RETAINED_UNIT_NOT_STOPPED')

def _cgroup_populated(unit:str)->str:
    """Only cgroup.events populated=0 is positive evidence. Missing => UNKNOWN."""
    state=kernel._kernel_snapshot(unit,'/system.slice/'+unit,
                                kernel_root=kernel.CGROUP_ROOT)
    if state.get('cgroup_state')=='EMPTY_AT_SAMPLE' and state.get('sampled_populated')=='0':
        return '0'
    return 'UNKNOWN_OR_POPULATED'

def run_once(*,root:Path,runtime_root:Path,task_prompt_id:str,attempt_id:str,
             source_head:str,baseline_sha256:str,handoff_sha256:str,
             launch_values:dict,started_callback):
    """Single canonical route. Success means terminal process, NOT Worker acceptance."""
    assert_cutover_ready()
    if os.geteuid()!=0:deny('ROOT_REQUIRED')
    spec,plan=bind_contract(root=root,runtime_root=runtime_root,
        task_prompt_id=task_prompt_id,attempt_id=attempt_id,
        source_head=source_head,baseline_sha256=baseline_sha256,
        handoff_sha256=handoff_sha256,launch_values=launch_values)
    unit=plan['identity']['unit']
    holder=[None]

    def start_after_witness(record):
        # Called while the systemd gate is HELD. No Worker argv can run yet.
        # If this root-side readback fails, STARTED is NOT appended or released.
        if holder[0] is not None:deny('WITNESS_CALLBACK_REPEATED')
        holder[0]=witness.arm(unit,_trusted_runner)
        # Immutable root boundary must be fsynced BEFORE ledger STARTED/release.
        durable.record_pre(spec=spec,unit=unit,witness=holder[0])
        started_callback(record)

    # Post-release errors are NOT ordinary terminal completion. Preserve the
    # existing R030 happy path, but kill the already released canonical unit
    # and record REVIEW_REQUIRED if result/kernel/durable proof fails.
    released=False
    durable_terminal=False
    try:
        started=backend.launch_after_owner_claim(spec=spec,plan=plan,
                                                started_callback=start_after_witness)
        released=True  # the only successful backend return is after gate release
        if (started.get('state')!='SYSTEMD_RELEASED_OBSERVE_WORKER' or
                started.get('unit')!=unit or started.get('process_started') is not True or
                holder[0] is None):
            deny('RELEASE_OBSERVATION_INCOMPLETE')
        attempt=backend.RUNTIME/'forprint_system_blueprint'/'worker-01'/attempt_id
        # R030 arms the actual kernel witness in its STARTED callback BEFORE
        # release. Do not duplicate the arm in the backend (R132 corrected).
        outcome=terminal.witnessed_terminal(unit=unit,attempt_root=attempt,
            stdout_path=attempt/'logs'/'stdout.log',stderr_path=attempt/'logs'/'stderr.log',
            witness=holder[0],runner=_trusted_runner,timeout_seconds=spec.timeout_seconds)
        durable.record_terminal(spec=spec,unit=unit,outcome=outcome)
        durable_terminal=True
        # R138 checks historical kernel/claim/STARTED ledger lineage. This is
        # a read-only review gate, NOT a terminal append/Worker Result verdict.
        handoff.review_success(spec=spec,unit=unit,outcome=outcome)
        _retire_after_durable_terminal(unit)
    except BaseException:
        if released and not durable_terminal:
            from scripts.coordination.control_plane.worker_runtime import (
                cf10_r133_post_release_quarantine_v0_1 as quarantine,
            )
            try:
                cancelled=quarantine.quarantine(attempt_id=attempt_id,source_head=source_head,
                    unit=unit,pinned_witness=holder[0],timeout_seconds=spec.timeout_seconds)
                # A killed cgroup is not a valid Worker Result or terminal
                # ledger fact. Verify R133 review receipts and R035 PRE only.
                handoff.review_cancelled(spec=spec,unit=unit,outcome=cancelled)
            except (quarantine.QuarantineHold, handoff.TerminalHandoffHold) as exc:
                # Do not report successful cancellation or Worker terminal
                # when systemd/FD/receipt proofs are absent.
                raise CanonicalCutoverBlocked('CF10_R030_POST_RELEASE_RECONCILE_REQUIRED') from exc
        raise  # After successful cancellation, original failure is still fatal.
    finally:
        if holder[0] is not None:holder[0].close()
    if outcome.get('return_code')!=0 or outcome.get('worker_result_accepted') is not False:
        deny('TERMINAL_BRIDGE_CONTRACT_DRIFT')
    return outcome
