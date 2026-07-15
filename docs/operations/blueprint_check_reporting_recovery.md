# Blueprint Check Reporting Recovery Guide

## Purpose

Use this guide after chat-context loss, assistant replacement, a long pause or an interrupted reporting change.

## Step 1 — establish repository state

```bash
git status -sb
git log --oneline -8
```

Do not stage unrelated module, Website or risk-register work.

## Step 2 — identify current coordination work

```bash
make prompt-dashboard MODULE=logistics_service
make roadmap-dashboard MODULE=logistics_service
```

Repeat for the module currently being coordinated.

## Step 3 — read reporting architecture and rules

```text
docs/architecture/blueprint_check_reporting_architecture.md
docs/operations/blueprint_check_reporting_runbook.md
coordination/standards/testing_and_check_report_standard.md
coordination/standards/visual_interface/color_tokens_policy.md
coordination/standards/visual_interface/boxed_table_layout_policy.md
coordination/standards/governance/documentation_and_recovery_gate.md
```

## Step 4 — run compact validation

```bash
make check-report
```

Record:

```text
overall status;
failed count;
warning count;
blockers;
JSON/Markdown paths.
```

## Step 5 — open diagnostics only when needed

```bash
make check-report-full
```

Then inspect:

```text
reports/diagnostics/blueprint_check_report_full.log
```

## Step 6 — verify active branch purpose

The reporting implementation branch is:

```text
feature/blueprint-compact-check-report-v01
```

Confirm that the active branch and latest commits match the current task before editing.

## Step 7 — continue only documented work

Use the active prompt, roadmap and completion evidence.

Do not infer a new scope from an old chat when repository evidence disagrees.
