#!/usr/bin/env python3
"""CF10 R140: bounded root IPC broker adapter over existing R135/R126.

Source-only release status.  This is a REAL reusable root socket/session
adapter, but remains restricted to disposable R125 leases under /run. It does
not start Copilot, a Worker, or an MCP child; mint a lease, consume a claim,
write a ledger, authorize a release, or attest provider egress/credentials.

The independent root caller must have established that the backend socket
belongs to its canonical MCP child. Kernel peer identity alone cannot prove
that lineage; the method intentionally reports that outstanding blocker.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import select
import socket
import stat
import time
from typing import Mapping

from scripts.coordination.control_plane.worker_runtime import (
    cf10_r126_root_external_revoke_v0_1 as lease_lib,
    cf10_r135_ipc_session_fence_v0_1 as session_lib,
)

SCHEMA = 'cf10_r140_root_ipc_broker_adapter_v0_1'
MAX_ACCEPT = 30
SOCKET_NAME = 'mcp.sock'


class BrokerHold(RuntimeError):
    pass


def deny(reason: str) -> None:
    raise BrokerHold('CF10_R140_HOLD_' + reason)


def _identity(*, invocation: Mapping, candidate: Mapping, attempt: str,
              epoch: str, head: str, lease: Path) -> dict:
    if os.geteuid() != 0:
        deny('ROOT_REQUIRED')
    try:
        identity = session_lib.verify_binding(invocation=invocation,
            candidate=candidate, expected_attempt=attempt,
            expected_epoch=epoch, expected_head=head, lease_path=lease)
        session_lib.check_lease(lease_path=lease, identity=identity)
    except (session_lib.SessionHold, lease_lib.ExternalRevokeHold,
            KeyError, TypeError, ValueError, OSError) as exc:
        deny('FROZEN_LEASE_OR_INVOCATION_' + type(exc).__name__)
    if identity.get('unit') is None:
        deny('UNIT_MISSING')
    return identity


def _directory(lease: Path) -> tuple[int, int]:
    """Root-owned 0710 directory from R126; do not follow symlinks."""
    if not isinstance(lease, Path) or not lease_lib.LEASE_RE.fullmatch(str(lease)):
        deny('LAB_LEASE_SCOPE')
    gid = lease_lib.runner_gid()
    try:
        fd = lease_lib._safe_parent(lease, gid)
    except (lease_lib.ExternalRevokeHold, OSError, ValueError):
        deny('PARENT_ROOT_OWNER_MODE')
    return fd, gid


def _check_socket(path: Path, gid: int, *, device: int | None = None,
                  inode: int | None = None) -> None:
    try:
        info = path.lstat()
    except OSError:
        deny('SOCKET_MISSING')
    if (not stat.S_ISSOCK(info.st_mode) or info.st_uid != 0 or info.st_gid != gid
            or stat.S_IMODE(info.st_mode) != 0o660 or info.st_nlink != 1):
        deny('SOCKET_OWNER_MODE')
    if (device is not None and info.st_dev != device) or (inode is not None and info.st_ino != inode):
        deny('SOCKET_INODE_CHANGED')


def bind_lab_listener(*, invocation: Mapping, candidate: Mapping,
                      attempt: str, epoch: str, head: str,
                      lease: Path) -> tuple[socket.socket, dict]:
    """Provision exactly one root-owned client listener, no child or Worker.

    R125 disposable lease must already exist, be bound and not revoked. An
    occupied socket or unsafe parent is HOLD; never unlink an unknown inode.
    """
    identity = _identity(invocation=invocation, candidate=candidate,
        attempt=attempt, epoch=epoch, head=head, lease=lease)
    fd, gid = _directory(lease)
    path = lease.with_name(SOCKET_NAME)
    listener = None
    bound_inode = None
    try:
        if path.exists() or path.is_symlink():
            deny('SOCKET_OCCUPIED_NO_OVERWRITE')
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM | socket.SOCK_CLOEXEC)
        listener.bind(str(path))
        bound_inode = path.lstat()
        os.chown(path, 0, gid, follow_symlinks=False)
        os.chmod(path, 0o660, follow_symlinks=False)
        _check_socket(path, gid, device=bound_inode.st_dev, inode=bound_inode.st_ino)
        listener.listen(1)
        session_lib.check_lease(lease_path=lease, identity=identity)
        return listener, identity
    except BaseException:
        if listener is not None:
            listener.close()
        if bound_inode is not None:
            try:
                current = path.lstat()
                if (current.st_dev, current.st_ino) == (bound_inode.st_dev, bound_inode.st_ino):
                    path.unlink()
            except FileNotFoundError:
                pass
        raise
    finally:
        os.close(fd)


def _revoke_on_hold(*, lease: Path, identity: dict) -> None:
    """Attempt irreversible revocation; never claim physical process shutdown."""
    values = {'attempt': identity['attempt_id'], 'epoch': identity['epoch'],
              'source_head': identity['source_head'],
              'capsule_id': identity['capsule_id']}
    try:
        state = lease_lib.inspect_lease(lease, **values)
        if state.get('revoked') is False:
            lease_lib.revoke_lease(lease, **values)
        elif state.get('revoked') is not True:
            deny('LEASE_STATE_CORRUPT')
        final = lease_lib.inspect_lease(lease, **values)
        if final.get('revoked') is not True:
            deny('REVOKE_READBACK_FAILED')
    except (lease_lib.ExternalRevokeHold, OSError, KeyError,
            TypeError, ValueError) as exc:
        deny('REVOKE_UNPROVEN_' + type(exc).__name__)


def _serve_lab_one(*, listener: socket.socket, trusted_mcp: socket.socket,
              invocation: Mapping, candidate: Mapping, attempt: str,
              epoch: str, head: str, lease: Path,
              timeout_seconds: int = 10) -> dict:
    """One root-controlled, kernel-peer-verified R135 session.

    The caller provisions a separately controlled canonical MCP backend; its
    origin and full cgroup quiescence require independent proofs outside R140.
    Any error fences the lease and yields quarantine, NEVER success/retry.
    """
    identity = _identity(invocation=invocation, candidate=candidate,
        attempt=attempt, epoch=epoch, head=head, lease=lease)
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 30:
        deny('TIMEOUT')
    if not isinstance(listener, socket.socket) or not isinstance(trusted_mcp, socket.socket):
        deny('SOCKET_TYPE')
    if listener.getsockname() != str(lease.with_name(SOCKET_NAME)):
        deny('LISTENER_SCOPE')
    fd, gid = _directory(lease)
    try:
        _check_socket(lease.with_name(SOCKET_NAME), gid)
    finally:
        os.close(fd)
    try:
        session_lib.verify_peer(trusted_mcp, unit=identity['unit'])
    except (session_lib.SessionHold, OSError, TypeError, ValueError):
        deny('BACKEND_PEER_UNTRUSTED')
    # Recheck lease at the last decision point before accepting one connection.
    session_lib.check_lease(lease_path=lease, identity=identity)
    client = None
    try:
        deadline = time.monotonic() + timeout_seconds
        while client is None:
            session_lib.check_lease(lease_path=lease, identity=identity)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                deny('ACCEPT_TIMEOUT')
            ready, _, _ = select.select([listener], [], [], min(.05, remaining))
            if ready:
                client, _ = listener.accept()
        result = session_lib.handle_session(client=client, trusted_mcp=trusted_mcp,
            invocation=invocation, candidate=candidate,
            expected_attempt=attempt, expected_epoch=epoch, expected_head=head,
            lease_path=lease, timeout_seconds=timeout_seconds)
        if (not isinstance(result, dict) or result.get('read_only_calls') != 1 or
                result.get('lease_exhausted') is not True or
                result.get('worker_result_accepted') is not False or
                result.get('terminal_ledger_written') is not False or
                result.get('live_worker_authorized') is not False):
            deny('SESSION_RESULT_NOT_SEALED')
        session_lib.check_lease(lease_path=lease, identity=identity, revoked=True)
        return {'schema_version': SCHEMA, 'state': 'ONE_READ_ONLY_MCP_SESSION_REVIEW_ONLY',
                'attempt_id': attempt, 'epoch': epoch, 'source_head': head,
                'unit': identity['unit'], 'lease_revoked': True,
                'session_read_only_calls': 1, 'backend_lineage_independently_proven': False,
                'worker_result_accepted': False, 'terminal_ledger_written': False,
                'kernel_terminal_proven': False, 'g1_g5_closed': False,
                'live_worker_authorized': False, 'automatic_retry': False}
    except BaseException as exc:
        # A forwarded operation might still be active. Do not report success
        # or release; external R133 + KernelWitness proof remains mandatory.
        try:
            _revoke_on_hold(lease=lease, identity=identity)
        except BrokerHold as fence_exc:
            raise BrokerHold('CF10_R140_HOLD_REVOKE_UNKNOWN_KERNEL_QUARANTINE_REQUIRED') from fence_exc
        raise BrokerHold('CF10_R140_HOLD_SESSION_KERNEL_QUARANTINE_REQUIRED') from exc
    finally:
        if client is not None:
            client.close()



def serve_one(*, listener: socket.socket, trusted_mcp: socket.socket,
              invocation: Mapping, candidate: Mapping, attempt: str,
              epoch: str, head: str, lease: Path,
              held_review: dict, spec, plan: dict, witness,
              bridge_pin, child_pin, frozen_source_commit: str,
              timeout_seconds: int = 10) -> dict:
    """R144 guarded root-side handoff: POST-release proof BEFORE any IPC frame.

    R141 rereads the same kernel systemd invocation and bridge socket PIDFD;
    R143 rereads the direct MCP child PIDFD/stdio and all Git object capsule
    bytes. No report supplied by the Worker can substitute for the checks.

    The only executable session is R140's existing disposable R125 lease API;
    this wrapper DOES NOT mint a claim or listener, release the held gate,
    launch a Worker, prove Copilot G1-G3 or append to the terminal ledger.
    """
    # First establish a root-controlled lab identity. No arbitrary production
    # lease or independently supplied "verified" boolean is accepted.
    identity = _identity(invocation=invocation, candidate=candidate,
        attempt=attempt, epoch=epoch, head=head, lease=lease)
    from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as binding
    from scripts.coordination.control_plane.worker_runtime import (
        cf10_r141_held_ipc_bridge_origin_v0_1 as r141,
        cf10_r142_canonical_mcp_child_lineage_v0_1 as r142,
        cf10_r143_git_mcp_capsule_origin_v0_1 as r143,
    )
    try:
        if (type(frozen_source_commit) is not str or frozen_source_commit != head
                or type(spec) is not binding.BoundedInput or type(plan) is not dict
                or type(bridge_pin) is not r141.BridgePin
                or type(child_pin) is not r142.MCPChildPin
                or bridge_pin.closed or child_pin.closed
                or spec.attempt_id != attempt or spec.source_head != head
                or plan.get('identity',{}).get('unit') != identity['unit']
                or bridge_pin.unit != identity['unit'] or child_pin.unit != identity['unit']):
            deny('FROZEN_ORIGIN_IDENTITY')
        post=r141.review_post_release_bridge(held_review=held_review,
            spec=spec,plan=plan,witness=witness,
            bridge_pin=bridge_pin,backend_socket=trusted_mcp)
        origin=r143.review_post_release_git_child(post_review=post,
            bridge_pin=bridge_pin,child_pin=child_pin,
            backend_socket=trusted_mcp,frozen_source_commit=head)
        joined=origin.get('origin') if type(origin) is dict else None
        if (origin.get('schema_version') != r143.SCHEMA
                or origin.get('state') != 'POST_RELEASE_GIT_PINNED_MCP_REVIEW_ONLY'
                or origin.get('root_release_readback_proven') is not False
                or type(joined) is not dict
                or joined.get('source_commit') != head
                or joined.get('unit') != identity['unit']
                or joined.get('bridge_pid') != bridge_pin.pid
                or joined.get('mcp_pid') != child_pin.pid
                or joined.get('capsule_file_count') != len(r143.CAPSULE_FILES)
                or joined.get('mcp_process_transport_lineage_proven') is not True
                or joined.get('git_object_source_verified_by_independent_caller') is not True
                or not isinstance(joined.get('capsule_manifest_sha256'),str)
                or len(joined['capsule_manifest_sha256']) != 64
                or any(joined.get(k) is not False for k in ('live_worker_authorized',
                    'worker_result_accepted','terminal_ledger_written','g1_g5_closed',
                    'copilot_process_tree_proven','copilot_egress_attested',
                    'credential_isolation_attested','automatic_retry'))
                or any(origin.get(k) is not False for k in ('live_worker_authorized',
                    'worker_result_accepted','terminal_ledger_written','g1_g5_closed',
                    'automatic_retry'))):
            deny('R143_ORIGIN_NOT_EXACT_REVIEW')
        # The R140 lab relay is invoked only AFTER the live kernel+source
        # readbacks succeed. Its own R135/revoke checks remain unchanged.
        result=_serve_lab_one(listener=listener,trusted_mcp=trusted_mcp,
            invocation=invocation,candidate=candidate,attempt=attempt,
            epoch=epoch,head=head,lease=lease,timeout_seconds=timeout_seconds)
        if (type(result) is not dict or result.get('lease_revoked') is not True
                or result.get('session_read_only_calls') != 1
                or any(result.get(k) is not False for k in ('live_worker_authorized',
                    'worker_result_accepted','terminal_ledger_written','g1_g5_closed',
                    'automatic_retry'))):
            deny('SESSION_RETURN_NOT_SEALED')
        return {**result,
            'schema_version':'cf10_r144_origin_bound_ipc_handoff_v0_1',
            'state':'LAB_ONE_MCP_CALL_WITH_ROOT_GIT_PIDFD_ORIGIN_REVIEW_ONLY',
            'backend_lineage_independently_proven':True,
            'mcp_source_sha256':joined['mcp_blob_sha256'],
            'capsule_manifest_sha256':joined['capsule_manifest_sha256'],
            'mcp_pid':child_pin.pid,
            'root_release_readback_proven':False,
            'copilot_process_tree_proven':False,
            'copilot_egress_attested':False,
            'credential_isolation_attested':False,
            'kernel_terminal_proven':False,
            'g1_g5_closed':False,
            'live_worker_authorized':False,
            'worker_result_accepted':False,
            'terminal_ledger_written':False,
            'automatic_retry':False}
    except BaseException as exc:
        # Fail closed even if no client was ever accepted. A revoked lease does
        # not prove kernel quiescence. R133/KernelWitness still mandatory.
        try:
            _revoke_on_hold(lease=lease,identity=identity)
        except BrokerHold as fence_exc:
            raise BrokerHold('CF10_R144_HOLD_REVOKE_UNKNOWN_KERNEL_QUARANTINE_REQUIRED') from fence_exc
        raise BrokerHold('CF10_R144_HOLD_ORIGIN_OR_SESSION_KERNEL_QUARANTINE_REQUIRED') from exc


def source_check() -> int:
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend
    if backend.LIVE_CUTOVER_ENABLED is not False:
        deny('SOURCE_LIVE_GATE_DRIFT')
    if SOCKET_NAME != 'mcp.sock' or MAX_ACCEPT != 30:
        deny('SOURCE_CONSTANT_DRIFT')
    if lease_lib.CAPSULE_ID != identity_capsule():
        deny('SOURCE_CAPSULE_DRIFT')
    print('CF10_R140_ROOT_IPC=BOUNDED_LAB_LEASE_ONLY_NO_PRODUCTION_LISTENER')
    if not callable(serve_one) or not callable(_serve_lab_one) or serve_one is _serve_lab_one:
        deny('R144_PUBLIC_GUARD_NOT_INSTALLED')
    print('CF10_R140_BACKEND_ORIGIN=R144_GUARDED_LAB_PREFORWARD_GIT_PIDFD_JOIN')
    print('CF10_R144_PREFORWARD=REQUIRES_R141_R143_LIVE_KERNEL_GIT_PIDFD_BEFORE_IPC')
    print('CF10_R140_G1_G5=OPEN_NO_LIVE_ADMISSION')
    return 0


def identity_capsule() -> str:
    from scripts.coordination.control_plane.worker_runtime import cf10_r129_canonical_lifecycle_convergence_v0_1 as r129
    return r129.CAPSULE


def main(argv=None):
    ap = argparse.ArgumentParser(description='R140 source-only broker readiness check')
    ap.add_argument('--mode', choices=['source-check'], required=True)
    ap.parse_args(argv)
    return source_check()


if __name__ == '__main__':
    raise SystemExit(main())
