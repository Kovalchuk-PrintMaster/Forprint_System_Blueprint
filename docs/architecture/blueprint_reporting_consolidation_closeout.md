# Blueprint Reporting Consolidation Closeout

## Status

Closed at `reporting_consolidation_closed_v0_1`.

## Scope

The closeout covers terminal presentation, detailed report artifacts, canonical
Make contracts, module assistant obligations, completion evidence and the
reporting consumer registry.

## Source of truth

| Concern | Source |
|---|---|
| Shared reporting registry | `scripts/reporting/audit_consolidation.py` |
| Module Make template | `coordination/templates/module_makefile_standard.template.mk` |
| Make governance rules | `coordination/standards/module_governance_make_targets.md` |
| Make command behavior | `coordination/standards/make_command_standard.md` |
| Public Make compatibility | `coordination/standards/module_make_target_contract.md` |
| Assistant obligations | `coordination/module_policy/README.md` |
| Completion evidence | `tools/completion_packet_template/README.md` |
| Compact output directive | `coordination/directives/global/active/2026-07-14__global__directive__compact-report-output-v0-1.md` |

## Verified registry

- 16 configured targets;
- 7 shared reporting core files;
- 9 consolidated consumers;
- 0 action-required entries;
- 0 manual-review entries;
- no current intentional special cases.

## Terminal and artifact boundary

Routine operator commands use compact terminal summaries. Detailed JSON and
Markdown artifacts remain the diagnostics source when they exist. ANSI
presentation is optional and must respect `NO_COLOR=1`.

Machine schemas, target names, CLI flags, stdout/stderr ownership and exit
codes are compatibility contracts.

## Command mutation boundary

Read-only commands include `coordination-check`, `module-policy-check` and
audits explicitly documented as read-only.

`coordination-fix`, Blueprint pull/synchronization commands and composite
targets that invoke them may mutate documented coordination state.

`check-report` may write its documented report artifacts but does not gain
permission to mutate unrelated coordination state.

## Future consumer registration

A future reporting consumer must:

1. use the shared reporting layer or document a justified special case;
2. preserve its public CLI and artifact contracts;
3. register in `DEFAULT_TARGETS` and the correct classification collection;
4. add exact registry tests;
5. pass `make reporting-consolidation-audit`;
6. update architecture, runbook and recovery documentation when substantial.
