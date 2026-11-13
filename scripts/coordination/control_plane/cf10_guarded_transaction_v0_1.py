"""CF-10 r023: explicit, non-authorizing transaction core.

The only public executor is a DISPOSABLE fixture harness, not a production launcher.
It uses actual r022 immutable root receipt primitives and the r020 read-only join.
A successful fixture *cannot* assert independent verification or release authority.
No subprocess/systemd invocation, Git mutation, credential access, or automatic retry.

Production integration needs separate authenticated operator gate and trusted runtime
adapter; this module must not be connected to governed_worker_cycle launch.
"""
from __future__ import annotations
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
import os
import re
from typing import Protocol

from scripts.coordination.control_plane import (
    cf10_root_lifecycle_receipt_v0_1 as receipt,
    cf10_receipt_ledger_join_review_v0_1 as join,
    cf10_supervisor_binding_candidate_v0_1 as supervisor,
)

class TransactionBlocked(RuntimeError):
    pass

def deny(tag: str) -> None:
    raise TransactionBlocked('CF10_R023_' + tag)

class SimulatedCrash(BaseException):
    """Test-only hard interruption: intentionally bypass exception handlers."""

@dataclass(frozen=True)
class FixtureScope:
    # A private, disposable fixture directory, NEVER a production runtime root.
    private_store: Path
    fixture_parent: Path

    def validate(self) -> None:
        p = self.private_store
        parent = self.fixture_parent
        if not p.is_absolute() or not parent.is_absolute() or p.is_symlink() or parent.is_symlink():
            deny('FIXTURE_PATH')
        if p != parent / 'root_receipts' or parent.name != 'cf10-r023-disposable-fixture':
            deny('FIXTURE_SCOPE')
        if not parent.is_dir() or not p.is_dir():
            deny('FIXTURE_MISSING')
        if os.path.commonpath((str(parent), '/srv/software_development/forprint-worker-runtime')) == '/srv/software_development/forprint-worker-runtime':
            deny('PRODUCTION_RUNTIME_FORBIDDEN')
        if os.path.commonpath((str(parent), '/srv/software_development/forprint-project')) == '/srv/software_development/forprint-project':
            deny('PRODUCTION_REPOSITORY_FORBIDDEN')
        # No symlink traversal at root or store; stores are otherwise checked by r022.
        if parent.resolve() != parent or p.resolve() != p:
            deny('FIXTURE_SYMLINK')

class FixtureDriver(Protocol):
    def start(self, plan: Mapping, spec: supervisor.BoundedInput) -> None: ...
    def stop(self, plan: Mapping, spec: supervisor.BoundedInput) -> None: ...
    def observe(self, plan: Mapping, spec: supervisor.BoundedInput) -> dict: ...

class FixtureLedger(Protocol):
    def started(self, spec: supervisor.BoundedInput) -> None: ...
    def rows(self, spec: supervisor.BoundedInput) -> list[dict]: ...


def _validate_fixture(*, scope: FixtureScope, plan: dict,
                      spec: supervisor.BoundedInput, driver: FixtureDriver,
                      ledger: FixtureLedger) -> None:
    if not isinstance(scope, FixtureScope): deny('NOT_FIXTURE')
    scope.validate()
    supervisor.validate_plan(plan, spec)
    if not all(callable(getattr(driver, name, None)) for name in ('start', 'stop', 'observe')):
        deny('DRIVER_PROTOCOL')
    if not all(callable(getattr(ledger, name, None)) for name in ('started', 'rows')):
        deny('LEDGER_PROTOCOL')
    if os.geteuid() != 0: deny('ROOT_FIXTURE_REQUIRED')
    if not re.fullmatch(r'[0-9a-f]{40}', spec.source_head): deny('HEAD')


def inspection(*, scope: FixtureScope, spec: supervisor.BoundedInput,
               ledger: FixtureLedger) -> dict:
    """Read-only recovery view; absence of claim is not proof of permission."""
    scope.validate()
    try:
        state = receipt.observe(private_store=scope.private_store,
            attempt_id=spec.attempt_id, expected_head=spec.source_head)
    except FileNotFoundError:
        if (scope.private_store / spec.attempt_id).exists() or (scope.private_store / spec.attempt_id).is_symlink():
            return {'state': 'QUARANTINE_INCOMPLETE_OR_TAMPERED_RECEIPT',
                    'attempt_id': spec.attempt_id, 'automatic_retry': False,
                    'worker_result_accepted': False, 'release_allowed': False}
        state = None
    except receipt.ReceiptBlocked as exc:
        # An occupied but incomplete claim directory is UNKNOWN, not unused.
        if (scope.private_store / spec.attempt_id).exists():
            return {'state': 'QUARANTINE_INCOMPLETE_OR_TAMPERED_RECEIPT',
                    'attempt_id': spec.attempt_id, 'automatic_retry': False,
                    'worker_result_accepted': False, 'release_allowed': False}
        raise
    if state is not None:
        # r022 observe() verifies the chain but intentionally omits handoff from
        # its summary. Bind that immutable claim explicitly before cross-store join.
        raw = receipt._read_json(scope.private_store / spec.attempt_id / '0000_claim.json')
        if raw.get('handoff_sha256') != spec.handoff_sha256:
            deny('CLAIM_HANDOFF_MISMATCH')
    result = join.reconcile(attempt_id=spec.attempt_id,source_head=spec.source_head,
        handoff_sha256=spec.handoff_sha256,receipt=state,ledger_rows=ledger.rows(spec))
    return result


def execute_fixture(*, scope: FixtureScope, plan: dict,
                    spec: supervisor.BoundedInput, driver: FixtureDriver,
                    ledger: FixtureLedger, failpoint: str | None = None) -> dict:
    """Run ONE fixture transaction. Failpoints imitate immediate process death.

    There is no manual permission to retry the same ID. Caller must not supply
    a real Worker driver; this non-authorizing path exists for controlled QA.
    """
    _validate_fixture(scope=scope,plan=plan,spec=spec,driver=driver,ledger=ledger)
    failpoints_allowed = {None, 'after_claim', 'after_launch_intent',
                          'after_start', 'after_service_observed',
                          'after_ledger_started', 'after_stop', 'after_quiescence_candidate'}
    if failpoint not in failpoints_allowed: deny('FAILPOINT')
    store = scope.private_store
    # Actual irreversible O_EXCL receipt; claim before any adapter invocation.
    receipt.claim(private_store=store, attempt_id=spec.attempt_id,
        head=spec.source_head,handoff_sha256=spec.handoff_sha256)
    if failpoint == 'after_claim': raise SimulatedCrash('after_claim')
    receipt.append_observation(private_store=store,attempt_id=spec.attempt_id,
        expected_head=spec.source_head,event='LAUNCH_REQUESTED')
    if failpoint == 'after_launch_intent': raise SimulatedCrash('after_launch_intent')
    started = False
    stop_attempted = False
    try:
        driver.start(plan, spec)
        started = True
        if failpoint == 'after_start': raise SimulatedCrash('after_start')
        obs = driver.observe(plan, spec)
        if (not isinstance(obs,dict) or obs.get('attempt_id') != spec.attempt_id
                or obs.get('source_head') != spec.source_head
                or obs.get('worker_result_accepted') is not False
                or obs.get('production_quiescence_proven') is not False):
            deny('UNTRUSTED_SERVICE_OBSERVATION')
        receipt.append_observation(private_store=store,attempt_id=spec.attempt_id,
            expected_head=spec.source_head,event='SERVICE_OBSERVED')
        if failpoint == 'after_service_observed': raise SimulatedCrash('after_service_observed')
        ledger.started(spec)  # Fake contract in fixture; production must validate canonical record.
        if failpoint == 'after_ledger_started': raise SimulatedCrash('after_ledger_started')
        receipt.append_observation(private_store=store,attempt_id=spec.attempt_id,
            expected_head=spec.source_head,event='STOP_REQUESTED')
        driver.stop(plan, spec)
        stop_attempted = True
        if failpoint == 'after_stop': raise SimulatedCrash('after_stop')
        # Candidate observation only; NEVER production quiescence proof.
        receipt.append_observation(private_store=store,attempt_id=spec.attempt_id,
            expected_head=spec.source_head,event='QUIESCENCE_OBSERVED_CANDIDATE')
        if failpoint == 'after_quiescence_candidate': raise SimulatedCrash('after_quiescence_candidate')
    except Exception:
        # Hard interruption (BaseException) intentionally bypasses cleanup for recovery tests.
        if started and not stop_attempted:
            try: driver.stop(plan,spec)
            except Exception: pass
        try:
            receipt.append_observation(private_store=store,attempt_id=spec.attempt_id,
                expected_head=spec.source_head,event='REVIEW_REQUIRED')
        except Exception: pass
        raise
    return inspection(scope=scope,spec=spec,ledger=ledger)
