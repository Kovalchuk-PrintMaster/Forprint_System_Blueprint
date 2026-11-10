#!/usr/bin/env python3
"""R142: root-only kernel lineage of a canonical MCP child behind R141 bridge.

SOURCE-ONLY and NON-AUTHORIZING.  Uses the already pinned R141 bridge, one
observed direct child, real pidfd, /proc kernel credentials/cgroup/argv and
both inherited stdio pipes.  No spawn, claim, systemd, Worker, lease, ledger
writes, credential access, network or release.  Caller supplies independently
frozen source SHA and argv, not values accepted from MCP output.

This establishes *process and stdio transport lineage*, not isolation of
Copilot's tools, credential access, network, or an all-processes kill proof.
"""
from __future__ import annotations

from dataclasses import dataclass
import argparse
import os
from pathlib import Path
import re
import select
import stat
import socket

from scripts.coordination.control_plane import cf10_supervisor_binding_candidate_v0_1 as binding
from scripts.coordination.control_plane.worker_runtime import (
    cf10_r141_held_ipc_bridge_origin_v0_1 as bridge_lib,
    cf10_r135_ipc_session_fence_v0_1 as session,
    cf10_systemd_launcher_v0_1 as launcher,
)

SCHEMA = 'cf10_r142_canonical_mcp_child_lineage_v0_1'
REL_MCP = 'source_capsule/scripts/coordination/control_plane/worker_runtime/worker_validation_mcp.py'
HEX64 = re.compile(r'[0-9a-f]{64}\Z')
PIPE = re.compile(r'pipe:\[(\d+)\]\Z')
MAX_ARGV_BYTES = 8192
MAX_PROC = 65536

class ChildHold(RuntimeError):
    pass

def deny(reason: str) -> None:
    raise ChildHold('CF10_R142_HOLD_' + reason)


def _bounded_proc(path: str, limit: int = MAX_PROC) -> bytes:
    try:
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            raw = os.read(fd, limit + 1)
        finally:
            os.close(fd)
    except OSError:
        deny('PROC_READ_UNAVAILABLE')
    if not raw or len(raw) > limit:
        deny('PROC_READ_SIZE')
    return raw


def _children(pid: int) -> tuple[int, ...]:
    """Exact direct-child census. Use /proc task children, or bounded proc scan.

    Some kernels/containers omit /proc/PID/task/PID/children. In that case
    enumerate kernel /proc/PID/stat parents; never use a Worker-supplied PID.
    The root caller rechecks immediately before IPC forwarding.
    """
    path=f'/proc/{pid}/task/{pid}/children'
    if os.path.isfile(path):
        raw=_bounded_proc(path,2048)
        try:
            children=tuple(int(x) for x in raw.decode('ascii').split())
        except (UnicodeError,ValueError):
            deny('CHILDREN_FORMAT')
    else:
        children=[]
        try:
            names=os.listdir('/proc')
        except OSError:
            deny('PROC_CENSUS_UNAVAILABLE')
        numeric=[int(n) for n in names if n.isdigit()]
        if len(numeric)>16384:
            deny('PROC_CENSUS_TOO_MANY')
        for candidate in numeric:
            if candidate == pid:
                continue
            try:
                parent,_=_proc_ppid_ticks(candidate)
            except ChildHold:
                # A transient vanished process cannot be a live child.
                if not os.path.exists(f'/proc/{candidate}'):
                    continue
                deny('PROC_CENSUS_INCOMPLETE')
            if parent == pid:
                children.append(candidate)
        children=tuple(sorted(children))
    if len(children)!=1 or children[0]<2 or children[0]==pid:
        deny('EXACT_ONE_DIRECT_CHILD_REQUIRED')
    return children


def _proc_ppid_ticks(pid: int) -> tuple[int, str]:
    raw = _bounded_proc(f'/proc/{pid}/stat', 8192)
    if not raw.startswith(str(pid).encode() + b' ('):
        deny('STAT_PID_FORMAT')
    p = raw.rfind(b') ')
    if p < 1:
        deny('STAT_COMM_FORMAT')
    fields = raw[p+2:].split()
    if len(fields) < 20 or not fields[1].isdigit() or not fields[19].isdigit():
        deny('STAT_FIELDS')
    return int(fields[1]), fields[19].decode('ascii')


def _proc_ids(pid: int) -> tuple[int, int]:
    raw = _bounded_proc(f'/proc/{pid}/status', 65536)
    info = {}
    for line in raw.splitlines():
        if line.startswith((b'Uid:', b'Gid:')):
            k,_,rest = line.partition(b':')
            try:
                v = tuple(int(x) for x in rest.split())
            except ValueError:
                deny('PROC_CREDS_FORMAT')
            if len(v) != 4 or len(set(v)) != 1:
                deny('PROC_CREDS_NOT_UNIFORM')
            info[k] = v[0]
    if set(info) != {b'Uid', b'Gid'}:
        deny('PROC_CREDS_MISSING')
    return info[b'Uid'], info[b'Gid']


def _pipe_link(pid: int, fd: int) -> str:
    if type(pid) is not int or pid < 2 or type(fd) is not int or fd < 0:
        deny('PIPE_FD')
    try:
        value = os.readlink(f'/proc/{pid}/fd/{fd}')
    except OSError:
        deny('PIPE_FD_UNAVAILABLE')
    if not PIPE.fullmatch(value):
        deny('STDIO_NOT_KERNEL_PIPE')
    return value


def _transport(bridge_pid: int, child_pid: int) -> tuple[str, str]:
    in_pipe = _pipe_link(child_pid, 0)
    out_pipe = _pipe_link(child_pid, 1)
    if in_pipe == out_pipe:
        deny('DUPLICATED_STDIO_PIPE')
    try:
        names = list(os.scandir(f'/proc/{bridge_pid}/fd'))
    except OSError:
        deny('PARENT_FD_UNAVAILABLE')
    if len(names) > 128:
        deny('PARENT_FD_UNBOUNDED')
    seen = {in_pipe: 0, out_pipe: 0}
    for entry in names:
        if not entry.name.isdigit():
            deny('PARENT_FD_FORMAT')
        try:
            link = os.readlink(entry.path)
        except FileNotFoundError:
            deny('PARENT_FD_RACE')
        if link in seen:
            seen[link] += 1
    if any(value != 1 for value in seen.values()):
        deny('PARENT_STDIO_PIPE_MISMATCH')
    return in_pipe, out_pipe


def _frozen_argv(*, argv: tuple[str, ...], executable: Path, source: Path,
                 bridge_pin: bridge_lib.BridgePin) -> None:
    if (type(argv) is not tuple or len(argv) != 16 or
        any(type(x) is not str or not x or '\0' in x for x in argv) or
        sum(len(x.encode('utf8'))+1 for x in argv) > MAX_ARGV_BYTES):
        deny('FROZEN_CHILD_ARGV_SIZE')
    lab = bridge_pin.source.parent
    if (source != lab/REL_MCP or argv[:4] != (str(executable), '-I', '-B', str(source)) or
        argv[4] != '--attempt-id' or argv[6] != '--task-id' or
        argv[8] != '--work-front-id' or argv[10] != '--decision-id' or
        argv[12] != '--workspace-repo' or argv[14] != '--evidence-root' or
        not HEX64.fullmatch(argv[11])):
        deny('FROZEN_CANONICAL_MCP_ARGV')
    for idx in (13,15):
        path = Path(argv[idx])
        if (not path.is_absolute() or '..' in path.parts or
            not path.is_relative_to(lab) or str(path) != str(path.resolve())):
            deny('FROZEN_CHILD_WORKSPACE_EVIDENCE_SCOPE')


def _pidfd_alive(fd: int) -> bool:
    try:
        poll = select.poll()
        poll.register(fd, select.POLLIN | select.POLLERR | select.POLLHUP)
        return not poll.poll(0)
    except (OSError,ValueError):
        return False


@dataclass
class MCPChildPin:
    pid: int
    pidfd: int
    bridge_pid: int
    unit: str
    start_ticks: str
    exe_dev_ino: tuple[int,int]
    source: Path
    source_inode: tuple[int,int,int,str]
    argv: tuple[str,...]
    pipes: tuple[str,str]
    closed: bool=False

    def close(self) -> None:
        if not self.closed:
            os.close(self.pidfd)
            self.closed=True


def pin_mcp_child(*, bridge_pin: bridge_lib.BridgePin, backend_socket: socket.socket,
                  executable: Path, source: Path, source_sha256: str,
                  frozen_argv: tuple[str,...]) -> MCPChildPin:
    """Discover one child under the R141 PIDFD-pinned bridge, never trust child PID text."""
    if os.geteuid() != 0:
        deny('ROOT_REQUIRED')
    if (type(bridge_pin) is not bridge_lib.BridgePin or bridge_pin.closed or
        type(source_sha256) is not str or not HEX64.fullmatch(source_sha256)):
        deny('BRIDGE_OR_SOURCE_INPUT')
    _frozen_argv(argv=frozen_argv,executable=executable,source=source,bridge_pin=bridge_pin)
    try:
        bridge_lib.verify_bridge_pin(bridge_pin,backend_socket)
    except (bridge_lib.OriginHold,OSError,ValueError,TypeError):
        deny('BRIDGE_NO_LONGER_PINNED')
    observed_children=_children(bridge_pin.pid)
    if len(observed_children)!=1:deny('EXACT_ONE_DIRECT_CHILD_REQUIRED')
    (pid,)=observed_children
    if not hasattr(os,'pidfd_open'):
        deny('PIDFD_UNAVAILABLE')
    try:
        fd = os.pidfd_open(pid,0)
    except OSError:
        deny('CHILD_PIDFD_FAILED')
    try:
        if not _pidfd_alive(fd):
            deny('CHILD_ALREADY_EXITED')
        ppid,start = _proc_ppid_ticks(pid)
        if ppid != bridge_pin.pid:
            deny('CHILD_PARENT_NOT_BRIDGE')
        if _proc_ids(pid) != (binding.UID,binding.GID):
            deny('CHILD_UID_GID')
        try:
            actual_cgroup = session._proc_cgroup(pid)
        except (session.SessionHold,OSError):
            deny('CHILD_CGROUP_UNAVAILABLE')
        if actual_cgroup != '0::/system.slice/' + bridge_pin.unit:
            deny('CHILD_NOT_IN_EXACT_UNIT_CGROUP')
        exe_id = bridge_lib._exe_inode(pid,executable)
        if bridge_lib._proc_argv(pid) != frozen_argv:
            deny('CHILD_ARGV_MISMATCH')
        source_inode = bridge_lib._source_identity(source,source_sha256)
        pipes = _transport(bridge_pin.pid,pid)
        if (_proc_ppid_ticks(pid) != (bridge_pin.pid,start) or
                _children(bridge_pin.pid) != (pid,) or not _pidfd_alive(fd)):
            deny('CHILD_REBOUND_DURING_PIN')
        return MCPChildPin(pid=pid,pidfd=fd,bridge_pid=bridge_pin.pid,
            unit=bridge_pin.unit,start_ticks=start,exe_dev_ino=exe_id,
            source=source,source_inode=source_inode,argv=frozen_argv,pipes=pipes)
    except BaseException:
        os.close(fd)
        raise


def verify_mcp_child(*, child_pin: MCPChildPin, bridge_pin: bridge_lib.BridgePin,
                     backend_socket: socket.socket) -> dict:
    """Read-only recheck immediately before forwarding; no runtime permission implied."""
    if (type(child_pin) is not MCPChildPin or child_pin.closed or
        type(bridge_pin) is not bridge_lib.BridgePin or bridge_pin.closed or
        child_pin.bridge_pid != bridge_pin.pid or child_pin.unit != bridge_pin.unit or
        not _pidfd_alive(child_pin.pidfd)):
        deny('PIN_CLOSED_OR_EXITED')
    try:
        bridge_lib.verify_bridge_pin(bridge_pin,backend_socket)
        if (not _pidfd_alive(child_pin.pidfd) or
            _proc_ppid_ticks(child_pin.pid) != (bridge_pin.pid,child_pin.start_ticks) or
            _children(bridge_pin.pid) != (child_pin.pid,) or
            _proc_ids(child_pin.pid) != (binding.UID,binding.GID) or
            session._proc_cgroup(child_pin.pid) != '0::/system.slice/'+child_pin.unit or
            bridge_lib._exe_inode(child_pin.pid,Path(child_pin.argv[0])) != child_pin.exe_dev_ino or
            bridge_lib._proc_argv(child_pin.pid) != child_pin.argv or
            bridge_lib._source_identity(child_pin.source,child_pin.source_inode[3]) != child_pin.source_inode or
            _transport(bridge_pin.pid,child_pin.pid) != child_pin.pipes):
            deny('CHILD_LINEAGE_CHANGED')
    except (bridge_lib.OriginHold,session.SessionHold,OSError,TypeError,ValueError):
        deny('CHILD_READBACK_UNAVAILABLE')
    return {'schema_version':SCHEMA,'state':'R142_MCP_CHILD_PIDFD_STDIO_ORIGIN_REVIEW_ONLY',
        'unit':child_pin.unit,'bridge_pid':bridge_pin.pid,'mcp_pid':child_pin.pid,
        'mcp_source_sha256':child_pin.source_inode[3],
        'child_pidfd_alive':True,'parent_pidfd_rechecked':True,
        'same_systemd_cgroup':True,'stdio_two_pipes_bound':True,
        'mcp_process_transport_lineage_proven':True,
        'git_object_source_verified_by_independent_caller':False,
        'copilot_process_tree_proven':False,'copilot_egress_attested':False,
        'credential_isolation_attested':False,'live_worker_authorized':False,
        'worker_result_accepted':False,'terminal_ledger_written':False,
        'automatic_retry':False,'g1_g5_closed':False}


def review_post_release_child(*, post_review: dict, child_pin: MCPChildPin,
                              bridge_pin: bridge_lib.BridgePin,
                              backend_socket: socket.socket) -> dict:
    """Join R141 POST bridge review to independently pinned child; no R030 authority."""
    if (type(post_review) is not dict or
        post_review.get('schema_version') != bridge_lib.SCHEMA or
        post_review.get('state') != 'POST_RELEASE_BRIDGE_PINNED_PRE_IPC_REVIEW_ONLY' or
        post_review.get('backend_bridge_origin_pinned') is not True or
        post_review.get('bridge_pid') != bridge_pin.pid or
        post_review.get('unit') != bridge_pin.unit or
        post_review.get('root_release_readback_proven') is not False or
        any(post_review.get(k) is not False for k in ('canonical_mcp_child_independently_proven',
            'terminal_ledger_written','g1_g5_closed','live_worker_authorized',
            'worker_result_accepted','automatic_retry'))):
        deny('R141_POST_PROOF_INVALID')
    record = verify_mcp_child(child_pin=child_pin,bridge_pin=bridge_pin,
                              backend_socket=backend_socket)
    return {'schema_version':SCHEMA,'state':'POST_RELEASE_MCP_PROCESS_TRANSPORT_ORIGIN_REVIEW_ONLY',
        'unit':bridge_pin.unit,'bridge_pid':bridge_pin.pid,'mcp_pid':child_pin.pid,
        'mcp_lineage':record,'root_release_readback_proven':False,
        'canonical_mcp_child_independently_proven':False,
        'g1_g5_closed':False,'live_worker_authorized':False,
        'worker_result_accepted':False,'terminal_ledger_written':False,
        'automatic_retry':False}


def source_check() -> int:
    if (launcher.LIVE_CUTOVER_ENABLED is not False or
        not hasattr(os,'pidfd_open') or
        REL_MCP != 'source_capsule/scripts/coordination/control_plane/worker_runtime/worker_validation_mcp.py'):
        deny('SEALED_SOURCE_CHECK')
    print('CF10_R142_CHILD=PIDFD_DIRECT_PARENT_STDIN_STDOUT_EXACT_CGROUP_REVIEW_ONLY')
    print('CF10_R142_GIT_HEAD_SOURCE=INDEPENDENT_CALLER_PROOF_REQUIRED')
    print('CF10_R142_R030_RELEASE=NOT_MODIFIED')
    print('CF10_R142_G1_G5=OPEN_NO_LIVE_ADMISSION')
    return 0


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode',choices=('source-check',),required=True)
    parser.parse_args()
    try:
        return source_check()
    except ChildHold as exc:
        print(str(exc))
        return 3

if __name__ == '__main__':
    raise SystemExit(main())
