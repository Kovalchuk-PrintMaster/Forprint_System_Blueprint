"""CF10 R135: bounded root-side IPC session fence using R126/R127/R134.

Candidate transport component, NOT an independently executable broker or
production entrypoint. The caller must supply already-authenticated sockets
and a trusted MCP transport; this module NEVER creates a listener, launches
an MCP subprocess, starts a Worker or writes a terminal ledger event.

R126's lease remains disposable /run/forprint-cf10-r125-*; the current R115
preclaim still rejects the IPC proxy. If external revoke occurs while a tool
is already running, response is suppressed and a kernel quarantine is
REQUIRED: this fence does not claim it killed the in-flight process.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import select
import socket
import struct
import time
from collections.abc import Mapping

from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as bind
from scripts.coordination.control_plane.worker_runtime import (
    cf10_r126_root_external_revoke_v0_1 as r126,
    cf10_r127_mcp_stdio_ipc_proxy_v0_1 as r127_proxy,
    cf10_r129_canonical_lifecycle_convergence_v0_1 as r129,
    cf10_r134_ipc_preclaim_crosswalk_v0_1 as r134,
)

SCHEMA = 'cf10_r135_ipc_session_fence_v0_1'
MAX = r127_proxy.MAX_FRAME
PROTOCOL_PHASES = 4
INTERVAL = 0.05
UNIT_RE = re.compile(r'forprint-cf10-worker-[0-9a-f]{24}\.service\Z')
CGROUP_LINE = re.compile(r'0::/system\.slice/(forprint-cf10-worker-[0-9a-f]{24}\.service)\Z')


class SessionHold(RuntimeError):
    """Always requires operator reconciliation; never signals terminal PASS."""
    def __init__(self, reason: str, *, in_flight: bool = False):
        super().__init__('CF10_R135_HOLD_' + reason)
        self.in_flight = in_flight
        self.quarantine_required = in_flight
        self.worker_result_accepted = False
        self.terminal_success = False
        self.automatic_retry = False


def deny(reason: str, *, in_flight: bool = False) -> None:
    raise SessionHold(reason, in_flight=in_flight)


def _proc_cgroup(pid: int) -> str:
    """Read-only kernel identity, no /proc string supplied by the model."""
    if type(pid) is not int or pid < 2:
        deny('PEER_PID')
    path = '/proc/' + str(pid) + '/cgroup'
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
        try:
            raw = os.read(fd, 2049)
        finally:
            os.close(fd)
        if not raw or len(raw) > 2048 or b'\0' in raw:
            deny('PROC_CGROUP_BYTES')
        return raw.decode('ascii', 'strict').strip()
    except (OSError, UnicodeError):
        deny('PROC_CGROUP_UNAVAILABLE')


def _peer_kernel(conn: socket.socket) -> tuple[int, int, int]:
    try:
        raw = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize('3i'))
        if len(raw) != struct.calcsize('3i'):
            deny('PEER_CREDS_LENGTH')
        return struct.unpack('3i', raw)
    except OSError:
        deny('PEER_CREDS_MISSING')


def verify_peer(conn: socket.socket, *, unit: str) -> dict:
    """SO_PEERCRED plus exact unified cgroup peer identity; not G3 isolation."""
    if not isinstance(conn, socket.socket):
        deny('CLIENT_SOCKET')
    if type(unit) is not str or not UNIT_RE.fullmatch(unit):
        deny('UNIT_FORMAT')
    pid, uid, gid = _peer_kernel(conn)
    if pid < 2 or uid != bind.UID or gid != bind.GID:
        deny('PEER_UID_GID')
    observed = _proc_cgroup(pid)
    # Deliberately require unified v2 and the exact canonical systemd unit.
    if observed != '0::/system.slice/' + unit or not CGROUP_LINE.fullmatch(observed):
        deny('PEER_NOT_IN_CANONICAL_CGROUP')
    return {'uid': uid, 'gid': gid, 'unit': unit, 'cgroup_exact': True,
            'kernel_peer_readback': True, 'g3_process_isolation_attested': False}


def verify_binding(*, invocation: Mapping, candidate: Mapping,
                   expected_attempt: str, expected_epoch: str,
                   expected_head: str, lease_path: Path) -> dict:
    """Check independent caller identity AND the existing R134 source crosswalk."""
    if os.geteuid() != 0:
        deny('ROOT_REQUIRED')
    if not isinstance(lease_path, Path) or not r126.LEASE_RE.fullmatch(str(lease_path)):
        deny('LAB_LEASE_ONLY')
    try:
        review = r134.verify_source_only(invocation=invocation, candidate=candidate)
        c = r129.validate_r127_candidate(candidate)
        unit = bind.unit_for(expected_attempt, expected_head)
    except (r134.IPCPreclaimHold, r129.ConvergenceHold, bind.BoundaryBlocked,
            KeyError, TypeError, ValueError):
        deny('SOURCE_CROSSWALK')
    if (any(type(s) is not str for s in (expected_attempt, expected_epoch, expected_head))
        or c['attempt_id'] != expected_attempt or c['epoch'] != expected_epoch
        or c['source_head'] != expected_head
        or review.get('candidate_sha256') != c['candidate_sha256']
        or review.get('live_cutover_authorized') is not False
        or review.get('legacy_r115_rejects_prospective_argv') is not True):
        deny('FROZEN_IDENTITY')
    if c['candidate_mcp_config']['mcpServers']['ForPrintValidation']['args'][2] != str(lease_path.with_name('mcp.sock')):
        deny('SOCKET_LEASE_BINDING')
    return {'unit': unit, 'attempt_id': expected_attempt, 'epoch': expected_epoch,
            'source_head': expected_head, 'capsule_id': r129.CAPSULE,
            'candidate_sha256': c['candidate_sha256'], 'review_sha256': review['report_sha256']}


def check_lease(*, lease_path: Path, identity: dict, revoked: bool = False,
                in_flight: bool = False) -> None:
    """Never trust a caller's lease dictionary: invoke R126 inode readback."""
    try:
        current = r126.inspect_lease(lease_path, attempt=identity['attempt_id'],
            epoch=identity['epoch'], source_head=identity['source_head'],
            capsule_id=identity['capsule_id'])
    except (r126.ExternalRevokeHold, KeyError, OSError, ValueError, TypeError):
        deny('ROOT_LEASE_UNAVAILABLE', in_flight=in_flight)
    if type(current) is not dict or current.get('revoked') is not revoked:
        deny('ROOT_LEASE_REVOKED_OR_DRIFT', in_flight=in_flight)


class FrameReader:
    def __init__(self):
        self.pending = bytearray()

    def read(self, transport: socket.socket, *, lease: Path, identity: dict,
             deadline: float, in_flight: bool) -> bytes:
        """Bounded newline frame; checks external revoke every 50ms in a wait."""
        while True:
            check_lease(lease_path=lease, identity=identity, in_flight=in_flight)
            if b'\n' in self.pending:
                end = self.pending.index(b'\n') + 1
                if end > MAX:
                    deny('FRAME_OVERSIZE', in_flight=in_flight)
                data = bytes(self.pending[:end]); del self.pending[:end]
                try:
                    r127_proxy.decode(data)
                except r127_proxy.IPCProxyHold:
                    deny('FRAME_INVALID', in_flight=in_flight)
                return data
            if len(self.pending) >= MAX or time.monotonic() >= deadline:
                deny('FRAME_OVERSIZE_OR_TIMEOUT', in_flight=in_flight)
            try:
                readable, _, _ = select.select([transport], [], [],
                    min(INTERVAL, max(0.0, deadline - time.monotonic())))
                if readable:
                    fragment = transport.recv(min(8192, MAX + 1 - len(self.pending)))
                    if not fragment:
                        deny('FRAME_EOF', in_flight=in_flight)
                    self.pending.extend(fragment)
            except (OSError, ValueError):
                deny('FRAME_TRANSPORT', in_flight=in_flight)


def handle_session(*, client: socket.socket, trusted_mcp: socket.socket,
                   invocation: Mapping, candidate: Mapping,
                   expected_attempt: str, expected_epoch: str, expected_head: str,
                   lease_path: Path, timeout_seconds: int = 10) -> dict:
    """One bounded 3-metadata + 1 read-only call through a trusted MCP socket.

    No socket or MCP process is created here. The caller is responsible for
    root-controlled socket provisioning and a complete canonical launch join.
    On revoked in-flight work this raises HOLD/quarantine_required and NEVER
    claims the child was killed. An external R133 controller must quarantine.
    """
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 30:
        deny('SESSION_TIMEOUT')
    if not isinstance(trusted_mcp, socket.socket):
        deny('BACKEND_SOCKET')
    identity = verify_binding(invocation=invocation, candidate=candidate,
        expected_attempt=expected_attempt, expected_epoch=expected_epoch,
        expected_head=expected_head, lease_path=lease_path)
    verify_peer(client, unit=identity['unit'])
    seen: set = set()
    cr, br = FrameReader(), FrameReader()
    forwarded = 0
    for phase in range(PROTOCOL_PHASES):
        check_lease(lease_path=lease_path, identity=identity)
        request = cr.read(client, lease=lease_path, identity=identity,
                          deadline=time.monotonic()+timeout_seconds, in_flight=False)
        try:
            ident = r127_proxy.validate_request(r127_proxy.decode(request), phase, seen)
        except r127_proxy.IPCProxyHold:
            deny('PROTOCOL_DENIED')
        check_lease(lease_path=lease_path, identity=identity)
        try:
            trusted_mcp.sendall(request)
        except OSError:
            deny('TRUSTED_MCP_SEND', in_flight=phase == 3)
        forwarded += 1
        if phase == 1:  # initialized notification has no reply
            continue
        response = br.read(trusted_mcp, lease=lease_path, identity=identity,
                           deadline=time.monotonic()+timeout_seconds,
                           in_flight=phase == 3)
        try:
            validated = r127_proxy.validate_response(r127_proxy.decode(response), ident, phase)
        except r127_proxy.IPCProxyHold:
            deny('TRUSTED_MCP_RESULT_DENIED', in_flight=phase == 3)
        check_lease(lease_path=lease_path, identity=identity, in_flight=phase == 3)
        if phase == 3:
            # Exhaust the lab grant BEFORE returning the only allowed result.
            # R126 readback has its own root ownership checks; external revoke
            # racing this operation must return HOLD and no output.
            try:
                r126.revoke_lease(lease_path, attempt=identity['attempt_id'],
                    epoch=identity['epoch'], source_head=identity['source_head'],
                    capsule_id=identity['capsule_id'])
                check_lease(lease_path=lease_path, identity=identity, revoked=True)
            except (r126.ExternalRevokeHold, SessionHold, OSError, ValueError, KeyError, TypeError):
                deny('FINAL_REVOKE_NOT_PROVEN', in_flight=True)
        try:
            client.sendall(r127_proxy.encode(validated))
        except (OSError, r127_proxy.IPCProxyHold):
            deny('CLIENT_RESPONSE', in_flight=phase == 3)
    return {'schema_version': SCHEMA,
            'state': 'DISPOSABLE_IPC_ONE_READ_ONLY_CALL_REVOKED_REVIEW_ONLY',
            'forwarded_frames': forwarded, 'read_only_calls': 1,
            'lease_exhausted': True, 'root_verified_peer': True,
            'attempt_id': identity['attempt_id'], 'source_head': identity['source_head'],
            'epoch': identity['epoch'], 'unit': identity['unit'],
            'worker_result_accepted': False, 'terminal_ledger_written': False,
            'inflight_kernel_cancellation_proven': False,
            'g1_g5_closed': False, 'live_worker_authorized': False,
            'automatic_retry': False}


def main(argv=None):
    p = argparse.ArgumentParser(description='CF10 R135 read-only source check; no IPC listener')
    p.add_argument('--mode', choices=['source-check'], required=True)
    p.parse_args(argv)
    try:
        from scripts.coordination.control_plane.worker_runtime import cf10_systemd_launcher_v0_1 as launch
        r129.verify_pinned_seams(r129.REPO)
        if launch.LIVE_CUTOVER_ENABLED is not False:
            deny('LIVE_GATE_DRIFT')
        if r127_proxy.CAPABILITY != 'run_repo_head' or len(r127_proxy.METHODS) != 4:
            deny('PROTOCOL_DRIFT')
        print('CF10_R135_ROOT_IPC=SOURCE_ONLY_NO_LISTENER_NO_WORKER')
        print('CF10_R135_INFLIGHT_REVOKE=SUPPRESS_RESPONSE_HOLD_KERNEL_QUARANTINE_REQUIRED')
        print('CF10_R135_G1_G5=OPEN_NO_LIVE_ADMISSION')
        return 0
    except (SessionHold, r129.ConvergenceHold, OSError, KeyError, ValueError, TypeError):
        print('CF10_R135=HOLD_SOURCE_RECONCILE')
        return 3


if __name__ == '__main__':
    raise SystemExit(main())
