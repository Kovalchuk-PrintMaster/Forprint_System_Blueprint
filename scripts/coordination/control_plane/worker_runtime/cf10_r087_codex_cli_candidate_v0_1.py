"""CF10 R087: Codex CLI non-authorizing source-only adapter candidate.

NOT wired into R081's _SOURCE_BOUND_ADAPTERS. Not a READY provider. This
module never executes a command, checks credentials, creates an attempt,
launches a process, claims an owner receipt, or accepts Handoff results.

The argv is an illustrative frozen command contract for future independent
sandbox/CLI/auth verification. The CLI is not run by this module.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

SCHEMA = 'cf10_r087_codex_cli_candidate_v0_1'
EVENT_SCHEMA = 'cf10_r087_codex_jsonl_observation_candidate_v0_1'
PROVIDER = 'openai_codex_cli'
MODEL = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{1,79}\Z')
ATTEMPT = re.compile(r'cf10-[A-Za-z0-9_-]{3,80}-a[0-9]{3,5}\Z')
WORKER = re.compile(r'worker-[0-9]{2}\Z')
HEAD = re.compile(r'[a-f0-9]{40}\Z')
SHA = re.compile(r'[a-f0-9]{64}\Z')
EVENTS = frozenset((
    'thread.started', 'turn.started', 'turn.completed', 'turn.failed',
    'item.started', 'item.updated', 'item.completed', 'error',
))
MAX_PROMPT_BYTES = 160_000
MAX_JSONL_BYTES = 1_048_576
MAX_JSONL_LINES = 2048
MAX_LINE_BYTES = 65_536


class CodexCandidateBlocked(ValueError):
    pass


def deny(reason: str) -> None:
    raise CodexCandidateBlocked('CF10_R087_' + reason)


def _strict_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.startswith('/') or '\x00' in value or '\n' in value or '\r' in value:
        deny('PATH_INVALID_' + label)
    path = PurePosixPath(value)
    if '..' in value.split('/') or '.' in value.split('/') or '//' in value or str(path) != value or value == '/':
        deny('PATH_NOT_NORMALIZED_' + label)
    return value


def _assert_false(binding: Mapping, *keys: str) -> None:
    if any(binding.get(k) is not False for k in keys):
        deny('AUTHORITY_BOUNDARY')


def inspect_readiness(binding: Mapping) -> dict[str, Any]:
    if not isinstance(binding, Mapping) or binding.get('provider_id') != PROVIDER:
        deny('PROVIDER_ID_MISMATCH')
    return {
        'schema_version': SCHEMA,
        'provider_id': PROVIDER,
        'source_adapter_candidate_available': True,
        'registered_state': 'NOT_CONFIGURED',
        'provider_ready': False,
        'cli_installed_or_verified': False,
        'provider_auth_verified': False,
        'live_dispatch_wired': False,
        'execution_authorized': False,
        'worker_launched': False,
    }


def build_invocation(binding: Mapping, frozen_task: Mapping) -> dict[str, Any]:
    """Render a non-executable ARGV_NO_SHELL draft; stdin is NOT opened.

    Caller MUST supply exact workspace under the given attempt runtime, frozen
    HEAD, task prompt and an explicitly selected model. No implicit model or
    provider default; no shell, network access, privilege or extra directories.
    """
    if not isinstance(binding, Mapping) or not isinstance(frozen_task, Mapping):
        deny('BINDING_OR_TASK_MISSING')
    if binding.get('provider_id') != PROVIDER:
        deny('PROVIDER_ID_MISMATCH')
    _assert_false(binding, 'execution_authorized', 'provider_ready', 'claim_consumed',
                  'automatic_fallback', 'automatic_retry')
    model = binding.get('model_id')
    if not isinstance(model, str) or not MODEL.fullmatch(model) or model == 'auto':
        deny('EXPLICIT_MODEL_REQUIRED')
    attempt = binding.get('attempt_id')
    worker = binding.get('worker_id')
    head = binding.get('source_head')
    if not isinstance(attempt, str) or not ATTEMPT.fullmatch(attempt):
        deny('ATTEMPT_ID_INVALID')
    if not isinstance(worker, str) or not WORKER.fullmatch(worker):
        deny('WORKER_ID_INVALID')
    if not isinstance(head, str) or not HEAD.fullmatch(head):
        deny('SOURCE_HEAD_INVALID')
    executable = _strict_path(binding.get('executable'), 'EXECUTABLE')
    runtime = _strict_path(binding.get('runtime_root'), 'RUNTIME_ROOT')
    workspace = _strict_path(binding.get('workspace'), 'WORKSPACE')
    expected = runtime + '/forprint_system_blueprint/' + worker + '/' + attempt + '/workspace/repo'
    if workspace != expected or workspace.startswith('/srv/software_development/forprint-project/'):
        deny('ATTEMPT_ISOLATION_REQUIRED')
    prompt = frozen_task.get('prompt')
    if not isinstance(prompt, str) or not prompt.strip() or '\x00' in prompt:
        deny('FROZEN_PROMPT_INVALID')
    encoded = prompt.encode('utf-8')
    if len(encoded) > MAX_PROMPT_BYTES:
        deny('PROMPT_OVERSIZE')
    digest = hashlib.sha256(encoded).hexdigest()
    pinned = frozen_task.get('prompt_sha256')
    if pinned is not None and (not isinstance(pinned, str) or not SHA.fullmatch(pinned) or pinned != digest):
        deny('FROZEN_PROMPT_SHA_DRIFT')
    if frozen_task.get('result_transport') != 'CANONICAL_HANDOFF_PENDING_ADAPTER_PROOF':
        deny('RESULT_TRANSPORT_NOT_BOUND')
    # read-only is deliberately not a workable editing Worker. Later migration
    # must separately review workspace-write, network, MCP and auth boundaries.
    argv = [executable, 'exec', '--json', '--ephemeral',
            '--ignore-user-config', '--ignore-rules',
            '--sandbox', 'read-only', '--model', model, '--cd', workspace, '-']
    argv_sha = hashlib.sha256(json.dumps(argv, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
    return {
        'schema_version': SCHEMA,
        'provider_id': PROVIDER,
        'attempt_id': attempt,
        'worker_id': worker,
        'source_head': head,
        'model_id': model,
        'argv': argv,
        'argv_sha256': argv_sha,
        'command_representation': 'ARGV_NO_SHELL',
        'stdin_transport': 'UNOPENED_PIPE_PLACEHOLDER',
        'prompt_sha256': digest,
        'sandbox': 'read-only',
        'jsonl_capture': 'CANDIDATE_OBSERVATION_ONLY',
        'no_user_config_or_rules': True,
        'provider_ready': False,
        'candidate_only': True,
        'adapter_grants_authority': False,
        'claim_consumed': False,
        'process_started': False,
        'result_accepted': False,
        'automatic_fallback': False,
        'automatic_retry': False,
    }


def observe_jsonl_candidate(provider_stream: bytes, binding: Mapping) -> dict[str, Any]:
    """Sanitized untrusted JSONL *observation*; NEVER accepted Handoff evidence.

    The raw stream must remain in its designated (future) worker evidence
    transport, not be stored in canonical ledgers or used for acceptance.
    """
    if not isinstance(binding, Mapping) or binding.get('provider_id') != PROVIDER:
        deny('PROVIDER_ID_MISMATCH')
    if not isinstance(provider_stream, bytes) or not provider_stream or len(provider_stream) > MAX_JSONL_BYTES:
        deny('JSONL_MISSING_OR_OVERSIZE')
    raw_lines = provider_stream.splitlines()
    if not raw_lines or len(raw_lines) > MAX_JSONL_LINES:
        deny('JSONL_LINE_COUNT')
    event_counts: dict[str, int] = {}
    for line in raw_lines:
        if not line or len(line) > MAX_LINE_BYTES:
            deny('JSONL_LINE_INVALID')
        try:
            event = json.loads(line)
        except (ValueError, UnicodeDecodeError, TypeError):
            deny('JSONL_INVALID')
        kind = event.get('type') if isinstance(event, dict) else None
        if kind not in EVENTS:
            deny('JSONL_EVENT_UNKNOWN')
        event_counts[kind] = event_counts.get(kind, 0) + 1
    if event_counts.get('turn.failed', 0) or event_counts.get('error', 0):
        deny('JSONL_PROVIDER_ERROR_OR_FAILURE')
    if event_counts.get('turn.completed', 0) != 1:
        deny('JSONL_INCOMPLETE_OR_DUPLICATE_TURN')
    return {
        'schema_version': EVENT_SCHEMA,
        'provider_id': PROVIDER,
        'stream_sha256': hashlib.sha256(provider_stream).hexdigest(),
        'event_counts': dict(sorted(event_counts.items())),
        'source_is_untrusted': True,
        'jsonl_observation_only': True,
        'handoff_result_validated': False,
        'result_accepted': False,
        'canonical_ledger_written': False,
        'worker_launched': False,
    }


class CodexCliCandidateAdapter:
    def inspect_readiness(self, binding: Mapping) -> Mapping:
        return inspect_readiness(binding)

    def build_invocation(self, binding: Mapping, frozen_task: Mapping) -> Mapping:
        return build_invocation(binding, frozen_task)

    def normalize_result_candidate(self, provider_stream: bytes, binding: Mapping) -> Mapping:
        # No Codex stream directly satisfies Handoff v2; provenance must be
        # independently verified by canonical WorkerResultReturn + R037.
        deny('CANONICAL_HANDOFF_NORMALIZATION_NOT_IMPLEMENTED')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('inspect',), required=True)
    parser.parse_args(argv)
    print(json.dumps(inspect_readiness({'provider_id': PROVIDER}), sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
