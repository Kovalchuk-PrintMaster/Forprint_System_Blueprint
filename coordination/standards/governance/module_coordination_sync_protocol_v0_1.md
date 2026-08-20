# ForPrint Module Coordination Sync Protocol v0.1

Status: active standard / v0.4.1 hardening

## Purpose

This protocol defines the canonical module-side freshness and prompt
notification workflow for Blueprint-driven work.

It supersedes the legacy assumption that a module should update the Blueprint
repository with `git pull`.

## Canonical commands

```text
make coordination-sync-check
make prompt-notify
make module-sync
make module-start
```

`coordination-sync-check` is an explicit network read-only freshness check.

`prompt-notify` is a local read-only prompt availability projection.

`module-sync` synchronizes already-readable Blueprint inputs into module-owned
snapshots. It does not use the network and never writes Blueprint.

`module-start` is the canonical prompt-driven startup:

```text
coordination-sync-check
module-sync
module-status
prompt-notify
prompt-read-next
```

## Freshness states

```text
CURRENT
STALE
NETWORK_UNAVAILABLE
REMOTE_BRANCH_NOT_FOUND
```

Only `CURRENT` passes the freshness gate.

The preferred remote read is `git ls-remote`. The check must not use `git
fetch`, `git pull`, or update remote-tracking refs.

If Blueprint is stale, the module stops. Blueprint is updated only from inside
the Blueprint repository, then `module-start` is rerun.

## Prompt notification states

```text
READY_PROMPT
NO_READY_PROMPT
MULTIPLE_READY_PROMPTS
```

Exactly one `ready_for_module_pull` prompt is normal executable readiness.

`NO_READY_PROMPT` is advisory and never fabricates work.

`MULTIPLE_READY_PROMPTS` is a coordination error.

Notification does not create H3 `CLAIMED`. CLAIMED is emitted only after the
module actually accepts the prompt into work.

## Deterministic checks

These remain network-independent:

```text
make check
make governance-check
make module-validate
Blueprint make check
```

Network freshness is not a dependency of them.

## Legacy blueprint-pull

`blueprint-pull` is no longer a canonical module workflow command.

A module may temporarily retain a fail-closed compatibility stub, but that
target must not perform Git mutation.

Older standards that define module-side `blueprint-pull` as `git pull` are
superseded by this protocol and the current module Makefile template.

## Repository boundary

The module uses a module-owned copy of the coordination sync checker.

Blueprint stores the reference implementation at:

```text
coordination/templates/module_coordination_sync_check_v0_1.py
```

During rollout this reference is copied/adapted into each module as:

```text
scripts/coordination_sync_check.py
```

Modules do not execute Blueprint Python code directly.

The checker may read Blueprint Git metadata, the origin URL, the remote branch
head through `git ls-remote`, and the module's Prompt Queue v0.2.

It must not:

```text
git fetch;
git pull;
write Blueprint;
write module files;
create CLAIMED;
mutate Prompt Queue;
perform ACCEPT / RETURN / HOLD;
select or activate a next prompt.
```

## Rollout

H4 defines the canonical contract, reference implementation, template, and
tests. External module adoption is a later rollout step.
