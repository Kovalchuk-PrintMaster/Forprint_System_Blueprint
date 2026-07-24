# Blueprint Internal Workflow Foundation v0.1 — Completion Report

## Intended result

```text
READY_FOR_INSTALLATION_AND_VERIFICATION
```

## Scope

- module-scoped workflow control structure;
- shared workflow engine foundation;
- Blueprint Self Audit;
- exact `bsa.yaml` external-input contract;
- compact boxed dashboard;
- detailed Markdown and JSON reports;
- one-file external analysis bundle;
- Make commands and aliases;
- standards, architecture, runbook and recovery;
- focused tests.

## Safety

- no external network calls;
- no cross-repository writes;
- no automatic staging;
- no automatic commit or push;
- expected waiting state is explicit;
- external input is validated before use.

## Verification performed before packaging

- focused workflow tests: `4 passed`;
- module workflow registry check: `OK`;
- standards index validation: `OK`;
- end-to-end prepare phase: `AWAITING_EXTERNAL_INPUT`;
- end-to-end resume phase: `COMPLETED`;
- YAML parse validation: `OK`;
- Python compile validation: `OK`;
- reconstructed-snapshot `git diff --check`: `0`.

The live Blueprint repository must still run its canonical `make check-report`
after installation because the collector archive intentionally omitted several
pre-existing template fragments that are present in the live repository.

## Deferred


- queue/roadmap/current-focus consistency calculation;
- automatic application of recommendations to canonical snapshots;
- module profiles beyond Blueprint;
- Project Inspector automation;
- contract registry integration.

## Pre-commit workflow foundation correction

Before the foundation commit, live verification exposed two packaging defects:

1. the `Module workflow control` help recipe initially lacked Make TAB
   indentation and caused `missing separator`;
2. Ruff found four issues in the new workflow files:
   `UP022`, two `E402` findings and one `I001`.

The correction:

- preserved the manually repaired Make help TAB indentation;
- changed workflow CLI execution to the package form:

  ```text
  python -m scripts.coordination.modules.module_workflow_cli
  ```

- removed the runtime `sys.path` bootstrap from the CLI;
- changed `subprocess.run` to `capture_output=True`;
- sorted the self-audit test imports;
- added a regression test that runs
  `make -n module-workflow-check`;
- reran Ruff, focused workflow tests, workflow validation,
  the complete Blueprint check report and `git diff --check`.

The final commit must contain the corrected foundation, not the original
installer form.
