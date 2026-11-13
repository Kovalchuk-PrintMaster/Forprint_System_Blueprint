"""Read-only observation of cgroup v2 state; never a process-quiescence receipt.

An empty cgroup.events observation is NOT proof that a process couldn't escape
its cgroup or leave open file descriptors. Production launch must bind trusted
pre-claim, enforced unit membership, lifecycle and independent reviewer.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import stat
from typing import Mapping

class QuiescenceObservationBlocked(ValueError):
    pass


def parse_events(raw: str) -> Mapping[str, int]:
    if not isinstance(raw, str) or len(raw) > 8192:
        raise QuiescenceObservationBlocked('CF10_EVENTS_INVALID')
    fields: dict[str,int] = {}
    for line in raw.splitlines():
        parts = line.split()
        if len(parts) != 2 or not parts[0].replace('_','').isalnum() or parts[0] in fields or parts[1] not in ('0','1'):
            raise QuiescenceObservationBlocked('CF10_EVENTS_INVALID')
        fields[parts[0]] = int(parts[1])
    if 'populated' not in fields:
        raise QuiescenceObservationBlocked('CF10_EVENTS_POPULATED_MISSING')
    return fields


def observe_cgroup_events(*, directory: Path, expected_root: Path) -> dict:
    """Read-only; never asserts containment or authorizes subsequent snapshot."""
    expected_root = Path(expected_root)
    directory = Path(directory)
    if not expected_root.is_absolute() or not directory.is_absolute() or not directory.is_relative_to(expected_root) or directory == expected_root:
        raise QuiescenceObservationBlocked('CF10_CGROUP_SCOPE_UNBOUND')
    if any(part in ('.','..') for part in directory.parts):
        raise QuiescenceObservationBlocked('CF10_CGROUP_SCOPE_UNSAFE')
    if directory.is_symlink():
        raise QuiescenceObservationBlocked('CF10_CGROUP_SYMLINK')
    st = directory.lstat()
    if not stat.S_ISDIR(st.st_mode):
        raise QuiescenceObservationBlocked('CF10_CGROUP_NOT_DIRECTORY')
    event_file = directory/'cgroup.events'
    if event_file.is_symlink():
        raise QuiescenceObservationBlocked('CF10_EVENTS_SYMLINK')
    fd = os.open(event_file, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        fst = os.fstat(fd)
        if not stat.S_ISREG(fst.st_mode) or fst.st_size > 8192:
            # cgroup pseudo-files often have size zero; that's expected.
            raise QuiescenceObservationBlocked('CF10_EVENTS_NOT_REGULAR')
        raw = os.read(fd, 8193)
        if len(raw) > 8192:
            raise QuiescenceObservationBlocked('CF10_EVENTS_OVERSIZE')
        events = parse_events(raw.decode('ascii'))
    finally:
        os.close(fd)
    return {
        'schema':'cf10_cgroup_read_only_observation_v0_1',
        'populated_observed': events['populated'],
        'empty_observed': events['populated'] == 0,
        'cgroup_containment_proven': False,
        'escape_protection_proven': False,
        'process_quiescence_proven': False,
        'root_controlled_lifecycle_receipt': False,
        'dispatch_authorized': False,
    }
