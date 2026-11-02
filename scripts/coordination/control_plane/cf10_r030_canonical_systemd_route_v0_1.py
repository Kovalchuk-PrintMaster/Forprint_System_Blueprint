"""Source-bound canonical systemd Worker route; never authorizes its own activation.

The old subprocess launcher is intentionally not a production fallback. The
existing PAM owner session, immutable claim, frozen Handoff/baseline, ledger and
independent Worker Result verifier remain independent authorities. Until the
systemd backend's source-controlled live gate is released this route blocks
BEFORE any production attempt can be consumed by the operator console.
"""
from __future__ import annotations
import os
from pathlib import Path
import stat
import subprocess

from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as binding
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_terminal_bridge_v0_1 as terminal
from scripts.coordination.control_plane import cf10_r026_trusted_systemd_readback_v0_1 as kernel
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_kernel_witness_v0_1 as witness
from scripts.coordination.control_plane.worker_runtime import cf10_r035_durable_witness_boundary_v0_1 as durable

class CanonicalCutoverBlocked(RuntimeError):
    pass

def deny(code: str):
    raise CanonicalCutoverBlocked('CF10_R030_' + code)

def assert_cutover_ready() -> None:
    """No user-supplied flag or environment variable can enable this route."""
    if backend.LIVE_CUTOVER_ENABLED is not True:
        deny('LIVE_SYSTEMD_ROUTE_NOT_RELEASED')

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

def _trusted_runner(argv:list[str]):
    if (not isinstance(argv,list) or len(argv)<3 or
            argv[:3]!=['/usr/bin/systemctl','show','--no-pager']):
        deny('SYSTEMCTL_COMMAND_SCOPE')
    return subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,timeout=12,check=False,
                          env={'PATH':'/usr/bin:/bin','LANG':'C'})

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

    try:
        started=backend.launch_after_owner_claim(spec=spec,plan=plan,
                                                started_callback=start_after_witness)
        if (started.get('state')!='SYSTEMD_RELEASED_OBSERVE_WORKER' or
                started.get('unit')!=unit or started.get('process_started') is not True or
                holder[0] is None):
            deny('RELEASE_OBSERVATION_INCOMPLETE')
        attempt=backend.RUNTIME/'forprint_system_blueprint'/'worker-01'/attempt_id
        # The witness FD remains open across gate release and worker exit.
        # Service remains retained for terminal InvocationID / Result readback.
        outcome=terminal.witnessed_terminal(unit=unit,attempt_root=attempt,
            stdout_path=attempt/'logs'/'stdout.log',stderr_path=attempt/'logs'/'stderr.log',
            witness=holder[0],runner=_trusted_runner,timeout_seconds=spec.timeout_seconds)
        # Terminal evidence is durable BEFORE returning to the Worker Result path.
        durable.record_terminal(spec=spec,unit=unit,outcome=outcome)
    finally:
        if holder[0] is not None:holder[0].close()
    if outcome.get('return_code')!=0 or outcome.get('worker_result_accepted') is not False:
        deny('TERMINAL_BRIDGE_CONTRACT_DRIFT')
    return outcome
