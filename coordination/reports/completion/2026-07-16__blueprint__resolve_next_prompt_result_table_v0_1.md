# Blueprint Resolve Next Prompt Result Table v0.1 — Completion Record

## Date

2026-07-16

## Scope

```text
add shared next-prompt metadata renderer;
delegate resolve_next_prompt metadata presentation;
preserve path-only, failure and read-content contracts;
update reporting consolidation baseline;
add architecture, runbook, recovery and regression tests.
```

## Runtime baseline before implementation

```text
default_summary:
rc=0
stdout_lines=7
stderr_lines=0
box=false
ansi=false
sha256=839ac89af5da32645593e40382d4364ca7c63e9b397bd702d25091b811d6787d

path_only:
rc=0
stdout_lines=1
stderr_lines=0
sha256=c818c8df4de9446d7f25170fb3960e8b77e13a3c2ec97bb8c59d1fdd1bbfc7b9

read:
rc=0
stdout_lines=350
stderr_lines=0
sha256=7c853960aa97d043890e870f4a1e9c5feaf81fa4b871a5cbdcc4aafa778fe2b1

invalid_module:
rc=1
stdout_lines=1
stderr_lines=0
sha256=fef5e1d6844eae552b7affe2e5470195ef6d5f21cc16e5f766621689421b81ea
```

## Allowed presentation change

Only default/read metadata presentation changes from seven plain lines to a
shared boxed result table.

## Preserved byte contracts

```text
path-only stdout/stderr/exit code;
invalid-module stdout/stderr/exit code;
prompt body after the 80-character separator;
read-only behavior.
```

## Next planning step

```text
blueprint_module_governance_terminal_artifact_split_v0_1
```
