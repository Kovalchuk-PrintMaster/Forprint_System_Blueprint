# Telegram Bot Governance Baseline Adoption v0.1

## Coordination metadata

```yaml
prompt_id: telegram_bot_governance_baseline_adoption_v0_1
module: telegram_bot
status: ready
priority: high
issued_by: forprint_system_blueprint
issued_date: 2026-07-17
previous_front: telegram_bot_dialogue_audit_events_v0_1
accepted_main_commit: af335a5
target_branch: feature/telegram-governance-baseline-adoption-v01
scope_class: governance_and_development_tooling
implementation_scope_allowed: false
```

## 1. Purpose

Bring the legacy Telegram Bot repository’s development-governance shell to the current ForPrint Blueprint baseline without changing Telegram dialogue behavior, business logic, public interfaces, or runtime integration boundaries.

The repository already contains accepted dialogue-audit functionality on:

```text
main @ af335a5
```

This task aligns only:

- Make targets and command semantics;
- human-facing terminal reporting;
- machine-readable reporting artifacts;
- Blueprint prompt and policy consumption;
- module validation and completion lifecycle;
- lint, format, test, recovery, and diagnostic evidence;
- module-side governance documentation.

Do not start a new Telegram product or dialogue implementation front.

## 2. Mandatory source of truth

At task intake, read the current versions from the Blueprint repository and record the exact Blueprint commit used.

Required sources:

```text
coordination/templates/module_makefile_standard.template.mk
coordination/standards/module_governance_make_targets.md
coordination/standards/make_command_standard.md
coordination/standards/module_make_target_contract.md
coordination/module_policy/README.md
coordination/module_policy/telegram_bot/module_policy.md
tools/completion_packet_template/README.md
tools/completion_packet_template/completion_packet.example.yaml
docs/architecture/blueprint_reporting_consolidation_closeout.md
docs/operations/blueprint_reporting_consolidation_closeout_runbook.md
docs/operations/blueprint_reporting_consolidation_closeout_recovery.md
```

Also consume the current global compact-reporting directive when present.

Create a module-side adoption manifest containing:

- Blueprint commit;
- every consumed source path;
- SHA-256 of every consumed source;
- mandatory clauses adopted;
- deviations and reasons;
- deferred clauses;
- verification commands.

Blueprint remains the source of truth. Do not create an independent competing standard inside Telegram Bot.

## 3. Scope

### 3.1 Make target alignment

Audit the Telegram Bot `Makefile` against the canonical Blueprint contract.

Preserve existing target names and backward compatibility unless the Blueprint contract explicitly requires correction.

Required target coverage:

```text
env-check
tooling-check
config-check
secrets-check
compile
lint
format-check
test
check
check-report
check-report-full
status-report
blueprint-check
blueprint-prompts-check
module-policy-check
coordination-check
governance-check
module-validate
completion-packet-validate
completion-packet-apply
completion-packet-check
module-finish
report-clean
```

Do not remove a working legacy target merely because a canonical alias exists.

Document every missing, added, aliased, or deliberately deferred target.

### 3.2 Color-first terminal reporting

Human-operated development commands must use colored output by default.

This applies to:

```text
make check
make governance-check
make module-validate
make check-report
make check-report-full
make status-report
```

Required terminal behavior:

1. Begin with a compact closed-border table showing:
   - command;
   - module;
   - branch/commit;
   - mode;
   - artifact root.

2. Routine successful output must be compact and table-first.

3. One or several tables may be used when separate concerns would otherwise become mixed.

4. There is no rigid 20–40-line limit. Keep routine human-facing output as small as practical, normally within approximately 100 lines, but allow more when architecture requires it.

5. Large successful smoke traces, nested Make output, raw YAML, raw Markdown, and detailed diagnostics must be redirected into files.

6. Terminal output must show the artifact paths.

7. Warnings and failures may include focused diagnostic excerpts in the terminal.

8. Every short report and every extended report must end with a colored closed-border summary table.

9. Final summary must clearly show:
   - passed;
   - warnings;
   - failed;
   - blocked;
   - overall result;
   - artifact paths;
   - next action.

10. Status colors:
    - green: passed, accepted, healthy;
    - yellow: warning, deferred, needs review;
    - red: failed, blocked, unsafe;
    - cyan/blue or neutral: information, planned, future.

### 3.3 `NO_COLOR` behavior

Colored terminal output is the default for human development workflows.

`NO_COLOR=1` is supported for:

- machine processing;
- CI;
- redirected technical logs;
- archived evidence;
- downstream parsers.

`NO_COLOR=1` must not change:

- report data;
- JSON/Markdown schema;
- check counts;
- exit codes;
- artifact paths;
- ordering;
- hashes, except for artifacts that intentionally contain terminal escape sequences.

Do not use `NO_COLOR=1` as the main human review evidence. Verify it only as a compatibility contract.

### 3.4 Compact and extended reports

`make check-report`:

- compact human-facing colored tables;
- detailed logs written to `reports/diagnostics/`;
- stable JSON and Markdown artifacts;
- colored final summary table.

`make check-report-full`:

- may print or reference more detailed diagnostics;
- must remain bounded and readable;
- may redirect very large output to files;
- must still end with the same colored final summary table;
- must preserve canonical artifact schemas and exit codes.

`make status-report`:

- must not dump raw status YAML and Markdown by default;
- must render the current state as a compact colored table;
- full raw status remains available in tracked artifacts or explicit full mode.

### 3.5 Quality-gate semantics

Current targets must not report a false green result when a required tool is unavailable.

For every tool, classify it as:

```text
required
optional
not_applicable
```

Rules:

- unavailable required tool → `FAIL`;
- unavailable optional tool → `WARN` or `DEFERRED`;
- not applicable tool → `SKIP` with reason;
- never convert unavailable tooling into an unexplained `PASS`.

Align and document at least:

```text
ruff or canonical Python linter
formatter check
pytest or canonical test runner
py_compile
type checking when required by module policy
```

Do not install or introduce an unrelated toolchain merely to make the table green. Declare dependencies and behavior honestly.

### 3.6 Prompt and policy lifecycle

Verify and align:

- outgoing prompt index validation;
- active/ready prompt discovery;
- `--allow-no-ready`;
- active prompt readability;
- module policy visibility;
- global policy visibility;
- directive-index availability;
- completion application;
- prompt archival;
- current status update;
- next-questions update.

Preserve the accepted compatibility behavior for:

```text
--list
--check-active
--read
--module
--blueprint-root
--prompt
--check-index
--allow-no-ready
```

Prompt and policy checks must remain read-only against Blueprint.

No Blueprint repository writes are allowed from Telegram Bot.

### 3.7 Completion lifecycle

Align the module-side completion lifecycle with the canonical completion packet contract.

Required behavior:

- validation before application;
- deterministic application;
- idempotency check;
- no self-referential commit hashes in the same commit;
- completion report;
- reports index update;
- current status update;
- next questions;
- recovery documentation;
- generated reports excluded from implementation commits unless the contract explicitly requires tracking.

### 3.8 Documentation

Create or update:

```text
docs/architecture/telegram_governance_baseline.md
docs/architecture/telegram_reporting_architecture.md
docs/operations/telegram_governance_baseline_runbook.md
docs/operations/telegram_governance_baseline_recovery.md
coordination/reports/completion/telegram_bot_governance_baseline_adoption_v0_1_completion.md
```

Documentation must explain:

- what changed;
- why it changed;
- Blueprint source of truth;
- command contracts;
- terminal/report artifact split;
- color policy;
- `NO_COLOR` compatibility;
- quality-gate semantics;
- prompt lifecycle;
- completion lifecycle;
- verification;
- rollback and recovery.

## 4. Required tests

Add focused contract tests for at least:

1. compact output starts with a closed-border table;
2. compact output ends with a closed-border colored summary table;
3. full output ends with a closed-border colored summary table;
4. default human mode contains ANSI color when attached to a TTY or forced by the test harness;
5. `NO_COLOR=1` contains no ANSI escape sequences;
6. normal and `NO_COLOR` modes preserve status counts and exit codes;
7. successful routine output does not print the full smoke trace;
8. detailed smoke output is available in a diagnostic file;
9. failures appear in the final table;
10. warnings appear in the final table;
11. artifact paths appear in the terminal;
12. `status-report` does not dump raw YAML/Markdown by default;
13. prompt-reader existing CLI remains backward compatible;
14. malformed prompt index still fails;
15. valid index with no ready prompt passes only when allowed;
16. required unavailable quality tooling cannot silently pass;
17. completion application remains idempotent;
18. generated reports are not accidentally staged.

Preserve all existing Telegram Bot behavior tests.

## 5. Forbidden changes

Do not change:

- dialogue flow;
- user-facing Telegram messages;
- reply keyboards;
- dialogue audit event taxonomy;
- `MemoryState` public API;
- conversation-state behavior;
- SQLite business/runtime schema, except reporting-only storage when explicitly necessary and justified;
- canonical order behavior;
- Calculator integration;
- Logistics integration;
- CRM, Operational Registry, Gateway, 1C, payment, stock, or production writes;
- external APIs;
- production deployment behavior.

Do not merge to `main` before Blueprint acceptance.

Do not delete the feature branch before post-merge checks.

## 6. Required implementation order

1. Create the feature branch from current `main`.
2. Record repository, branch, HEAD, origin/main, and clean status.
3. Read canonical Blueprint sources.
4. Create the adoption manifest.
5. Produce a gap table before implementation.
6. Align reporting runner and terminal presentation.
7. Align Make targets and honest quality semantics.
8. Align prompt, policy, and completion lifecycle.
9. Add architecture, runbook, and recovery documents.
10. Add focused contract tests.
11. Run focused tests.
12. Run full checks.
13. Generate compact colored human evidence.
14. Verify `NO_COLOR=1` only as machine compatibility evidence.
15. Create completion records and commit.
16. Push the feature branch.
17. Stop for Blueprint review.

## 7. Required validation

Human-facing colored validation:

```bash
make lint
make format-check
make check
make governance-check
make module-validate
make check-report
make check-report-full
make status-report
git diff --check
git status -sb
```

Machine compatibility validation:

```bash
NO_COLOR=1 make check-report
NO_COLOR=1 make check-report-full
```

Also validate generated JSON:

```bash
python -m json.tool reports/telegram_bot_check_report.json >/dev/null
```

All commands must record exit codes.

## 8. Acceptance criteria

The task is ready for Blueprint review only when:

- current accepted Telegram behavior remains unchanged;
- all existing functional checks pass;
- routine terminal reports are compact and colored;
- every short and extended report ends with a colored summary table;
- large details are stored in diagnostic files;
- artifact paths are visible;
- `NO_COLOR` compatibility is verified;
- required unavailable tools cannot appear as PASS;
- canonical Make/governance/prompt/completion contracts are aligned;
- all documentation and recovery artifacts exist;
- generated artifacts are not staged unless explicitly required;
- branch is pushed and clean;
- no Blueprint writes occurred;
- no forbidden implementation scope was entered.

## 9. Final completion response

Return one compact completion response with:

- repository path;
- branch;
- base commit;
- final commit;
- Blueprint commit consumed;
- adoption manifest path;
- gap table before/after;
- changed files grouped by area;
- focused test commands and counts;
- full validation commands and results;
- compact-report screenshot-equivalent text table;
- full-report final table;
- JSON/Markdown/diagnostic artifact paths;
- quality-tool classification;
- public-interface confirmation;
- blockers;
- deferred work;
- clean `git status -sb`;
- readiness for Blueprint acceptance.

Final line:

```text
RESULT: READY_FOR_BLUEPRINT_REVIEW | BLOCKED | INCOMPLETE
```
