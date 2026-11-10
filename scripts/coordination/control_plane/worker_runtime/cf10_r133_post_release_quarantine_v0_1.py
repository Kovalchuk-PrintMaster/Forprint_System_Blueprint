"""CF10 R133: fail-closed, root-side post-release cancellation/quarantine.

Only R030 may call this after its existing canonical launch has returned.
Does not authorize a Worker, accept Results, grant release, retry, or claim
terminal success. A stopped cgroup is never a successful Worker Result.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess

from scripts.coordination.control_plane import cf10_root_lifecycle_receipt_v0_1 as receipts
from scripts.coordination.control_plane.worker_runtime import cf10_systemd_kernel_witness_v0_1 as kernel

UNIT = re.compile(r'forprint-cf10-worker-[a-f0-9]{24}\.service\Z')
STORE = Path('/srv/software_development/forprint-worker-runtime/forprint_system_blueprint/control_plane/root_receipts')
SYSTEMCTL = '/usr/bin/systemctl'

class QuarantineHold(RuntimeError):
    pass


def deny(code: str) -> None:
    raise QuarantineHold('CF10_R133_HOLD_' + code)


def _append_review(*, attempt_id: str, source_head: str, observed: bool) -> None:
    """Write only existing non-authorizing R015 receipt event kinds.

    Failure to append is itself a HOLD. No terminal Worker result is forged.
    """
    event = 'QUIESCENCE_OBSERVED_CANDIDATE' if observed else 'QUIESCENCE_UNPROVEN'
    try:
        receipts.append_observation(private_store=STORE, attempt_id=attempt_id,
                                    expected_head=source_head, event=event)
        receipts.append_observation(private_store=STORE, attempt_id=attempt_id,
                                    expected_head=source_head, event='REVIEW_REQUIRED')
    except (receipts.ReceiptBlocked, OSError, ValueError, KeyError, TypeError):
        deny('ROOT_RECEIPT_REVIEW_NOT_DURABLE')


def quarantine(*, attempt_id: str, source_head: str, unit: str,
               pinned_witness: kernel.KernelWitness, timeout_seconds: int,
               runner=None) -> dict:
    """Stop only an already-released, exact canonical unit, then observe FD.

    Unsuccessful stop or missing kernel observation -> QUARANTINE HOLD, not a
    terminal state. No fake cgroup-zero is accepted. Never removes a unit.
    """
    if os.geteuid() != 0:
        deny('ROOT_REQUIRED')
    if (type(unit) is not str or not UNIT.fullmatch(unit)
        or not isinstance(attempt_id, str) or not receipts.ATTEMPT.fullmatch(attempt_id)
        or not isinstance(source_head, str) or not receipts.HEAD.fullmatch(source_head)
        or type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 7200):
        deny('CANONICAL_IDENTITY')
    if (type(pinned_witness) is not kernel.KernelWitness
        or pinned_witness.closed or pinned_witness.armed_populated != '1'
        or pinned_witness.unit != unit
        or not kernel.INVOKE.fullmatch(pinned_witness.invocation_id)):
        deny('PINNED_WITNESS_REQUIRED')
    if runner is None:
        def runner(argv):
            return subprocess.run(argv, stdin=subprocess.DEVNULL,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  timeout=12, check=False,
                                  env={'PATH': '/usr/bin:/bin', 'LANG': 'C'})
    if not callable(runner):
        deny('RUNNER')
    # Independent retained systemd readback immediately before signal.
    # A unit NAME alone is not sufficient: reject a recycled InvocationID
    # or an unrelated account/cgroup even with the correct unit pattern.
    try:
        live = kernel.show(unit, runner)
    except (kernel.WitnessBlocked, OSError, ValueError, TypeError, KeyError):
        deny('RETAINED_UNIT_READBACK_UNAVAILABLE')
    if (live.get('InvocationID') != pinned_witness.invocation_id
        or live.get('Id') != unit or live.get('LoadState') != 'loaded'
        or live.get('ControlGroup') != '/system.slice/' + unit
        or live.get('User') != 'forprint-runner'
        or live.get('Group') != 'forprint-runner'
        or live.get('KillMode') != 'control-group'):
        deny('RETAINED_UNIT_IDENTITY_DRIFT')
    # Exact single-unit kill; no wildcard and no stop/reset that could erase
    # retained systemd evidence. SIGKILL bounds in-flight tool descendants.
    command = [SYSTEMCTL, 'kill', '--signal=SIGKILL', '--', unit]
    killed = False
    try:
        cp = runner(command)
        killed = type(cp.returncode) is int and cp.returncode == 0
    except (OSError, subprocess.SubprocessError, AttributeError):
        killed = False
    observed = False
    if killed:
        try:
            state = pinned_witness.wait_zero(timeout_seconds=min(timeout_seconds, 60))
            observed = (type(state) is dict and state.get('transition') == '1_TO_0'
                        and state.get('unit') == unit
                        and state.get('invocation_id') == pinned_witness.invocation_id
                        and state.get('kernel_observation') == 'PINNED_FD_READ')
        except (kernel.WitnessBlocked, OSError, ValueError, TypeError, KeyError):
            observed = False
    # Record HOLD/review even if kill/readback failed, as long as we can write
    # the existing immutable claim chain. Any unprovable fact remains HOLD.
    _append_review(attempt_id=attempt_id, source_head=source_head, observed=observed)
    if not killed:
        deny('SYSTEMD_KILL_NOT_PROVEN_RECONCILE')
    if not observed:
        deny('PINNED_KERNEL_ZERO_NOT_PROVEN_RECONCILE')
    return {'state': 'CANCELLED_KERNEL_ZERO_REVIEW_REQUIRED',
            'attempt_id': attempt_id, 'unit': unit,
            'systemd_invocation_id': pinned_witness.invocation_id,
            'root_review_recorded': True, 'worker_result_accepted': False,
            'terminal_success': False, 'automatic_retry': False,
            'release_allowed': False, 'worker_authorized': False}
