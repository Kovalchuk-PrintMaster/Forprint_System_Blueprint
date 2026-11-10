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


def serve_one(*, listener: socket.socket, trusted_mcp: socket.socket,
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


def source_check() -> int:
    from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as backend
    if backend.LIVE_CUTOVER_ENABLED is not False:
        deny('SOURCE_LIVE_GATE_DRIFT')
    if SOCKET_NAME != 'mcp.sock' or MAX_ACCEPT != 30:
        deny('SOURCE_CONSTANT_DRIFT')
    if lease_lib.CAPSULE_ID != identity_capsule():
        deny('SOURCE_CAPSULE_DRIFT')
    print('CF10_R140_ROOT_IPC=BOUNDED_LAB_LEASE_ONLY_NO_PRODUCTION_LISTENER')
    print('CF10_R140_BACKEND_ORIGIN=REQUIRES_INDEPENDENT_CANONICAL_MCP_PROOF')
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
