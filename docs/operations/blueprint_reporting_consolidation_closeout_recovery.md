# Blueprint Reporting Consolidation Closeout Recovery

## Installer backup

The installer creates:

```text
.tmp_blueprint_backups/reporting_consolidation_closeout_<UTC timestamp>/
```

The backup contains a manifest and pre-change copies of every modified file.

## Git recovery before commit

Restore tracked files:

```bash
git restore -- \
  coordination/templates/module_makefile_standard.template.mk \
  coordination/standards/module_governance_make_targets.md \
  coordination/standards/make_command_standard.md \
  coordination/standards/module_make_target_contract.md \
  coordination/module_policy/README.md \
  tools/completion_packet_template/README.md \
  tools/completion_packet_template/completion_packet.example.yaml \
  scripts/reporting/audit_consolidation.py \
  tests/reporting/test_reporting_consolidation_audit.py \
  docs/architecture/blueprint_reporting_consolidation_map.md
```

Delete closeout-only files:

```bash
rm -f \
  tests/reporting/test_reporting_consolidation_closeout.py \
  docs/architecture/blueprint_reporting_consolidation_closeout.md \
  docs/operations/blueprint_reporting_consolidation_closeout_runbook.md \
  docs/operations/blueprint_reporting_consolidation_closeout_recovery.md \
  coordination/reports/completion/2026-07-16__blueprint__reporting_consolidation_closeout_v0_1.md
```

## Verification after recovery

```bash
make reporting-consolidation-audit
python -m pytest -q
make check-report
git diff --check
git status -sb
```

Do not remove unrelated untracked Website, risk-register, roadmap or backup
files.
