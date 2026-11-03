"""r053 dormant pilot cutover seam: root-safe hard stop, never release authority.

This exists to prove source wiring before freezing Task70. It NEVER launches,
consumes one-shot claims, changes runtime state or accepts completion. The live
activation is a separate source/governance change, prohibited by this module.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re

SCHEMA = 'cf10_r053_dormant_pilot_bridge_v0_1'
TASK = 'cf10-validation-check-pipeline-profile-and-optimization-v0-1'
ATTEMPT = re.compile(r'cf10-u180j-a[0-9]{3,}\Z')

class PilotDormantBlocked(RuntimeError):
    pass


def refuse_backend_launch(*, spec, guard_module) -> None:
    """Unconditional hard stop before Worker _core, even with fake/all-PASS evidence.

    `spec` and guard_module cannot enable the bridge: no calls to either are
    made. No process, PAM, claim, socket, ledger or proof issuance occurs.
    """
    raise PilotDormantBlocked('CF10_R053_DORMANT_BACKEND_NOT_RELEASED')


def requirements() -> dict:
    return {'schema_version': SCHEMA,
            'status': 'MAKE_PREFLIGHT_PRESENT_BACKEND_DORMANT_NON_AUTHORIZING',
            'launch_allowed': False,
            'production_worker_launched': False,
            'production_cutover': False,
            'legacy_release_quarantine_unchanged': True,
            'root_pilot_proof_issued': False,
            'preclaim_receipt_issued': False,
            'next_action': 'EXACT_SOURCE_BOUND_RUNTIME_ACTIVATION_AND_POSTWORKER_GATE_REVIEW'}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('requirements',), required=True)
    parser.parse_args(argv)
    print(json.dumps(requirements(), sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
