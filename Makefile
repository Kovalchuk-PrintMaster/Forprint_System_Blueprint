# ForPrint System Blueprint Makefile
#
# This file is the executable command surface for the Blueprint repository.
# Public targets must preserve repository ownership and command semantics:
#   - preview/status/list/show/validate/check targets are operator-safe and
#     must not hide apply/commit/push/merge behavior;
#   - explicit write/apply/fix/generate targets may mutate only Blueprint;
#   - Blueprint completion intake reads module repositories but never writes them;
#   - completion-accept requires a successful read-only intake check;
#   - completion-return remains available for invalid evidence and writes only
#     Blueprint review records.
#
# GNU Make recipes use TAB indentation. Do not use .RECIPEPREFIX.

# =============================================================================
# Operator reading guide
# =============================================================================
# Every public target below has a five-field command contract:
#   Purpose — what the command actually does.
#   Safety  — whether it is read-only, report/tmp-only, or mutating.
#   Inputs  — operator variables read by the target; required inputs are marked.
#   Scope   — how broad the command is.
#   Result  — what appears on success and how failure is surfaced.
#
# Scope vocabulary:
#   LOCAL/FOCUSED   one explicit artifact/query/target surface.
#   RELATED         one contract plus its direct validation dependencies.
#   CORE            core Blueprint control/governance validation surface.
#   FULL            broad repository validation/test surface.
#   PORTFOLIO       multi-module/project portfolio view.
#   PROJECT_ONBOARD authoritative whole-project onboarding handoff context.
#   MODULE/QUEUE    one selected module/prompt/packet/queue surface.
#   WORKTREE        current Blueprint Git worktree/diff/seal surface.
#
# Important operator distinction:
#   assistant-pack         = authoritative PROJECT_ONBOARD handoff archive.
#   assistant-context-pack = scoped MODULE/TOPICS context archive.
#   check                  = FULL non-mutating validation wrapper.
#   check-core             = CORE validation suite.
#   diff-show              = DIFF_PATHS when provided; otherwise full unstaged tracked diff.
#
# This refactor intentionally preserves target names, dependencies, recipes,
# CLI flags, stdout/stderr ownership, and exit-code semantics.

# =============================================================================
# 00 Environment / constants
# =============================================================================
# Block scope: Global Blueprint command variables and defaults.

.DEFAULT_GOAL := help
.DELETE_ON_ERROR:

PYTHON ?= .venv_blueprint/bin/python
BLUEPRINT_PYTHON ?= $(PYTHON)
PIP ?= $(PYTHON) -m pip

MODULE ?= forprint_library
MODULE_ROOT ?= ../$(MODULE)
MODULES ?=
ROADMAP ?=

SCOPE ?= bootstrap
LIMIT ?= 40
BEFORE_CURRENT ?= 5
AFTER_CURRENT ?= 10
ROADMAP_SUMMARY_MODULES ?= forprint_library

PACKET ?=
REVIEW_NOTES ?=
COMPLETION_COMMIT ?=
REVIEWED_AT ?=
REMOTE ?= origin
BRANCH ?=

STATUS ?= acknowledged
LEDGER ?= coordination/blueprint_awareness/document_review_ledger.yaml
DOCUMENT ?=
SOURCE ?=
PROMPT_ID ?=
APPLY ?= 0
REPLACE ?= 0
PRIORITY ?=
NOTES ?=
MODULE_COMMIT ?=
GOVERNANCE_STATUS_FORMAT ?= status


BLUEPRINT_MODULE_MANIFEST_EXAMPLE ?= module_manifests/examples/calculator_engine.forprint_module_manifest.example.yaml


# =============================================================================
# 01 Help / navigation
# =============================================================================
# Block scope: Operator discovery only; no project mutation.

# Target: help
# Purpose: Show the operator command map for the Blueprint repository.
# Safety: READ-ONLY — prints navigation only.
# Inputs: None.
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: help
help:
	@echo "ForPrint System Blueprint Make targets"
	@echo ""
	@echo "Install / bootstrap:"
	@echo "  make install"
	@echo ""
	@echo "Lint / tests / validation:"
	@echo "  make lint"
	@echo "  make lint-fix"
	@echo "  make format"
	@echo "  make test"
	@echo "  make validate"
	@echo "  make markdown-fences"
	@echo "  make check"
	@echo "  make validation-suite SUITE=cf10-worker-pipeline"
	@echo "  make check-report"
	@echo "  make test-make-command-surface"
	@echo "  make test-v0-4-coordination"
	@echo ""
	@echo "Blueprint artifacts:"
	@echo "  make diagrams"
	@echo "  make diagrams-check"
	@echo "  make diagrams-list"
	@echo "  make guides"
	@echo "  make manifest-example"
	@echo ""
	@echo "Prompt preparation / release:"
	@echo "  make prompt-prepare SOURCE=operator_input/prompts/example.md"
	@echo "  make prompt-prepare SOURCE=operator_input/prompts/example.md APPLY=1"
	@echo "  make prompt-prepare SOURCE=operator_input/prompts/example.md APPLY=1 REPLACE=1"
	@echo "  make prompt-release MODULE=forprint_library PROMPT_ID=library_example_v0_1"
	@echo "  make prompt-release MODULE=forprint_library PROMPT_ID=library_example_v0_1 APPLY=1"
	@echo "  Release apply remains fail-closed unless governance policy authorizes it."
	@echo ""
	@echo "Prompt queue navigation:"
	@echo "  make prompt-queue-validate"
	@echo "  make prompt-dashboard MODULE=forprint_library"
	@echo "  make prompt-next MODULE=forprint_library"
	@echo "  make prompt-read-next MODULE=forprint_library"
	@echo "  make completion-intake-check MODULE=logistics_service MODULE_ROOT=../forprint_logistics_service PACKET=coordination/completion_packets/records/example.yaml COMPLETION_COMMIT=<commit>"
	@echo "  make completion-revision-status"
	@echo "  make completion-revision-check"
	@echo "  make completion-intake-check MODULE=logistics_service MODULE_ROOT=../forprint_logistics_service PACKET=<v0.3-packet> COMPLETION_COMMIT=<commit> ALLOW_CANDIDATE_REFERENCE=1"
	@echo "  make completion-intake-preview MODULE=logistics_service MODULE_ROOT=../forprint_logistics_service PACKET=coordination/completion_packets/records/example.yaml COMPLETION_COMMIT=<commit>"
	@echo "  make completion-accept MODULE=logistics_service MODULE_ROOT=../forprint_logistics_service PACKET=coordination/completion_packets/records/example.yaml COMPLETION_COMMIT=<commit>"
	@echo "  make completion-return MODULE=logistics_service MODULE_ROOT=../forprint_logistics_service PACKET=coordination/completion_packets/records/example.yaml REVIEW_NOTES='Corrections required'"
	@echo "  make completion-finalize-check MODULE=logistics_service"
	@echo "  make next-work-suggestion MODULE=logistics_service"
	@echo ""
	@echo "Coordination document awareness:"
	@echo "  make document-manifest"
	@echo "  make document-awareness MODULE=forprint_library LIMIT=20"
	@echo "  make context-bundle MODULE=forprint_library SCOPE=bootstrap LIMIT=10"
	@echo "  make context-bundle-print MODULE=forprint_library SCOPE=bootstrap LIMIT=10"
	@echo "  make task-context-compiler-check"
	@echo "  make task-context-check MODULE=logistics_service TASK_PROMPT_ID=<prompt-id> TASK_MODULE_ROOT=<module-repo>"
	@echo "  make task-context-compile MODULE=logistics_service TASK_PROMPT_ID=<prompt-id> TASK_MODULE_ROOT=<module-repo> TASK_CONTEXT_OUTPUT_DIR=tmp/task_context_bundles"
	@echo "  make task-context-print MODULE=logistics_service TASK_PROMPT_ID=<prompt-id> TASK_MODULE_ROOT=<module-repo>"
	@echo "  make launch-request-gate-check"
	@echo "  make launch-request-evaluate TASK_MODULE_ROOT=<module-repo> TASK_CONTEXT_ARCHIVE=<archive> [DEPENDENCY_READINESS=<snapshot>]"
	@echo "  make launch-request-build TASK_MODULE_ROOT=<module-repo> TASK_CONTEXT_ARCHIVE=<archive> [DEPENDENCY_READINESS=<snapshot>]"
	@echo "  make operator-approval-gateway-check"
	@echo "  make operator-approval-evaluate TASK_MODULE_ROOT=<module-repo> LAUNCH_REQUEST=<launch-request>"
	@echo "  make operator-approval-decide TASK_MODULE_ROOT=<module-repo> LAUNCH_REQUEST=<launch-request> OPERATOR_DECISION=<APPROVE|HOLD|REJECT> OPERATOR_ACTOR=<actor> OPERATOR_REASON=<reason>"
	@echo "  make operator-approval-validate TASK_MODULE_ROOT=<module-repo> LAUNCH_REQUEST=<launch-request> APPROVAL_DECISION=<decision-artifact>"
	@echo "  make console-worker-adapter-check"
	@echo "  make worker-invocation-evaluate TASK_MODULE_ROOT=<module-repo> LAUNCH_REQUEST=<launch-request> WORKER_RUNTIME=<runtime> [APPROVAL_DECISION=<approval>]"
	@echo "  make worker-invocation-build TASK_MODULE_ROOT=<module-repo> LAUNCH_REQUEST=<launch-request> WORKER_RUNTIME=<runtime> [APPROVAL_DECISION=<approval>]"
	@echo "  make control-plane-runtime-check"
	@echo "  make control-plane-step LAUNCH_REQUEST=<launch> WORKER_INVOCATION=<invocation> [APPROVAL_DECISION=<approval>]"
	@echo "  make control-plane-status LAUNCH_REQUEST=<launch> WORKER_INVOCATION=<invocation> [APPROVAL_DECISION=<approval>]"
	@echo "  make completion-control-plane-check"
	@echo "  make document-ledger-preview MODULE=forprint_library DOCUMENT=coordination/global_policy/forprint_project_doctrine.md"
	@echo "  make document-ledger-update MODULE=forprint_library DOCUMENT=coordination/global_policy/forprint_project_doctrine.md STATUS=acknowledged"
	@echo ""
	@echo "Assistant / continuity / handoff:"
	@echo "  make assistant-pack"
	@echo "  make assistant-pack FRONT=<work-front-id>"
	@echo "  make assistant-context-pack MODULE=forprint_system_blueprint TOPICS=<comma-separated-topics>"
	@echo "  make assistant-handoff-check"
	@echo "  make roadmap-sync-check"
	@echo "  make continuity-lifecycle-status"
	@echo "  make continuity-projections-check"
	@echo "  make project-constitution-check"
	@echo "  make work-front-contract-check"
	@echo "  make execution-profile-registry-check"
	@echo "  make assistant-handoff-v2-contract-check"
	@echo "  make assistant-handoff-v2-runtime-check"
	@echo "  make assistant-handoff-v2-project-onboard"
	@echo "  make assistant-handoff-v2-task-execution FRONT=<front> EXECUTION_PROFILE=<profile> TASK_PROMPT_ID=<prompt-id> TASK_MODULE_ROOT=<module-root> PROCEDURE_ID=<procedure-id>"
	@echo "  make assistant-handoff-v2-result-check"
	@echo "  make assistant-handoff-v2-freshness-resume-check"
	@echo ""
	@echo "Module roadmap:"
	@echo "  make roadmap-validate MODULE=forprint_library"
	@echo "  make roadmap-dashboard MODULE=forprint_library"
	@echo "  make roadmap-detail MODULE=forprint_library"
	@echo "  make acceptance-oracle-validate ORACLE=coordination/acceptance_oracles/<module>/<oracle>.yaml"
	@echo "  make roadmap-dashboard MODULES=forprint_library,forprint_integration_gateway,forprint_crm"
	@echo "  make roadmap-summary"
	@echo "  make roadmap-summary ROADMAP_SUMMARY_MODULES=forprint_library,forprint_integration_gateway"
	@echo ""
	@echo "v0.4 coordination reference primitives:"
	@echo "  make coordination-pulse"
	@echo "  make coordination-pulse COORDINATION_PULSE_FORMAT=yaml"
	@echo "  make prompt-contract-v0-4-validate PROMPT_CONTRACT_V0_4=<contract-path>"
	@echo "  make completion-packet-v0-4-validate COMPLETION_PACKET_V0_4=<packet-path>"
	@echo "  make completion-outbox-v0-4-validate COMPLETION_OUTBOX_V0_4=<outbox-path>"
	@echo "  make completion-discovery-intake-v0-4"
	@echo "  make review-roadmap-queue-transaction-v0-4"
	@echo "  make review-roadmap-queue-transaction-v0-4 REVIEW_TRANSACTION_REQUEST=tmp/<request>.yaml"
	@echo "  make review-roadmap-queue-transaction-v0-4 REVIEW_TRANSACTION_REQUEST=tmp/<request>.yaml REVIEW_TRANSACTION_APPLY=1 REVIEW_OPERATOR_CONFIRMATION=<decision-id>"
	@echo "  make accept-and-advance ACCEPT_AND_ADVANCE_REQUEST=tmp/<request>.yaml ACCEPT_AND_ADVANCE_APPLY=1 ACCEPT_AND_ADVANCE_CONFIRMATION=<operation-id>"
	@echo "  make next-prompt-selection-activation-v0-4"
	@echo "  make tracking-events-reference-v0-4-preflight"
	@echo "  make tracking-events-reference-v0-4-build"
	@echo "  make tracking-events-reference-v0-4-validate"
	@echo "  make tracking-events-reference-v0-4-revise-after-pre-review"
	@echo "  make tracking-events-reference-v0-4-semantic-review-prep"
	@echo "  make tracking-events-reference-v0-4-semantic-decision TRACKING_EVENTS_SEMANTIC_DECISION=ACCEPT_SEMANTIC_FIDELITY"
	@echo "  v0.4 primitive targets never imply global v0.4 promotion."
	@echo ""
	@echo "Standards / governance:"
	@echo "  make standards-index"
	@echo "  make standards"
	@echo "  make standards-check"
	@echo "  make module-standards-template"
	@echo "  make instruction-intake"
	@echo "  make completion-packet-template"
	@echo "  make coordination-check"
	@echo "  make coordination-fix"
	@echo "  make module-policy-generate"
	@echo "  make module-policy-check"
	@echo "  make module-governance-audit"
	@echo ""
	@echo "Module workflow control:"
	@echo "  make module-workflow-list"
	@echo "  make module-workflow-check"
	@echo "  make module-self-audit MODULE=forprint_system_blueprint"
	@echo "  make module-self-audit-resume MODULE=forprint_system_blueprint"
	@echo "  make module-self-status MODULE=forprint_system_blueprint"
	@echo "  make module-self-report-full MODULE=forprint_system_blueprint"
	@echo "  make blueprint-self-audit"
	@echo "  make blueprint-self-audit-resume"
	@echo "  make blueprint-self-status"
	@echo "  make blueprint-governance-status GOVERNANCE_STATUS_FORMAT=status"
	@echo "  make blueprint-governance-status GOVERNANCE_STATUS_FORMAT=yaml"
	@echo "  make blueprint-governance-status GOVERNANCE_STATUS_FORMAT=json"
	@echo "  make blueprint-self-report-full"
	@echo "  make modules-self-status"
	@echo ""
	@echo "Repository state:"
	@echo "  make worktree-status"
	@echo "  make diff-check"
	@echo "  make diff-stat DIFF_PATHS='Makefile reports/example.yaml'"
	@echo "  make diff-show DIFF_PATHS='Makefile reports/example.yaml'"
	@echo "  make seal-stage-exact SEAL_PATHS='path1 path2'"
	@echo "  make seal-staged-review"
	@echo "  make seal-commit SEAL_COMMIT_MESSAGE='message'"
	@echo "  make seal-push"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean"


# =============================================================================
# 02 Install / bootstrap
# =============================================================================
# Block scope: Local development environment setup.

# Target: install
# Purpose: Install or update the Blueprint development environment and editable development dependencies.
# Safety: ENVIRONMENT MUTATION — changes the local Python environment/dependencies, not project source.
# Inputs: None.
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: install
install:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"


# =============================================================================
# 03 Code quality / tests / validation
# =============================================================================
# Block scope: Repository validation from focused checks through FULL gate.

# Target: lint
# Purpose: Run the configured Python linter without modifying source files.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: lint
lint:
	$(PYTHON) -m ruff check scripts tests tools

# Target: lint-fix
# Purpose: Apply supported automatic lint fixes to Blueprint Python sources and tests.
# Safety: SOURCE MUTATION — applies only the formatter/linter fixes documented by the target.
# Inputs: None.
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: lint-fix
lint-fix:
	$(PYTHON) -m ruff check scripts tests tools --fix

# Target: format
# Purpose: Format Blueprint Python sources and tests with the configured formatter.
# Safety: SOURCE MUTATION — applies only the formatter/linter fixes documented by the target.
# Inputs: None.
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: format
format:
	$(PYTHON) -m black scripts tests


# Target: test
# Purpose: Run the main Blueprint automated test suite.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: FULL — broad repository validation/test surface.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: test
test:
	$(PYTHON) -m pytest -q


# Target: test-make-command-surface
# Purpose: Verify the canonical Make/operator command surface.
# Safety: READ-ONLY TEST — tests only; no apply/commit/push/module writes.
# Inputs: None.
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: test-make-command-surface
test-make-command-surface:
	@$(BLUEPRINT_PYTHON) -m pytest -q \
		tests/coordination/modules/_shared/test_makefile_module_workflow_targets.py \
		tests/test_make_command_standard.py \
		tests/test_module_makefile_standard_template.py

# Target: test-v0-4-coordination
# Purpose: Verify the focused v0.4 coordination and Tracking Events reference surface.
# Safety: READ-ONLY TEST — tests only; no module writes, operator decisions, rollout, or promotion.
# Inputs: None.
# Scope: COORDINATION — focused coordination protocol surface.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: test-v0-4-coordination
test-v0-4-coordination:
	@$(BLUEPRINT_PYTHON) -m pytest -q \
		tests/validation/test_tracking_events_control_state_reconciliation.py \
		tests/validation/test_tracking_events_operator_review_findings.py \
		tests/validation/test_v0_4_closed_loop_lifecycle_standard.py \
		tests/validation/test_v0_4_closed_loop_reconciliation.py \
		tests/validation/test_v0_4_completion_discovery_and_intake.py \
		tests/validation/test_v0_4_completion_outbox.py \
		tests/validation/test_v0_4_completion_packet.py \
		tests/validation/test_v0_4_coordination_health_and_pulse.py \
		tests/validation/test_v0_4_coordination_source_registry.py \
		tests/validation/test_v0_4_immutable_prompt_contract.py \
		tests/validation/test_v0_4_next_prompt_selection_activation.py \
		tests/validation/test_v0_4_review_roadmap_queue_transaction.py \
		tests/validation/test_tracking_events_v0_4_reference_contract.py \
		tests/validation/test_tracking_events_v0_4_semantic_review_packet.py \
		tests/validation/test_tracking_events_v0_4_semantic_decision.py \
		tests/validation/test_v0_4_coordination_pulse_completion_observability.py \
		tests/validation/test_v0_4_review_transaction_module_schema_plan.py


# Target: validate
# Purpose: Run the primary Blueprint validation entrypoint.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: validate
validate:
	$(PYTHON) scripts/validate_blueprint.py

# Target: markdown-fences
# Purpose: Validate Markdown code-fence structure across managed documentation.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: markdown-fences
markdown-fences:
	$(PYTHON) scripts/validation/validate_markdown_fences.py

# Target: check
# Purpose: Run the main non-mutating repository validation wrapper.
# Safety: READ-ONLY — main non-mutating repository validation wrapper; no fix/apply/commit/push behavior.
# Inputs: MODULE_ROOT (optional/defaulted).
# Scope: FULL — broad repository validation/test surface.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: check
check:
	$(PYTHON) scripts/validation/run_non_mutating_make_check.py --target check-core --module-root "$(MODULE_ROOT)"

# Target: validation-suite
# Purpose: Run one registered focused validation suite through the reusable isolated suite runner.
# Safety: READ-ONLY — validation executes in disposable isolation; no apply/commit/push/module writes.
# Inputs: SUITE (required registered validation suite id).
# Scope: LOCAL/FOCUSED — selected registered validation suite only.
# Result: Validation exits 0 on success and non-zero on failure; durable source state remains unchanged.
.PHONY: validation-suite
validation-suite:
	@test -n "$(SUITE)$$FORPRINT_VALIDATION_SUITE_ID" || { echo "ERROR: SUITE=<registered-suite-id> is required"; exit 2; }
	@SUITE_ID="$${FORPRINT_VALIDATION_SUITE_ID:-$(SUITE)}"; \
		$(PYTHON) scripts/validation/run_validation_suite_v0_1.py --suite "$$SUITE_ID"

# Target: check-core
# Purpose: Run the broad core Blueprint validation suite used by the main check wrapper.
# Safety: READ-ONLY — broad core validation suite; no fix/apply/commit/push behavior.
# Inputs: None.
# Scope: CORE — core Blueprint governance/control-plane checks and direct dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: check-core
check-core: generator-inventory-check generator-contract-check execution-dependency-check roadmap-sync-check assistant-handoff-check continuity-projections-check continuity-lifecycle-check continuity-transfer-check continuity-event-store-check continuity-contract-check continuity-micro-roadmap-check check-module-registry-consistency check-self-coordination-consistency check-repository-knowledge-snapshots check-inventory-status-consistency check-repository-knowledge-freshness check-rci-semantic-enrichment check-redm-dependency-enrichment check-semantic-coverage-closure check-repository-knowledge-reconciliation check-inventory-acceptance-evidence-index check-inventory-acceptance-dry-run check-prompt-execution-observability surface-normalization-check human-intent-check root-roadmap-check roadmap-detail-check skip-inventory-check safe-mutation-check asset-retirement-check module-cleanliness-pack-check module-current-state-check canonical-state-freshness-impact-check module-memory-schema-check task-context-compiler-check launch-request-gate-check operator-approval-gateway-check console-worker-adapter-check control-plane-runtime-check completion-control-plane-check bootstrap-task-context-check project-constitution-check work-front-contract-check cf05-history-ledger-check execution-profile-registry-check assistant-handoff-v2-contract-check assistant-handoff-v2-runtime-check assistant-handoff-v2-result-check assistant-handoff-v2-freshness-resume-check
	$(PYTHON) scripts/run_blueprint_checks.py

# Target: check-report
# Purpose: Run Blueprint checks and render the normal operator validation report.
# Safety: REPORT WRITE ONLY — runs validation and may write documented report artifacts; does not mutate coordination authority or Git state.
# Inputs: None.
# Scope: FULL — broad repository validation/test surface.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: check-report
check-report:
	$(PYTHON) scripts/run_blueprint_checks.py

# Target: check-report-full
# Purpose: Run Blueprint checks with extended diagnostic output.
# Safety: REPORT WRITE ONLY — runs validation with extended diagnostics and may write documented report artifacts; does not mutate coordination authority or Git state.
# Inputs: None.
# Scope: FULL — broad repository validation/test surface.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: check-report-full
check-report-full:
	$(PYTHON) scripts/run_blueprint_checks.py --full-log

# Target: check-fix
# Purpose: Apply safe lint fixes, then run the main non-mutating repository check.
# Safety: SOURCE MUTATION — applies only the formatter/linter fixes documented by the target.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: check-fix
check-fix:
	$(MAKE) lint-fix
	$(MAKE) check


# =============================================================================
# 04 Repository state / diff / sealing
# =============================================================================
# Block scope: Worktree visibility and explicit Git sealing operations.

# Target: worktree-status
# Purpose: Show branch, HEAD, and the current repository dirty surface without mutation.
# Safety: READ-ONLY — shows repository state only; never stages, commits, pushes, restores, or writes module repositories.
# Inputs: None.
# Scope: WORKTREE — current Blueprint repository.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: worktree-status
worktree-status:
	@git status --short

# Target: diff-check
# Purpose: Validate unstaged and staged diffs for whitespace and patch integrity problems.
# Safety: READ-ONLY — validates current diffs only; never stages, commits, pushes, restores, or writes.
# Inputs: None.
# Scope: WORKTREE — current Blueprint repository.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: diff-check
diff-check:
	@git diff --check
	@git diff --cached --check

DIFF_PATHS ?=

# Target: diff-stat
# Purpose: Show a compact change summary for the selected unstaged diff surface.
# Safety: READ-ONLY — prints diff statistics only; never stages, writes, restores, commits, or pushes.
# Inputs: DIFF_PATHS (optional/defaulted).
# Scope: SELECTED/WORKTREE — DIFF_PATHS if supplied; otherwise the current unstaged tracked diff.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: diff-stat
diff-stat:
	@git diff --stat -- $(DIFF_PATHS)

# Target: diff-show
# Purpose: Show the exact unstaged patch for the selected paths; with no DIFF_PATHS, show the full unstaged tracked diff.
# Safety: READ-ONLY — prints the selected/current unstaged patch only; never stages, writes, restores, commits, or pushes.
# Inputs: DIFF_PATHS (optional/defaulted).
# Scope: SELECTED/WORKTREE — DIFF_PATHS if supplied; otherwise the current unstaged tracked diff.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: diff-show
diff-show:
	@git diff --no-ext-diff -- $(DIFF_PATHS)

SEAL_PATHS ?=
SEAL_COMMIT_MESSAGE ?=
SEAL_BRANCH ?= $(shell git branch --show-current)

# Target: seal-stage-exact
# Purpose: Stage exactly the paths explicitly supplied for a repository seal operation.
# Safety: GIT INDEX MUTATION — stages only explicit SEAL_PATHS and fails closed when the observed dirty surface differs.
# Inputs: SEAL_PATHS (required).
# Scope: WORKTREE — current Blueprint repository.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: seal-stage-exact
seal-stage-exact:
	@test -n "$(SEAL_PATHS)" || { echo "ERROR: SEAL_PATHS is required"; exit 1; }
	@set -eu; \
	expected="$$(printf '%s\n' $(SEAL_PATHS) | LC_ALL=C sort -u)"; \
	actual="$$( { git diff --name-only --no-renames; git diff --cached --name-only --no-renames; git ls-files --others --exclude-standard; } | LC_ALL=C sort -u)"; \
	if [ "$$actual" != "$$expected" ]; then \
		echo "ERROR: dirty surface differs from SEAL_PATHS"; \
		echo "EXPECTED:"; printf '%s\n' "$$expected"; \
		echo "ACTUAL:"; printf '%s\n' "$$actual"; \
		exit 1; \
	fi; \
	git add -- $(SEAL_PATHS); \
	staged="$$(git diff --cached --name-only --no-renames | LC_ALL=C sort -u)"; \
	if [ "$$staged" != "$$expected" ]; then \
		echo "ERROR: staged surface mismatch"; \
		exit 1; \
	fi; \
	echo "STAGED_PATH_COUNT=$$(printf '%s\n' "$$staged" | wc -l)"; \
	printf '%s\n' "$$staged"

# Target: seal-staged-review
# Purpose: Review the exact staged seal candidate before commit.
# Safety: READ-ONLY — reviews the staged seal candidate only.
# Inputs: None.
# Scope: WORKTREE — current Blueprint repository.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: seal-staged-review
seal-staged-review:
	@git diff --cached --check
	@GIT_PAGER=cat git diff --cached --name-only --no-renames
	@GIT_PAGER=cat git diff --cached --stat

# Target: seal-commit
# Purpose: Create an explicit operator-requested seal commit from the staged candidate.
# Safety: GIT MUTATION — creates a commit from staged content only; never pushes and requires an explicit non-empty message.
# Inputs: SEAL_COMMIT_MESSAGE (required).
# Scope: WORKTREE — current Blueprint repository.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: seal-commit
seal-commit:
	@test -n "$(SEAL_COMMIT_MESSAGE)" || { echo "ERROR: SEAL_COMMIT_MESSAGE is required"; exit 1; }
	@test -n "$$(git diff --cached --name-only --no-renames)" || { echo "ERROR: nothing staged"; exit 1; }
	@git diff --cached --check
	@git commit -m "$(SEAL_COMMIT_MESSAGE)"

# Target: seal-push
# Purpose: Push the current seal branch and verify local and remote HEAD agreement.
# Safety: NETWORK/GIT MUTATION — explicit push of the current seal branch; verifies local/remote HEAD and performs no merge.
# Inputs: SEAL_BRANCH (required).
# Scope: WORKTREE — current Blueprint repository.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: seal-push
seal-push:
	@test -n "$(SEAL_BRANCH)" || { echo "ERROR: SEAL_BRANCH is empty"; exit 1; }
	@set -eu; \
	current_branch="$$(git branch --show-current)"; \
	test "$$current_branch" = "$(SEAL_BRANCH)" || { echo "ERROR: current branch mismatch: $$current_branch"; exit 1; }; \
	local_head="$$(git rev-parse HEAD)"; \
	git push origin "$(SEAL_BRANCH)"; \
	remote_head="$$(git ls-remote --heads origin "$(SEAL_BRANCH)" | awk 'NR==1 {print $$1}')"; \
	echo "LOCAL_HEAD:"; echo "$$local_head"; \
	echo "REMOTE_HEAD:"; echo "$$remote_head"; \
	test -n "$$remote_head" || { echo "ERROR: remote branch not found"; exit 1; }; \
	test "$$local_head" = "$$remote_head" || { echo "ERROR: LOCAL_HEAD != REMOTE_HEAD"; exit 1; }; \
	worktree="$$(git status --short)"; \
	echo "WORKTREE:"; printf '%s\n' "$$worktree"; \
	test -z "$$worktree" || { echo "ERROR: worktree not clean after push"; exit 1; }


# =============================================================================
# 05 Cleanup / generated documentation artifacts
# =============================================================================
# Block scope: Local cleanup and documentation/diagram generation.

# Target: clean
# Purpose: Remove local cache, coverage, bytecode, and top-level egg-info artifacts.
# Safety: LOCAL DESTRUCTIVE CLEANUP — deletes only documented caches/generated local artifacts.
# Inputs: None.
# Scope: WORKTREE — current Blueprint repository.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: clean
clean:
	rm -rf -- .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	find scripts tests -type d -name "__pycache__" -prune -exec rm -rf -- {} +
	find . -maxdepth 1 -type d -name "*.egg-info" -prune -exec rm -rf -- {} +


# Target: diagrams
# Purpose: Generate managed Mermaid diagram artifacts.
# Safety: GENERATED-ARTIFACT WRITE — writes only the documented generated/report/package surface; no release/commit/push authority.
# Inputs: None.
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: diagrams
diagrams:
	$(PYTHON) scripts/generate_mermaid.py

# Target: diagrams-check
# Purpose: Validate generated diagram sources and diagram consistency.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: diagrams-check
diagrams-check:
	$(PYTHON) scripts/validation/validate_diagrams_index.py
	@echo "OK: existing Blueprint diagram artifacts are documented and valid."

# Target: diagrams-list
# Purpose: List managed diagram definitions/artifacts without changing them.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: LOCAL/FOCUSED — only the selected status/artifact/query surface.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: diagrams-list
diagrams-list:
	@find diagrams -maxdepth 1 -type f | sort

# Target: guides
# Purpose: Generate managed module guide artifacts.
# Safety: GENERATED-ARTIFACT WRITE — writes only the documented generated/report/package surface; no release/commit/push authority.
# Inputs: None.
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: guides
guides:
	$(PYTHON) scripts/generate_module_guides.py

# Target: manifest-example
# Purpose: Validate the configured example module manifest.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: manifest-example
manifest-example:
	$(PYTHON) scripts/validate_module_manifest.py "$(BLUEPRINT_MODULE_MANIFEST_EXAMPLE)"


# =============================================================================
# 06 Prompt preparation / release / queue navigation
# =============================================================================
# Block scope: Prompt lifecycle and queue-facing operator commands.

# Target: prompt-dispatch
# Purpose: Run the deprecated Prompt Queue v0.2 compatibility validation alias; it does not dispatch work.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: prompt-dispatch
prompt-dispatch:
	@echo "DEPRECATED compatibility alias: validating Prompt Queue v0.2"
	$(PYTHON) scripts/coordination/validate_prompt_queue.py

# Target: outgoing-prompts
# Purpose: Validate Blueprint outgoing prompt artifacts.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: outgoing-prompts
outgoing-prompts:
	$(PYTHON) scripts/validate_outgoing_prompts.py

# is explicit and never releases, commits, pushes, merges, or writes to modules.
# Target: prompt-prepare
# Purpose: Validate a managed prompt source and optionally prepare its Blueprint-owned draft artifact.
# Safety: CONDITIONAL MUTATION — APPLY=0 validates/previews only; APPLY=1 writes only the prepared Blueprint prompt artifact. REPLACE=1 is separately explicit.
# Inputs: SOURCE (required), APPLY (optional/defaulted), REPLACE (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: Preview/evaluation is reported; when explicit apply inputs authorize mutation, only the target's documented state is written.
.PHONY: prompt-prepare
prompt-prepare:
	@set -eu; \
		if [ -z "$(SOURCE)" ]; then \
			echo "FAILED: prompt-prepare requires SOURCE=<managed prompt source path>"; \
			exit 2; \
		fi; \
		case "$(APPLY)" in \
			0|1) ;; \
			*) echo "FAILED: APPLY must be 0 or 1"; exit 2 ;; \
		esac; \
		case "$(REPLACE)" in \
			0|1) ;; \
			*) echo "FAILED: REPLACE must be 0 or 1"; exit 2 ;; \
		esac; \
		set -- prepare --root "." --source "$(SOURCE)"; \
		if [ "$(APPLY)" = "1" ]; then set -- "$$@" --apply; fi; \
		if [ "$(REPLACE)" = "1" ]; then set -- "$$@" --replace; fi; \
		$(PYTHON) scripts/coordination/manage_outgoing_prompt.py "$$@"; \
		if [ "$(APPLY)" = "1" ]; then \
			$(PYTHON) scripts/coordination/validate_prompt_queue.py; \
			$(PYTHON) scripts/validate_outgoing_prompts.py; \
		fi

# Blueprint release policy. MODULE must be passed explicitly despite its global
# navigation default. Never writes to a module repository or commit/push/merge.
# Target: prompt-release
# Purpose: Validate release conditions and optionally publish one prepared prompt into Prompt Queue v0.2.
# Safety: CONDITIONAL MUTATION — APPLY=0 evaluates only; APPLY=1 may publish one prepared prompt only when governance gates authorize release.
# Inputs: MODULE (required), PROMPT_ID (required), APPLY (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: Preview/evaluation is reported; when explicit apply inputs authorize mutation, only the target's documented state is written.
.PHONY: prompt-release
prompt-release:
	@set -eu; \
		if [ "$(origin MODULE)" != "command line" ]; then \
			echo "FAILED: prompt-release requires explicit MODULE=<canonical module id>; the default MODULE is not accepted"; \
			exit 2; \
		fi; \
		if [ -z "$(MODULE)" ]; then \
			echo "FAILED: prompt-release requires MODULE=<canonical module id>"; \
			exit 2; \
		fi; \
		if [ -z "$(PROMPT_ID)" ]; then \
			echo "FAILED: prompt-release requires PROMPT_ID=<canonical prompt id>"; \
			exit 2; \
		fi; \
		case "$(APPLY)" in \
			0|1) ;; \
			*) echo "FAILED: APPLY must be 0 or 1"; exit 2 ;; \
		esac; \
		set -- release --root "." --module "$(MODULE)" --prompt-id "$(PROMPT_ID)"; \
		if [ "$(APPLY)" = "1" ]; then set -- "$$@" --apply; fi; \
		$(PYTHON) scripts/coordination/manage_outgoing_prompt.py "$$@"; \
		if [ "$(APPLY)" = "1" ]; then \
			$(PYTHON) scripts/coordination/validate_prompt_queue.py; \
			$(PYTHON) scripts/validate_outgoing_prompts.py; \
		fi


# Target: prompt-queue-validate
# Purpose: Validate Prompt Queue structure and queue records.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: prompt-queue-validate
prompt-queue-validate:
	$(PYTHON) scripts/coordination/validate_prompt_queue.py

# Target: prompt-dashboard
# Purpose: Render the human-readable prompt queue dashboard for the selected module.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: MODULE (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: prompt-dashboard
prompt-dashboard:
	$(PYTHON) scripts/coordination/render_prompt_dashboard.py --module "$(MODULE)"

# Target: prompt-status
# Purpose: Render canonical read-only prompt status for the selected module.
# Safety: READ-ONLY — renders prompt state only; does not prepare, release, or mutate prompts.
# Inputs: MODULE (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: prompt-status
prompt-status:
	$(MAKE) prompt-dashboard MODULE="$(MODULE)"

# Target: prompt-next
# Purpose: Resolve the next queue item that is currently eligible for the selected module.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: MODULE (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: prompt-next
prompt-next:
	$(PYTHON) scripts/coordination/resolve_next_prompt.py --module "$(MODULE)"

# Target: prompt-read-next
# Purpose: Resolve and print the next eligible prompt content for the selected module.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: MODULE (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: prompt-read-next
prompt-read-next:
	$(PYTHON) scripts/coordination/resolve_next_prompt.py --module "$(MODULE)" --read


# 12A Completion intake / finalization / next work START


# =============================================================================
# 07 Completion intake / review / next-work resolution
# =============================================================================
# Block scope: Module completion evidence intake and review decisions.

# Target: completion-revision-status
# Purpose: Render completion exchange revision lifecycle status.
# Safety: READ-ONLY — Blueprint revision lifecycle status only.
# Inputs: None.
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: completion-revision-status completion-revision-check
completion-revision-status:
	$(PYTHON) scripts/coordination/completion_revision_status.py --root "."

# Target: completion-revision-check
# Purpose: Validate completion exchange revision lifecycle consistency.
# Safety: READ-ONLY — validates Blueprint revision lifecycle only.
# Inputs: None.
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
completion-revision-check:
	$(PYTHON) scripts/coordination/completion_revision_status.py --root "." --output-format yaml

# without fetch/checkout/restore and never executes module code.
# Target: completion-intake-check
# Purpose: Independently verify published module completion evidence without accepting it.
# Safety: READ-ONLY WITH NETWORK READ — may use git ls-remote to verify published evidence; writes neither Blueprint nor module repositories.
# Inputs: MODULE (required), MODULE_ROOT (required), PACKET (required), COMPLETION_COMMIT (required), REMOTE (optional/defaulted), BRANCH (optional/defaulted), ALLOW_CANDIDATE_REFERENCE (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: completion-intake-check
completion-intake-check:
	@set -eu; \
		if [ -z "$(MODULE)" ]; then echo "FAILED: provide MODULE=<canonical module id>"; exit 2; fi; \
		if [ -z "$(MODULE_ROOT)" ]; then echo "FAILED: provide MODULE_ROOT=<module repository path>"; exit 2; fi; \
		if [ -z "$(PACKET)" ]; then echo "FAILED: provide PACKET=<module-relative completion packet path>"; exit 2; fi; \
		if [ -z "$(COMPLETION_COMMIT)" ]; then echo "FAILED: provide COMPLETION_COMMIT=<published commit>"; exit 2; fi; \
		set -- \
			--root "." \
			--module "$(MODULE)" \
			--module-root "$(MODULE_ROOT)" \
			--packet "$(PACKET)" \
			--completion-commit "$(COMPLETION_COMMIT)" \
			--remote "$(REMOTE)"; \
		if [ -n "$(BRANCH)" ]; then set -- "$$@" --branch "$(BRANCH)"; fi; \
		if [ "$(ALLOW_CANDIDATE_REFERENCE)" = "1" ]; then set -- "$$@" --allow-candidate-reference; fi; \
		$(PYTHON) scripts/coordination/completion_intake_check.py "$$@"

# Target: completion-intake-preview
# Purpose: Build and show the acceptance intake plan after the same read-only completion check.
# Safety: READ-ONLY — builds/prints the intake plan only; writes neither Blueprint nor module repository state.
# Inputs: MODULE (required), MODULE_ROOT (required), PACKET (required), COMPLETION_COMMIT (required), REMOTE (optional/defaulted), BRANCH (optional/defaulted), REVIEW_NOTES (optional/defaulted), REVIEWED_AT (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: completion-intake-preview
completion-intake-preview:
	@set -eu; \
		if [ -z "$(MODULE)" ]; then echo "FAILED: provide MODULE=<canonical module id>"; exit 2; fi; \
		if [ -z "$(MODULE_ROOT)" ]; then echo "FAILED: provide MODULE_ROOT=<module repository path>"; exit 2; fi; \
		if [ -z "$(PACKET)" ]; then echo "FAILED: provide PACKET=<module-relative completion packet path>"; exit 2; fi; \
		if [ -z "$(COMPLETION_COMMIT)" ]; then echo "FAILED: provide COMPLETION_COMMIT=<published commit>"; exit 2; fi; \
		set -- \
			--root "." \
			--module "$(MODULE)" \
			--module-root "$(MODULE_ROOT)" \
			--packet "$(PACKET)" \
			--decision accepted \
			--completion-commit "$(COMPLETION_COMMIT)" \
			--remote "$(REMOTE)"; \
		if [ -n "$(BRANCH)" ]; then set -- "$$@" --branch "$(BRANCH)"; fi; \
		if [ -n "$(REVIEW_NOTES)" ]; then set -- "$$@" --review-notes "$(REVIEW_NOTES)"; fi; \
		if [ -n "$(REVIEWED_AT)" ]; then set -- "$$@" --reviewed-at "$(REVIEWED_AT)"; fi; \
		$(PYTHON) scripts/coordination/module_completion_intake.py "$$@"

# independently blocks writes unless completion-intake-check passed.
# Target: completion-accept
# Purpose: Record acceptance of validated module completion evidence in Blueprint coordination state.
# Safety: BLUEPRINT MUTATION — writes only Blueprint-owned review/queue/roadmap coordination state after successful read-only intake checks; never writes the module repository.
# Inputs: MODULE (required), MODULE_ROOT (required), PACKET (required), COMPLETION_COMMIT (required), REMOTE (optional/defaulted), BRANCH (optional/defaulted), REVIEW_NOTES (optional/defaulted), REVIEWED_AT (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: completion-accept
completion-accept:
	@set -eu; \
		if [ -z "$(MODULE)" ]; then echo "FAILED: provide MODULE=<canonical module id>"; exit 2; fi; \
		if [ -z "$(MODULE_ROOT)" ]; then echo "FAILED: provide MODULE_ROOT=<module repository path>"; exit 2; fi; \
		if [ -z "$(PACKET)" ]; then echo "FAILED: provide PACKET=<module-relative completion packet path>"; exit 2; fi; \
		if [ -z "$(COMPLETION_COMMIT)" ]; then echo "FAILED: provide COMPLETION_COMMIT=<published commit>"; exit 2; fi; \
		set -- \
			--root "." \
			--module "$(MODULE)" \
			--module-root "$(MODULE_ROOT)" \
			--packet "$(PACKET)" \
			--decision accepted \
			--completion-commit "$(COMPLETION_COMMIT)" \
			--remote "$(REMOTE)" \
			--write; \
		if [ -n "$(BRANCH)" ]; then set -- "$$@" --branch "$(BRANCH)"; fi; \
		if [ -n "$(REVIEW_NOTES)" ]; then set -- "$$@" --review-notes "$(REVIEW_NOTES)"; fi; \
		if [ -n "$(REVIEWED_AT)" ]; then set -- "$$@" --reviewed-at "$(REVIEWED_AT)"; fi; \
		$(PYTHON) scripts/coordination/module_completion_intake.py "$$@"

# queue/roadmap/review records. It never mutates the module repository.
# Target: completion-return
# Purpose: Return completion evidence for correction with explicit operator review notes.
# Safety: BLUEPRINT MUTATION — writes only Blueprint-owned review/return records; never writes the module repository.
# Inputs: MODULE (required), MODULE_ROOT (required), PACKET (required), REVIEW_NOTES (required), COMPLETION_COMMIT (optional/defaulted), REVIEWED_AT (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: completion-return
completion-return:
	@set -eu; \
		if [ -z "$(MODULE)" ]; then echo "FAILED: provide MODULE=<canonical module id>"; exit 2; fi; \
		if [ -z "$(MODULE_ROOT)" ]; then echo "FAILED: provide MODULE_ROOT=<module repository path>"; exit 2; fi; \
		if [ -z "$(PACKET)" ]; then echo "FAILED: provide PACKET=<module-relative completion packet path>"; exit 2; fi; \
		if [ -z "$(REVIEW_NOTES)" ]; then echo "FAILED: completion-return requires REVIEW_NOTES=..."; exit 2; fi; \
		set -- \
			--root "." \
			--module "$(MODULE)" \
			--module-root "$(MODULE_ROOT)" \
			--packet "$(PACKET)" \
			--decision returned_for_fix \
			--review-notes "$(REVIEW_NOTES)" \
			--write; \
		if [ -n "$(COMPLETION_COMMIT)" ]; then set -- "$$@" --completion-commit "$(COMPLETION_COMMIT)"; fi; \
		if [ -n "$(REVIEWED_AT)" ]; then set -- "$$@" --reviewed-at "$(REVIEWED_AT)"; fi; \
		$(PYTHON) scripts/coordination/module_completion_intake.py "$$@"

# Target: next-work-suggestion
# Purpose: Render the next Blueprint coordination action suggested for the selected module.
# Safety: READ-ONLY — resolves and prints a suggestion only.
# Inputs: MODULE (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: next-work-suggestion
next-work-suggestion:
	$(PYTHON) scripts/coordination/resolve_next_module_work.py --root "." --module "$(MODULE)"

# Target: completion-finalize-check
# Purpose: Validate queue and roadmap state after an explicit completion accept/return action.
# Safety: READ-ONLY — validates post-decision queue/roadmap state; does not finalize or write completion state.
# Inputs: MODULE (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: completion-finalize-check
completion-finalize-check:
	$(PYTHON) scripts/coordination/validate_prompt_queue.py --root "."
	$(PYTHON) scripts/coordination/validate_module_roadmap.py --root "." --module "$(MODULE)"
	$(PYTHON) scripts/coordination/resolve_next_module_work.py --root "." --module "$(MODULE)"

# 12A Completion intake / finalization / next work FINISH


# =============================================================================
# 08 Context / launch / approval / worker control surfaces
# =============================================================================
# Block scope: Scoped context and control-plane preparation/runtime commands.

# Target: document-manifest
# Purpose: Build the coordination document manifest in read-only/no-write mode.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: document-manifest
document-manifest:
	$(PYTHON) scripts/coordination/build_document_manifest.py --no-write

# Target: document-manifest-write
# Purpose: Build and write generated coordination document-manifest artifacts.
# Safety: GENERATED-ARTIFACT WRITE — writes only the documented generated/report/package surface; no release/commit/push authority.
# Inputs: None.
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: document-manifest-write
document-manifest-write:
	$(PYTHON) scripts/coordination/build_document_manifest.py

# Target: document-awareness
# Purpose: Render module-scoped awareness of current Blueprint coordination documents.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: MODULE (optional/defaulted), LIMIT (optional/defaulted).
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: document-awareness
document-awareness:
	$(PYTHON) scripts/coordination/render_document_awareness_dashboard.py --module "$(MODULE)" --limit "$(LIMIT)"

# Target: context-bundle
# Purpose: Build a scoped module context bundle in memory without writing an artifact.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: MODULE (optional/defaulted), SCOPE (optional/defaulted), LIMIT (optional/defaulted).
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: context-bundle
context-bundle:
	$(PYTHON) scripts/coordination/build_context_bundle.py --module "$(MODULE)" --scope "$(SCOPE)" --limit "$(LIMIT)" --no-write

# Target: context-bundle-write
# Purpose: Build and write a scoped module context bundle artifact.
# Safety: GENERATED-ARTIFACT WRITE — writes only the documented generated/report/package surface; no release/commit/push authority.
# Inputs: MODULE (optional/defaulted), SCOPE (optional/defaulted), LIMIT (optional/defaulted).
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: context-bundle-write
context-bundle-write:
	$(PYTHON) scripts/coordination/build_context_bundle.py --module "$(MODULE)" --scope "$(SCOPE)" --limit "$(LIMIT)"

# Target: context-bundle-print
# Purpose: Build and print the selected module context bundle to stdout.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: MODULE (optional/defaulted), SCOPE (optional/defaulted), LIMIT (optional/defaulted).
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: context-bundle-print
context-bundle-print:
	$(PYTHON) scripts/coordination/build_context_bundle.py --module "$(MODULE)" --scope "$(SCOPE)" --limit "$(LIMIT)" --print

TASK_PROMPT_ID ?=
TASK_MODULE_ROOT ?=
TASK_CONTEXT_OUTPUT_DIR ?= tmp/task_context_bundles

# Target: task-context-compiler-check
# Purpose: Validate the task-context compiler contract and its tests.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: task-context-compiler-check
task-context-compiler-check:
	$(PYTHON) scripts/validation/validate_task_context_compiler_v0_1.py
	$(PYTHON) -m pytest -q tests/coordination/test_task_context_compiler_v0_1.py

# Target: task-context-check
# Purpose: Validate a task-specific context bundle request without writing the bundle.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: TASK_PROMPT_ID (required), TASK_MODULE_ROOT (required), MODULE (optional/defaulted).
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: task-context-check
task-context-check:
	@test -n "$(TASK_PROMPT_ID)" || { echo "FAILED: TASK_PROMPT_ID is required"; exit 1; }
	@test -n "$(TASK_MODULE_ROOT)" || { echo "FAILED: TASK_MODULE_ROOT is required"; exit 1; }
	$(PYTHON) scripts/coordination/build_context_bundle.py --module "$(MODULE)" --task-context --prompt-id "$(TASK_PROMPT_ID)" --module-root "$(TASK_MODULE_ROOT)" --no-write

# Target: task-context-compile
# Purpose: Compile and write a task-specific context bundle for the selected module and prompt.
# Safety: GENERATED-ARTIFACT WRITE — writes only the documented generated/report/package surface; no release/commit/push authority.
# Inputs: TASK_PROMPT_ID (required), TASK_MODULE_ROOT (required), MODULE (optional/defaulted), TASK_CONTEXT_OUTPUT_DIR (optional/defaulted).
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: task-context-compile
task-context-compile:
	@test -n "$(TASK_PROMPT_ID)" || { echo "FAILED: TASK_PROMPT_ID is required"; exit 1; }
	@test -n "$(TASK_MODULE_ROOT)" || { echo "FAILED: TASK_MODULE_ROOT is required"; exit 1; }
	$(PYTHON) scripts/coordination/build_context_bundle.py --module "$(MODULE)" --task-context --prompt-id "$(TASK_PROMPT_ID)" --module-root "$(TASK_MODULE_ROOT)" --output-dir "$(TASK_CONTEXT_OUTPUT_DIR)"

# Target: task-context-print
# Purpose: Compile and print task-specific context to stdout without persisting a bundle.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: TASK_PROMPT_ID (required), TASK_MODULE_ROOT (required), MODULE (optional/defaulted).
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: task-context-print
task-context-print:
	@test -n "$(TASK_PROMPT_ID)" || { echo "FAILED: TASK_PROMPT_ID is required"; exit 1; }
	@test -n "$(TASK_MODULE_ROOT)" || { echo "FAILED: TASK_MODULE_ROOT is required"; exit 1; }
	$(PYTHON) scripts/coordination/build_context_bundle.py --module "$(MODULE)" --task-context --prompt-id "$(TASK_PROMPT_ID)" --module-root "$(TASK_MODULE_ROOT)" --print


DEPENDENCY_READINESS ?=
LAUNCH_REQUEST_OUTPUT_DIR ?= tmp/control_plane/launch_requests

# Target: launch-request-gate-check
# Purpose: Validate the launch-request gate contract and tests.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: launch-request-gate-check
launch-request-gate-check:
	$(PYTHON) scripts/validation/validate_launch_request_fresh_context_gate_v0_1.py
	$(PYTHON) -m pytest -q tests/coordination/test_launch_request_fresh_context_gate_v0_1.py

# Target: launch-request-evaluate
# Purpose: Evaluate whether a task-context archive satisfies launch-request prerequisites without writing a request.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: TASK_MODULE_ROOT (required), TASK_CONTEXT_ARCHIVE (required), DEPENDENCY_READINESS (optional/defaulted).
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: launch-request-evaluate
launch-request-evaluate:
	@test -n "$(TASK_MODULE_ROOT)" || { echo "FAILED: TASK_MODULE_ROOT is required"; exit 1; }
	@test -n "$(TASK_CONTEXT_ARCHIVE)" || { echo "FAILED: TASK_CONTEXT_ARCHIVE is required"; exit 1; }
	$(PYTHON) scripts/coordination/build_launch_request.py --module-root "$(TASK_MODULE_ROOT)" --task-context-archive "$(TASK_CONTEXT_ARCHIVE)" $(if $(DEPENDENCY_READINESS),--dependency-readiness "$(DEPENDENCY_READINESS)",) --no-write

# Target: launch-request-build
# Purpose: Build a launch-request artifact from a validated task-context archive.
# Safety: GENERATED-ARTIFACT WRITE — writes only the documented generated/report/package surface; no release/commit/push authority.
# Inputs: TASK_MODULE_ROOT (required), TASK_CONTEXT_ARCHIVE (required), DEPENDENCY_READINESS (optional/defaulted), LAUNCH_REQUEST_OUTPUT_DIR (optional/defaulted).
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: launch-request-build
launch-request-build:
	@test -n "$(TASK_MODULE_ROOT)" || { echo "FAILED: TASK_MODULE_ROOT is required"; exit 1; }
	@test -n "$(TASK_CONTEXT_ARCHIVE)" || { echo "FAILED: TASK_CONTEXT_ARCHIVE is required"; exit 1; }
	$(PYTHON) scripts/coordination/build_launch_request.py --module-root "$(TASK_MODULE_ROOT)" --task-context-archive "$(TASK_CONTEXT_ARCHIVE)" $(if $(DEPENDENCY_READINESS),--dependency-readiness "$(DEPENDENCY_READINESS)",) --output-dir "$(LAUNCH_REQUEST_OUTPUT_DIR)"

OPERATOR_APPROVAL_OUTPUT_DIR ?= tmp/control_plane/operator_approval_decisions
OPERATOR_DECISION ?=
OPERATOR_ACTOR ?=
OPERATOR_REASON ?=
OPERATOR_EXPIRES_MINUTES ?= 30
APPROVAL_DECISION ?=

# Target: operator-approval-gateway-check
# Purpose: Validate the operator-approval gateway contract and tests.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: operator-approval-gateway-check
operator-approval-gateway-check:
	$(PYTHON) scripts/validation/validate_operator_approval_gateway_v0_1.py
	$(PYTHON) -m pytest -q tests/coordination/test_operator_approval_gateway_v0_1.py

# Target: operator-approval-evaluate
# Purpose: Evaluate whether a launch request requires or satisfies operator approval.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: TASK_MODULE_ROOT (required), LAUNCH_REQUEST (required).
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: operator-approval-evaluate
operator-approval-evaluate:
	@test -n "$(TASK_MODULE_ROOT)" || { echo "FAILED: TASK_MODULE_ROOT is required"; exit 1; }
	@test -n "$(LAUNCH_REQUEST)" || { echo "FAILED: LAUNCH_REQUEST is required"; exit 1; }
	$(PYTHON) scripts/coordination/build_operator_approval_decision.py --module-root "$(TASK_MODULE_ROOT)" --launch-request "$(LAUNCH_REQUEST)" --evaluate

# Target: operator-approval-decide
# Purpose: Write an explicit operator approval/hold/reject decision artifact for a launch request.
# Safety: DECISION ARTIFACT WRITE — writes only the explicit bounded operator decision artifact supplied by operator inputs.
# Inputs: TASK_MODULE_ROOT (required), LAUNCH_REQUEST (required), OPERATOR_DECISION (required), OPERATOR_ACTOR (required), OPERATOR_REASON (required), OPERATOR_EXPIRES_MINUTES (optional/defaulted), OPERATOR_APPROVAL_OUTPUT_DIR (optional/defaulted).
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: operator-approval-decide
operator-approval-decide:
	@test -n "$(TASK_MODULE_ROOT)" || { echo "FAILED: TASK_MODULE_ROOT is required"; exit 1; }
	@test -n "$(LAUNCH_REQUEST)" || { echo "FAILED: LAUNCH_REQUEST is required"; exit 1; }
	@test -n "$(OPERATOR_DECISION)" || { echo "FAILED: OPERATOR_DECISION is required"; exit 1; }
	@test -n "$(OPERATOR_ACTOR)" || { echo "FAILED: OPERATOR_ACTOR is required"; exit 1; }
	@test -n "$(OPERATOR_REASON)" || { echo "FAILED: OPERATOR_REASON is required"; exit 1; }
	$(PYTHON) scripts/coordination/build_operator_approval_decision.py --module-root "$(TASK_MODULE_ROOT)" --launch-request "$(LAUNCH_REQUEST)" --decision "$(OPERATOR_DECISION)" --decided-by "$(OPERATOR_ACTOR)" --reason "$(OPERATOR_REASON)" --expires-in-minutes "$(OPERATOR_EXPIRES_MINUTES)" --output-dir "$(OPERATOR_APPROVAL_OUTPUT_DIR)"

# Target: operator-approval-validate
# Purpose: Validate an operator approval decision against its launch request.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: TASK_MODULE_ROOT (required), LAUNCH_REQUEST (required), APPROVAL_DECISION (required).
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: operator-approval-validate
operator-approval-validate:
	@test -n "$(TASK_MODULE_ROOT)" || { echo "FAILED: TASK_MODULE_ROOT is required"; exit 1; }
	@test -n "$(LAUNCH_REQUEST)" || { echo "FAILED: LAUNCH_REQUEST is required"; exit 1; }
	@test -n "$(APPROVAL_DECISION)" || { echo "FAILED: APPROVAL_DECISION is required"; exit 1; }
	$(PYTHON) scripts/coordination/build_operator_approval_decision.py --module-root "$(TASK_MODULE_ROOT)" --launch-request "$(LAUNCH_REQUEST)" --validate-decision "$(APPROVAL_DECISION)"

WORKER_RUNTIME ?=
WORKER_INVOCATION_OUTPUT_DIR ?= tmp/control_plane/worker_invocations
WORKER_COMPLETION_ROOT ?= tmp/control_plane/worker_runs

# Target: console-worker-adapter-check
# Purpose: Validate the console worker adapter contract and tests.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: console-worker-adapter-check
console-worker-adapter-check:
	$(PYTHON) scripts/validation/validate_console_worker_adapter_v0_1.py
	$(PYTHON) -m pytest -q tests/coordination/test_console_worker_adapter_v0_1.py

# Target: worker-invocation-evaluate
# Purpose: Evaluate a prospective worker invocation without creating the invocation artifact.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: TASK_MODULE_ROOT (required), LAUNCH_REQUEST (required), WORKER_RUNTIME (required), APPROVAL_DECISION (optional/defaulted), WORKER_COMPLETION_ROOT (optional/defaulted).
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: worker-invocation-evaluate
worker-invocation-evaluate:
	@test -n "$(TASK_MODULE_ROOT)" || { echo "FAILED: TASK_MODULE_ROOT is required"; exit 1; }
	@test -n "$(LAUNCH_REQUEST)" || { echo "FAILED: LAUNCH_REQUEST is required"; exit 1; }
	@test -n "$(WORKER_RUNTIME)" || { echo "FAILED: WORKER_RUNTIME is required"; exit 1; }
	$(PYTHON) scripts/coordination/build_worker_invocation.py --module-root "$(TASK_MODULE_ROOT)" --launch-request "$(LAUNCH_REQUEST)" --runtime "$(WORKER_RUNTIME)" $(if $(APPROVAL_DECISION),--approval-decision "$(APPROVAL_DECISION)",) --completion-root "$(WORKER_COMPLETION_ROOT)" --no-write

# Target: worker-invocation-build
# Purpose: Build a worker invocation artifact from a launch request and runtime selection.
# Safety: GENERATED-ARTIFACT WRITE — writes only the documented generated/report/package surface; no release/commit/push authority.
# Inputs: TASK_MODULE_ROOT (required), LAUNCH_REQUEST (required), WORKER_RUNTIME (required), APPROVAL_DECISION (optional/defaulted), WORKER_COMPLETION_ROOT (optional/defaulted), WORKER_INVOCATION_OUTPUT_DIR (optional/defaulted).
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: worker-invocation-build
worker-invocation-build:
	@test -n "$(TASK_MODULE_ROOT)" || { echo "FAILED: TASK_MODULE_ROOT is required"; exit 1; }
	@test -n "$(LAUNCH_REQUEST)" || { echo "FAILED: LAUNCH_REQUEST is required"; exit 1; }
	@test -n "$(WORKER_RUNTIME)" || { echo "FAILED: WORKER_RUNTIME is required"; exit 1; }
	$(PYTHON) scripts/coordination/build_worker_invocation.py --module-root "$(TASK_MODULE_ROOT)" --launch-request "$(LAUNCH_REQUEST)" --runtime "$(WORKER_RUNTIME)" $(if $(APPROVAL_DECISION),--approval-decision "$(APPROVAL_DECISION)",) --completion-root "$(WORKER_COMPLETION_ROOT)" --output-dir "$(WORKER_INVOCATION_OUTPUT_DIR)"


CONTROL_PLANE_RUNTIME_DIR ?= tmp/control_plane/runtime
WORKER_INVOCATION ?=
CONTROL_PLANE_EVENT_ROOT ?=
CONTROL_PLANE_ACTIVE_EXECUTION ?=

# Target: control-plane-runtime-check
# Purpose: Validate control-plane runtime behavior and tests.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: control-plane-runtime-check
control-plane-runtime-check:
	$(PYTHON) scripts/validation/control_plane/validate_central_listener_dispatcher_monitor_v0_1.py
	$(PYTHON) -m pytest -q tests/coordination/control_plane/test_central_listener_dispatcher_monitor_v0_1.py

# Target: control-plane-step
# Purpose: Advance one bounded control-plane runtime step using supplied launch and invocation artifacts.
# Safety: RUNTIME-STATE MUTATION — advances one bounded control-plane runtime step only for the explicitly supplied artifacts.
# Inputs: LAUNCH_REQUEST (required), WORKER_INVOCATION (required), APPROVAL_DECISION (optional/defaulted), CONTROL_PLANE_EVENT_ROOT (optional/defaulted), CONTROL_PLANE_ACTIVE_EXECUTION (optional/defaulted), CONTROL_PLANE_RUNTIME_DIR (optional/defaulted).
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: control-plane-step
control-plane-step:
	@test -n "$(LAUNCH_REQUEST)" || { echo "FAILED: LAUNCH_REQUEST is required"; exit 1; }
	@test -n "$(WORKER_INVOCATION)" || { echo "FAILED: WORKER_INVOCATION is required"; exit 1; }
	$(PYTHON) -m scripts.coordination.control_plane.runtime --launch-request "$(LAUNCH_REQUEST)" --worker-invocation "$(WORKER_INVOCATION)" $(if $(APPROVAL_DECISION),--approval-decision "$(APPROVAL_DECISION)",) $(if $(CONTROL_PLANE_EVENT_ROOT),--event-root "$(CONTROL_PLANE_EVENT_ROOT)",) $(if $(CONTROL_PLANE_ACTIVE_EXECUTION),--active-execution "$(CONTROL_PLANE_ACTIVE_EXECUTION)",) --runtime-dir "$(CONTROL_PLANE_RUNTIME_DIR)"

# Target: control-plane-status
# Purpose: Render current control-plane runtime status for the supplied launch/invocation artifacts.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: LAUNCH_REQUEST (required), WORKER_INVOCATION (required), APPROVAL_DECISION (optional/defaulted), CONTROL_PLANE_RUNTIME_DIR (optional/defaulted).
# Scope: LOCAL/FOCUSED — only the selected status/artifact/query surface.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: control-plane-status
control-plane-status:
	@test -n "$(LAUNCH_REQUEST)" || { echo "FAILED: LAUNCH_REQUEST is required"; exit 1; }
	@test -n "$(WORKER_INVOCATION)" || { echo "FAILED: WORKER_INVOCATION is required"; exit 1; }
	$(PYTHON) -m scripts.coordination.control_plane.runtime --launch-request "$(LAUNCH_REQUEST)" --worker-invocation "$(WORKER_INVOCATION)" $(if $(APPROVAL_DECISION),--approval-decision "$(APPROVAL_DECISION)",) --runtime-dir "$(CONTROL_PLANE_RUNTIME_DIR)" --no-write --print


# Target: completion-control-plane-check
# Purpose: Validate completion-control-plane integration and tests.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: completion-control-plane-check
completion-control-plane-check:
	$(PYTHON) scripts/validation/control_plane/completion/validate_completion_intake_inspector_conformance_v0_1.py
	$(PYTHON) -m pytest -q tests/coordination/control_plane/completion/test_completion_intake_inspector_conformance_v0_1.py

# Target: bootstrap-task-context-check
# Purpose: Validate bootstrap task-context wiring.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: bootstrap-task-context-check
bootstrap-task-context-check:
	$(PYTHON) scripts/validation/control_plane/context/validate_bootstrap_task_context_mode_v0_1.py
	$(PYTHON) -m pytest -q tests/coordination/control_plane/context/test_bootstrap_task_context_mode_v0_1.py

# Target: module-readiness-levels-check
# Purpose: Validate module readiness-level contracts.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: module-readiness-levels-check
module-readiness-levels-check:
	$(PYTHON) scripts/validation/control_plane/readiness/validate_module_readiness_levels_v0_1.py
	$(PYTHON) -m pytest -q tests/coordination/control_plane/readiness/test_module_readiness_levels_v0_1.py

# Target: bootstrap-worker-runtime-check
# Purpose: Validate bootstrap worker-runtime contracts.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: bootstrap-worker-runtime-check
bootstrap-worker-runtime-check:
	$(PYTHON) scripts/validation/control_plane/worker_runtime/validate_bootstrap_worker_runtime_profile_v0_1.py
	$(PYTHON) -m pytest -q tests/coordination/control_plane/worker_runtime/test_bootstrap_worker_runtime_profile_v0_1.py

# Target: inspector-reviewer-registry-check
# Purpose: Validate inspector/reviewer registry contracts.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: inspector-reviewer-registry-check
inspector-reviewer-registry-check:
	$(PYTHON) scripts/validation/control_plane/inspection/validate_inspector_reviewer_registry_v0_1.py
	$(PYTHON) -m pytest -q tests/coordination/control_plane/inspection/test_inspector_reviewer_registry_v0_1.py

# Target: module-bootstrap-prompt-check
# Purpose: Validate module bootstrap prompt requirements and candidate integration.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: module-bootstrap-prompt-check
module-bootstrap-prompt-check:
	$(PYTHON) scripts/validation/control_plane/context/validate_module_bootstrap_prompt_requirements_v0_1.py
	$(PYTHON) scripts/validation/control_plane/context/validate_logistics_bootstrap_prompt_v0_2_candidate.py
	$(PYTHON) -m pytest -q tests/coordination/control_plane/context/test_module_bootstrap_prompt_requirements_v0_1.py

# Target: project-context-bootstrap-check
# Purpose: Validate project-context bootstrap behavior and dry-run package selection.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: PROJECT_ONBOARD — whole-project onboarding context bounded by the handoff contract.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: project-context-bootstrap-check
project-context-bootstrap-check:
	$(PYTHON) scripts/validation/validate_project_context_bootstrap_v0_1.py
	$(PYTHON) -m pytest -q tests/coordination/test_project_context_bootstrap_v0_1.py
	$(PYTHON) scripts/coordination/build_project_context_archive.py --root . --dry-run

# Target: module-roadmap-reconciliation-check
# Purpose: Validate module roadmap reconciliation behavior.
# Safety: READ-ONLY WITH REPORT/TMP OUTPUT — may refresh diagnostic/generated evidence, but does not change execution authority.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: module-roadmap-reconciliation-check
module-roadmap-reconciliation-check:
	$(PYTHON) scripts/validation/validate_module_roadmap_reconciliation_v0_1.py
	$(PYTHON) -m pytest -q tests/coordination/test_module_roadmap_reconciliation_v0_1.py
	$(PYTHON) scripts/coordination/build_module_roadmap_reconciliation.py --root . --module logistics_service --output tmp/module_roadmap_reconciliation_check/logistics_service.yaml

# Target: logistics-semantic-roadmap-reconciliation-check
# Purpose: Validate Logistics semantic roadmap reconciliation behavior.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: logistics-semantic-roadmap-reconciliation-check
logistics-semantic-roadmap-reconciliation-check:
	$(PYTHON) scripts/validation/validate_logistics_semantic_roadmap_reconciliation_v0_1.py
	$(PYTHON) -m pytest -q tests/coordination/test_logistics_semantic_roadmap_reconciliation_v0_1.py

# Target: module-preparation-registry-check
# Purpose: Build and validate the module preparation registry and queue.
# Safety: GENERATED-ARTIFACT WRITE — writes only the documented generated/report/package surface; no release/commit/push authority.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: module-preparation-registry-check
module-preparation-registry-check:
	$(PYTHON) scripts/coordination/control_plane/preparation/build_module_preparation_registry.py --root . --registry-output coordination/internal_work/blueprint/module_preparation/module_preparation_registry_v0_1.yaml --queue-output coordination/internal_work/blueprint/module_preparation/module_preparation_queue_v0_1.yaml
	$(PYTHON) scripts/validation/control_plane/preparation/validate_module_preparation_registry_v0_1.py
	$(PYTHON) -m pytest -q tests/coordination/control_plane/preparation/test_module_preparation_registry_v0_1.py

# Target: assistant-context-pack
# Purpose: Build a scoped project-context archive for the selected module/topics.
# Safety: GENERATED-ARTIFACT WRITE — creates a scoped context archive for MODULE/TOPICS; this is not the authoritative PROJECT_ONBOARD package route.
# Inputs: MODULE (optional explicit command-line override; default forprint_system_blueprint), TOPICS (optional/defaulted).
# Scope: SCOPED CONTEXT — selected MODULE/TOPICS; not the authoritative PROJECT_ONBOARD route.
# Result: A bounded assistant/context package is generated and its path/validation state is reported.
.PHONY: assistant-context-pack
assistant-context-pack:
	@set -- --root .; \
	module="forprint_system_blueprint"; \
	if [ "$(origin MODULE)" = "command line" ] && [ -n "$(MODULE)" ]; then module="$(MODULE)"; fi; \
	set -- "$$@" --module "$$module"; \
	if [ -n "$(TOPICS)" ]; then set -- "$$@" --topics "$(TOPICS)"; fi; \
	$(PYTHON) scripts/coordination/build_project_context_archive.py "$$@"

# Target: document-ledger-preview
# Purpose: Preview a coordination document-awareness ledger update without writing it.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: DOCUMENT (optional/defaulted), SOURCE (optional/defaulted), PRIORITY (optional/defaulted), MODULE (optional/defaulted), LEDGER (optional/defaulted), STATUS (optional/defaulted), NOTES (optional/defaulted), MODULE_COMMIT (optional/defaulted).
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: document-ledger-preview
document-ledger-preview:
	@set -eu; \
	if [ -z "$(DOCUMENT)$(SOURCE)$(PRIORITY)" ]; then \
		echo "FAILED: provide DOCUMENT=..., SOURCE=..., or PRIORITY=..."; \
		exit 1; \
	fi; \
	set -- --root "." --module "$(MODULE)" --ledger "$(LEDGER)" --status "$(STATUS)"; \
	if [ -n "$(DOCUMENT)" ]; then set -- "$$@" --document "$(DOCUMENT)"; fi; \
	if [ -n "$(SOURCE)" ]; then set -- "$$@" --source "$(SOURCE)"; fi; \
	if [ -n "$(PRIORITY)" ]; then set -- "$$@" --priority "$(PRIORITY)"; fi; \
	if [ -n "$(NOTES)" ]; then set -- "$$@" --notes "$(NOTES)"; fi; \
	if [ -n "$(MODULE_COMMIT)" ]; then set -- "$$@" --module-commit "$(MODULE_COMMIT)"; fi; \
	set -- "$$@" --no-write; \
	$(PYTHON) scripts/coordination/update_document_awareness_ledger.py "$$@"

# Target: document-ledger-update
# Purpose: Apply a coordination document-awareness ledger update.
# Safety: BLUEPRINT MUTATION — writes the documented Blueprint-owned coordination/policy state only.
# Inputs: DOCUMENT (optional/defaulted), SOURCE (optional/defaulted), PRIORITY (optional/defaulted), MODULE (optional/defaulted), LEDGER (optional/defaulted), STATUS (optional/defaulted), NOTES (optional/defaulted), MODULE_COMMIT (optional/defaulted).
# Scope: SCOPED CONTEXT — selected module/task/artifact only.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: document-ledger-update
document-ledger-update:
	@set -eu; \
	if [ -z "$(DOCUMENT)$(SOURCE)$(PRIORITY)" ]; then \
		echo "FAILED: provide DOCUMENT=..., SOURCE=..., or PRIORITY=..."; \
		exit 1; \
	fi; \
	set -- --root "." --module "$(MODULE)" --ledger "$(LEDGER)" --status "$(STATUS)"; \
	if [ -n "$(DOCUMENT)" ]; then set -- "$$@" --document "$(DOCUMENT)"; fi; \
	if [ -n "$(SOURCE)" ]; then set -- "$$@" --source "$(SOURCE)"; fi; \
	if [ -n "$(PRIORITY)" ]; then set -- "$$@" --priority "$(PRIORITY)"; fi; \
	if [ -n "$(NOTES)" ]; then set -- "$$@" --notes "$(NOTES)"; fi; \
	if [ -n "$(MODULE_COMMIT)" ]; then set -- "$$@" --module-commit "$(MODULE_COMMIT)"; fi; \
	$(PYTHON) scripts/coordination/update_document_awareness_ledger.py "$$@"


# =============================================================================
# 09 Module roadmaps / acceptance oracles
# =============================================================================
# Block scope: Roadmap inspection and acceptance-oracle validation.

# Target: roadmap-validate
# Purpose: Validate the selected module roadmap and its invariants.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: ROADMAP (optional/defaulted), MODULE (optional/defaulted).
# Scope: MODULE/ROADMAP — selected MODULE/ROADMAP or configured summary set.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: roadmap-validate
roadmap-validate:
	@if [ -n "$(ROADMAP)" ]; then \
		$(PYTHON) scripts/coordination/validate_module_roadmap.py --roadmap "$(ROADMAP)"; \
	else \
		$(PYTHON) scripts/coordination/validate_module_roadmap.py --module "$(MODULE)"; \
	fi

# Target: roadmap-dashboard
# Purpose: Render the selected module roadmap window around the current position.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: MODULES (optional/defaulted), BEFORE_CURRENT (optional/defaulted), AFTER_CURRENT (optional/defaulted), ROADMAP (optional/defaulted), MODULE (optional/defaulted).
# Scope: MODULE/ROADMAP — selected MODULE/ROADMAP or configured summary set.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: roadmap-dashboard
roadmap-dashboard:
	@if [ -n "$(MODULES)" ]; then \
		$(PYTHON) scripts/coordination/render_module_roadmap_dashboard.py --modules "$(MODULES)" --before-current "$(BEFORE_CURRENT)" --after-current "$(AFTER_CURRENT)"; \
	elif [ -n "$(ROADMAP)" ]; then \
		$(PYTHON) scripts/coordination/render_module_roadmap_dashboard.py --roadmap "$(ROADMAP)" --before-current "$(BEFORE_CURRENT)" --after-current "$(AFTER_CURRENT)"; \
	else \
		$(PYTHON) scripts/coordination/render_module_roadmap_dashboard.py --module "$(MODULE)" --before-current "$(BEFORE_CURRENT)" --after-current "$(AFTER_CURRENT)"; \
	fi

# Target: roadmap-detail
# Purpose: Render detailed roadmap information for the selected module.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: ROADMAP (optional/defaulted), BEFORE_CURRENT (optional/defaulted), AFTER_CURRENT (optional/defaulted), MODULE (optional/defaulted).
# Scope: MODULE/ROADMAP — selected MODULE/ROADMAP or configured summary set.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: roadmap-detail
roadmap-detail:
	@if [ -n "$(ROADMAP)" ]; then \
		$(PYTHON) scripts/coordination/render_module_roadmap_detail.py --roadmap "$(ROADMAP)" --before-current "$(BEFORE_CURRENT)" --after-current "$(AFTER_CURRENT)"; \
	else \
		$(PYTHON) scripts/coordination/render_module_roadmap_detail.py --module "$(MODULE)" --before-current "$(BEFORE_CURRENT)" --after-current "$(AFTER_CURRENT)"; \
	fi

# Target: acceptance-oracle-validate
# Purpose: Validate the supplied acceptance-oracle artifact, optionally against an expected SHA-256.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: ORACLE (optional/defaulted), ORACLE_SHA256 (optional/defaulted).
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: acceptance-oracle-validate
acceptance-oracle-validate:
	@$(PYTHON) scripts/coordination/acceptance_oracle_v0_1.py --root . --oracle "$(ORACLE)" $(if $(ORACLE_SHA256),--sha256 "$(ORACLE_SHA256)",)

# Target: roadmap-summary
# Purpose: Render a summary across the configured roadmap module set.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: ROADMAP_SUMMARY_MODULES (optional/defaulted).
# Scope: PORTFOLIO — configured multi-module/project view.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: roadmap-summary
roadmap-summary:
	$(PYTHON) scripts/coordination/render_module_roadmap_dashboard.py --modules "$(ROADMAP_SUMMARY_MODULES)"


# =============================================================================
# 10 Standards / governance / self-workflow
# =============================================================================
# Block scope: Standards, governance, policy, and durable self-audit workflows.

# Target: standards-index
# Purpose: Validate the Blueprint standards index.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: standards-index
standards-index:
	$(PYTHON) scripts/validate_standards_index.py

# Target: standards
# Purpose: Run the standard Blueprint standards validation entrypoint.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: standards
standards:
	$(PYTHON) scripts/validate_standards_index.py

# Target: standards-check
# Purpose: Run the standards validation target through the stable check alias.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: standards-check
standards-check: standards

# Target: module-standards-template
# Purpose: Render or validate the standard module Makefile/standards template surface.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: module-standards-template
module-standards-template:
	$(PYTHON) scripts/validate_module_standards_template.py

# Target: instruction-intake
# Purpose: Validate Blueprint instruction-intake sources and contracts.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: instruction-intake
instruction-intake:
	$(PYTHON) scripts/validate_instruction_intake.py

# Target: completion-packet-template
# Purpose: Validate the canonical completion-packet template surface.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: completion-packet-template
completion-packet-template:
	$(PYTHON) scripts/validate_completion_packet_template.py


# Target: coordination-check
# Purpose: Validate Blueprint coordination metadata without changing it.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: COORDINATION — focused coordination protocol surface.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: coordination-check
coordination-check:
	$(PYTHON) scripts/check_coordination_metadata.py --module-root .

# Target: coordination-fix
# Purpose: Apply supported repairs to Blueprint coordination metadata.
# Safety: BLUEPRINT MUTATION — writes the documented Blueprint-owned coordination/policy state only.
# Inputs: None.
# Scope: COORDINATION — focused coordination protocol surface.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: coordination-fix
coordination-fix:
	$(PYTHON) scripts/fix_coordination_metadata.py --module-root .

# Target: module-policy-generate
# Purpose: Generate module policy documentation from canonical policy sources.
# Safety: BLUEPRINT MUTATION — writes the documented Blueprint-owned coordination/policy state only.
# Inputs: None.
# Scope: MODULE — selected MODULE.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: module-policy-generate
module-policy-generate:
	$(PYTHON) scripts/generate_module_policy_docs.py

# Target: module-policy-check
# Purpose: Validate module policy artifacts and consistency.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: MODULE — selected MODULE.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: module-policy-check
module-policy-check:
	$(PYTHON) scripts/generate_module_policy_docs.py --check

# Target: module-governance-audit
# Purpose: Run the module governance audit for the selected module.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: MODULE — selected MODULE.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: module-governance-audit
module-governance-audit:
	$(PYTHON) scripts/audit_module_governance.py

# Target: module-governance-audit-check
# Purpose: Validate the module governance audit implementation/contract.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: MODULE — selected MODULE.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: module-governance-audit-check
module-governance-audit-check:
	$(PYTHON) scripts/audit_module_governance.py --no-write


# Blueprint reporting consolidation audit

# Target: reporting-consolidation-audit
# Purpose: Audit reporting surfaces for consolidation issues.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: reporting-consolidation-audit
reporting-consolidation-audit:
	$(PYTHON) scripts/reporting/audit_consolidation.py

# Target: reporting-consolidation-audit-json
# Purpose: Run the reporting consolidation audit with JSON-oriented output.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: reporting-consolidation-audit-json
reporting-consolidation-audit-json:
	@$(PYTHON) scripts/reporting/audit_consolidation.py --json


# Target: module-workflow-list
# Purpose: List available module workflow operations.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: LOCAL/FOCUSED — only the selected status/artifact/query surface.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: module-workflow-list
module-workflow-list:
	$(PYTHON) -m scripts.coordination.modules.module_workflow_cli --root "." list

# Target: module-workflow-check
# Purpose: Validate the generic module workflow control surface.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: module-workflow-check
module-workflow-check:
	$(PYTHON) -m scripts.coordination.modules.module_workflow_cli --root "." check

# Target: module-self-audit
# Purpose: Run or initialize the self-audit workflow for the selected module.
# Safety: WORKFLOW-STATE MUTATION — may create/update durable self-audit state for the selected module; no Git/release authority.
# Inputs: MODULE (optional/defaulted).
# Scope: MODULE — selected MODULE.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: module-self-audit
module-self-audit:
	$(PYTHON) -m scripts.coordination.modules.module_workflow_cli --root "." --module "$(MODULE)" self-audit

# Target: module-self-audit-resume
# Purpose: Resume the selected module self-audit from durable workflow state.
# Safety: WORKFLOW-STATE MUTATION — resumes and updates durable self-audit state for the selected module; no Git/release authority.
# Inputs: MODULE (optional/defaulted).
# Scope: MODULE — selected MODULE.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: module-self-audit-resume
module-self-audit-resume:
	$(PYTHON) -m scripts.coordination.modules.module_workflow_cli --root "." --module "$(MODULE)" self-audit-resume

# Target: module-self-status
# Purpose: Render concise durable self-workflow status for the selected module.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: MODULE (optional/defaulted).
# Scope: MODULE — selected MODULE.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: module-self-status
module-self-status:
	$(PYTHON) -m scripts.coordination.modules.module_workflow_cli --root "." --module "$(MODULE)" self-status

# Target: module-self-report-full
# Purpose: Render the full durable self-workflow report for the selected module.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: MODULE (optional/defaulted).
# Scope: MODULE — selected MODULE.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: module-self-report-full
module-self-report-full:
	$(PYTHON) -m scripts.coordination.modules.module_workflow_cli --root "." --module "$(MODULE)" self-report-full

# Target: modules-self-status
# Purpose: Render self-workflow status across the configured module portfolio.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: PORTFOLIO — configured multi-module/project view.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: modules-self-status
modules-self-status:
	$(PYTHON) -m scripts.coordination.modules.module_workflow_cli --root "." modules-status

# Target: blueprint-self-audit
# Purpose: Run the Blueprint repository self-audit through the generic module workflow.
# Safety: WORKFLOW-STATE MUTATION — delegates to module-self-audit for the Blueprint repository only.
# Inputs: None.
# Scope: PROJECT — Blueprint repository.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: blueprint-self-audit
blueprint-self-audit:
	$(MAKE) module-self-audit MODULE=forprint_system_blueprint

# Target: blueprint-self-audit-resume
# Purpose: Resume the Blueprint self-audit from durable workflow state.
# Safety: WORKFLOW-STATE MUTATION — resumes the Blueprint durable self-audit only.
# Inputs: None.
# Scope: PROJECT — Blueprint repository.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: blueprint-self-audit-resume
blueprint-self-audit-resume:
	$(MAKE) module-self-audit-resume MODULE=forprint_system_blueprint

# Target: blueprint-self-status
# Purpose: Render concise Blueprint self-workflow status.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: PROJECT — Blueprint repository.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: blueprint-self-status
blueprint-self-status:
	$(MAKE) module-self-status MODULE=forprint_system_blueprint

# Target: blueprint-self-report-full
# Purpose: Render the full Blueprint self-workflow report.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: PROJECT — Blueprint repository.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: blueprint-self-report-full
blueprint-self-report-full:
	$(MAKE) module-self-report-full MODULE=forprint_system_blueprint

# Target: blueprint-governance-status
# Purpose: Render Blueprint governance status in text, YAML, or JSON format.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: GOVERNANCE_STATUS_FORMAT (optional/defaulted).
# Scope: PROJECT — Blueprint repository.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: blueprint-governance-status
blueprint-governance-status:
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_blueprint_governance_status.py --repo-root "." --format "$(GOVERNANCE_STATUS_FORMAT)"


# These targets may write only declared generated reports/tmp evidence.
# They are invoked by the repository gate and must never mutate source records.


# =============================================================================
# 11 Repository knowledge / inventory / reconciliation
# =============================================================================
# Block scope: Repository-knowledge health, semantic coverage, and acceptance evidence.

# Target: check-module-registry-consistency
# Purpose: Validate module-registry consistency against current repository knowledge.
# Safety: READ-ONLY WITH REPORT/TMP OUTPUT — may refresh diagnostic/generated evidence, but does not change execution authority.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: check-module-registry-consistency
check-module-registry-consistency:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_module_registry_resolution.py --manifest coordination/repository_knowledge/registries/module_registry_resolution_v0_1.yaml --repo-root . --output reports/module_registry_consistency_report.yaml

# Target: roadmap-status
# Purpose: Render current roadmap status without mutation.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: MODULE (optional/defaulted).
# Scope: MODULE/ROADMAP — selected MODULE/ROADMAP or configured summary set.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: roadmap-status
roadmap-status:
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_blueprint_self_coordination_status.py --module "$(MODULE)" --view roadmap
	$(PYTHON) scripts/coordination/roadmap_execution_reconciliation.py --root . status

# Target: prompts-status
# Purpose: Render current prompt-system status without mutation.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: MODULE (optional/defaulted).
# Scope: LOCAL/FOCUSED — only the selected status/artifact/query surface.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: prompts-status
prompts-status:
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_blueprint_self_coordination_status.py --module "$(MODULE)" --view prompts

# Target: check-self-coordination-consistency
# Purpose: Validate self-coordination artifacts for internal consistency.
# Safety: READ-ONLY WITH REPORT/TMP OUTPUT — may refresh diagnostic/generated evidence, but does not change execution authority.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: check-self-coordination-consistency
check-self-coordination-consistency:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_blueprint_self_coordination.py --repo-root . --roadmap coordination/self_coordination/roadmap.yaml --queue coordination/self_coordination/prompt_queue/index.yaml --completion coordination/self_coordination/completion_packets/2026-07-30__forprint_system_blueprint__self_coordination_consistency_ci_gate_v0_1.yaml --module-plan coordination/self_coordination/module_plans/forprint_library.yaml --module-plan coordination/self_coordination/module_plans/logistics_service.yaml --module-plan coordination/self_coordination/module_plans/telegram_bot.yaml --output reports/blueprint_self_coordination_consistency_report.yaml

# Target: inventory-status
# Purpose: Render current repository capability-inventory status.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: MODULE (optional/defaulted).
# Scope: PROJECT KNOWLEDGE — repository-knowledge/inventory surfaces.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: inventory-status
inventory-status:
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_blueprint_inventory_status.py --module "$(MODULE)"

# Target: check-repository-knowledge-snapshots
# Purpose: Validate repository-knowledge snapshot artifacts.
# Safety: READ-ONLY WITH REPORT/TMP OUTPUT — may refresh diagnostic/generated evidence, but does not change execution authority.
# Inputs: None.
# Scope: PROJECT KNOWLEDGE — repository-knowledge/inventory surfaces.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: check-repository-knowledge-snapshots
check-repository-knowledge-snapshots:
	@mkdir -p reports tmp/repository_knowledge_snapshot_comparisons
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_repository_knowledge_snapshot_comparisons.py --manifest coordination/repository_knowledge/snapshot_comparison_gate_v0_1.yaml --repo-root . --work-dir tmp/repository_knowledge_snapshot_comparisons --output reports/repository_knowledge_snapshot_comparison_report.yaml

# Target: check-inventory-status-consistency
# Purpose: Validate consistency between repository inventory and reported status.
# Safety: READ-ONLY WITH REPORT/TMP OUTPUT — may refresh diagnostic/generated evidence, but does not change execution authority.
# Inputs: None.
# Scope: PROJECT KNOWLEDGE — repository-knowledge/inventory surfaces.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: check-inventory-status-consistency
check-inventory-status-consistency:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_blueprint_inventory_status_consistency.py --wave coordination/internal_work/blueprint/inventory_refresh/2026-07-29__blueprint__semantic_inventory_wave_2_v0_1.yaml --dashboard coordination/internal_work/blueprint/inventory_refresh/2026-07-29__blueprint__inventory_coverage_drift_dashboard_v0_1.yaml --maintenance coordination/repository_knowledge/inventory_maintenance_v0_1.yaml --roadmap coordination/self_coordination/roadmap.yaml --renderer scripts/coordination/render_blueprint_inventory_status.py --module forprint_system_blueprint --output reports/blueprint_inventory_status_consistency_report.yaml

# Target: check-repository-knowledge-freshness
# Purpose: Validate freshness of repository-knowledge artifacts.
# Safety: READ-ONLY WITH REPORT/TMP OUTPUT — may refresh diagnostic/generated evidence, but does not change execution authority.
# Inputs: None.
# Scope: PROJECT KNOWLEDGE — repository-knowledge/inventory surfaces.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: check-repository-knowledge-freshness
check-repository-knowledge-freshness:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/assess_repository_knowledge_freshness.py --manifest coordination/repository_knowledge/snapshot_comparison_gate_v0_1.yaml --repo-root . --output reports/repository_knowledge_freshness_report.yaml

# Target: repository-knowledge-freshness-status
# Purpose: Render repository-knowledge freshness status.
# Safety: READ-ONLY WITH REPORT/TMP OUTPUT — may refresh diagnostic/generated evidence, but does not change execution authority.
# Inputs: None.
# Scope: PROJECT KNOWLEDGE — repository-knowledge/inventory surfaces.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: repository-knowledge-freshness-status
repository-knowledge-freshness-status:
	@mkdir -p tmp
	@$(BLUEPRINT_PYTHON) scripts/coordination/assess_repository_knowledge_freshness.py --manifest coordination/repository_knowledge/snapshot_comparison_gate_v0_1.yaml --repo-root . --output tmp/repository_knowledge_freshness_status.yaml
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_repository_knowledge_freshness_status.py --report tmp/repository_knowledge_freshness_status.yaml

# Target: check-rci-semantic-enrichment
# Purpose: Validate semantic enrichment of the repository capability inventory.
# Safety: READ-ONLY WITH REPORT/TMP OUTPUT — may refresh diagnostic/generated evidence, but does not change execution authority.
# Inputs: None.
# Scope: PROJECT KNOWLEDGE — repository-knowledge/inventory surfaces.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: check-rci-semantic-enrichment
check-rci-semantic-enrichment:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_rci_semantic_enrichment.py --source coordination/repository_knowledge/inventory/2026-07-29__forprint_system_blueprint__repository_capability_inventory_v0_3.yaml --candidate coordination/repository_knowledge/inventory/2026-07-30__forprint_system_blueprint__repository_capability_inventory_v0_4.yaml --enrichment-record coordination/internal_work/blueprint/inventory_refresh/2026-07-30__blueprint__rci_semantic_enrichment_v0_1.yaml --repo-root . --expected-source-sha256 3b9278a9bea091ae83f045a2fb5028c97f5fbd00a69b2be173a92a6d9d58d9aa --output reports/rci_semantic_enrichment_validation_report.yaml

# Target: check-redm-dependency-enrichment
# Purpose: Validate dependency enrichment of the repository execution dependency map.
# Safety: READ-ONLY WITH REPORT/TMP OUTPUT — may refresh diagnostic/generated evidence, but does not change execution authority.
# Inputs: None.
# Scope: PROJECT KNOWLEDGE — repository-knowledge/inventory surfaces.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: check-redm-dependency-enrichment
check-redm-dependency-enrichment:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_redm_dependency_enrichment.py --source coordination/repository_knowledge/flows/2026-07-29__forprint_system_blueprint__repository_execution_dependency_map_v0_3.yaml --candidate coordination/repository_knowledge/flows/2026-07-30__forprint_system_blueprint__repository_execution_dependency_map_v0_4.yaml --capability-context coordination/repository_knowledge/inventory/2026-07-30__forprint_system_blueprint__repository_capability_inventory_v0_4.yaml --enrichment-record coordination/internal_work/blueprint/inventory_refresh/2026-07-30__blueprint__redm_dependency_enrichment_v0_1.yaml --repo-root . --expected-source-sha256 33b0224e3a3b7651412e49fc17b3a0f8192714bd009155d12877712067b8ee70 --output reports/redm_dependency_enrichment_validation_report.yaml

# Target: check-semantic-coverage-closure
# Purpose: Validate semantic coverage closure across current repository knowledge.
# Safety: READ-ONLY WITH REPORT/TMP OUTPUT — may refresh diagnostic/generated evidence, but does not change execution authority.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: check-semantic-coverage-closure
check-semantic-coverage-closure: check-rci-semantic-enrichment check-redm-dependency-enrichment check-repository-knowledge-freshness
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_semantic_coverage_closure.py --rci coordination/repository_knowledge/inventory/2026-07-30__forprint_system_blueprint__repository_capability_inventory_v0_4.yaml --redm coordination/repository_knowledge/flows/2026-07-30__forprint_system_blueprint__repository_execution_dependency_map_v0_4.yaml --rci-validation reports/rci_semantic_enrichment_validation_report.yaml --redm-validation reports/redm_dependency_enrichment_validation_report.yaml --freshness reports/repository_knowledge_freshness_report.yaml --unknowns coordination/internal_work/blueprint/inventory_refresh/2026-07-30__blueprint__semantic_inventory_unknowns_triage_v0_1.yaml --module forprint_system_blueprint --output reports/semantic_coverage_closure_report.yaml

# Target: semantic-coverage-status
# Purpose: Render semantic coverage status and outstanding gaps.
# Safety: READ-ONLY WITH REPORT/TMP OUTPUT — may refresh diagnostic/generated evidence, but does not change execution authority.
# Inputs: MODULE (optional/defaulted).
# Scope: PROJECT KNOWLEDGE — repository-knowledge/inventory surfaces.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: semantic-coverage-status
semantic-coverage-status:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_semantic_coverage_closure.py --rci coordination/repository_knowledge/inventory/2026-07-30__forprint_system_blueprint__repository_capability_inventory_v0_4.yaml --redm coordination/repository_knowledge/flows/2026-07-30__forprint_system_blueprint__repository_execution_dependency_map_v0_4.yaml --rci-validation reports/rci_semantic_enrichment_validation_report.yaml --redm-validation reports/redm_dependency_enrichment_validation_report.yaml --freshness reports/repository_knowledge_freshness_report.yaml --unknowns coordination/internal_work/blueprint/inventory_refresh/2026-07-30__blueprint__semantic_inventory_unknowns_triage_v0_1.yaml --module "$(MODULE)" --output reports/semantic_coverage_closure_report.yaml
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_semantic_coverage_closure_status.py --report reports/semantic_coverage_closure_report.yaml

# Target: check-repository-knowledge-reconciliation
# Purpose: Validate reconciliation between repository-knowledge artifacts and coordination direction.
# Safety: READ-ONLY WITH REPORT/TMP OUTPUT — may refresh diagnostic/generated evidence, but does not change execution authority.
# Inputs: None.
# Scope: PROJECT KNOWLEDGE — repository-knowledge/inventory surfaces.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: check-repository-knowledge-reconciliation
check-repository-knowledge-reconciliation: check-semantic-coverage-closure check-rci-semantic-enrichment check-redm-dependency-enrichment
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_repository_knowledge_reconciliation.py --rci coordination/repository_knowledge/inventory/2026-07-30__forprint_system_blueprint__repository_capability_inventory_v0_4.yaml --redm coordination/repository_knowledge/flows/2026-07-30__forprint_system_blueprint__repository_execution_dependency_map_v0_4.yaml --coordination-direction coordination/repository_knowledge/direction/blueprint_coordination/2026-07-29__forprint_system_blueprint__state_direction_rationale_snapshot_v0_2.yaml --portfolio-direction coordination/repository_knowledge/direction/system_portfolio/2026-07-29__forprint_system__state_direction_rationale_snapshot_v0_2.yaml --authority-policy coordination/repository_knowledge/artifact_authority_policy_v0_1.yaml --module-registry coordination/repository_knowledge/registries/module_registry_resolution_v0_1.yaml --closure-report reports/semantic_coverage_closure_report.yaml --rci-validation reports/rci_semantic_enrichment_validation_report.yaml --redm-validation reports/redm_dependency_enrichment_validation_report.yaml --module forprint_system_blueprint --output reports/repository_knowledge_reconciliation_report.yaml

# Target: repository-knowledge-reconciliation-status
# Purpose: Render repository-knowledge reconciliation status.
# Safety: READ-ONLY WITH REPORT/TMP OUTPUT — may refresh diagnostic/generated evidence, but does not change execution authority.
# Inputs: MODULE (optional/defaulted).
# Scope: PROJECT KNOWLEDGE — repository-knowledge/inventory surfaces.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: repository-knowledge-reconciliation-status
repository-knowledge-reconciliation-status:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_repository_knowledge_reconciliation.py --rci coordination/repository_knowledge/inventory/2026-07-30__forprint_system_blueprint__repository_capability_inventory_v0_4.yaml --redm coordination/repository_knowledge/flows/2026-07-30__forprint_system_blueprint__repository_execution_dependency_map_v0_4.yaml --coordination-direction coordination/repository_knowledge/direction/blueprint_coordination/2026-07-29__forprint_system_blueprint__state_direction_rationale_snapshot_v0_2.yaml --portfolio-direction coordination/repository_knowledge/direction/system_portfolio/2026-07-29__forprint_system__state_direction_rationale_snapshot_v0_2.yaml --authority-policy coordination/repository_knowledge/artifact_authority_policy_v0_1.yaml --module-registry coordination/repository_knowledge/registries/module_registry_resolution_v0_1.yaml --closure-report reports/semantic_coverage_closure_report.yaml --rci-validation reports/rci_semantic_enrichment_validation_report.yaml --redm-validation reports/redm_dependency_enrichment_validation_report.yaml --module "$(MODULE)" --output reports/repository_knowledge_reconciliation_report.yaml
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_repository_knowledge_reconciliation_status.py --report reports/repository_knowledge_reconciliation_report.yaml

# Target: check-inventory-acceptance-evidence-index
# Purpose: Validate the inventory acceptance evidence index and prerequisite semantic evidence.
# Safety: READ-ONLY WITH REPORT/TMP OUTPUT — may refresh diagnostic/generated evidence, but does not change execution authority.
# Inputs: None.
# Scope: PROJECT KNOWLEDGE — repository-knowledge/inventory surfaces.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: check-inventory-acceptance-evidence-index
check-inventory-acceptance-evidence-index: check-rci-semantic-enrichment check-redm-dependency-enrichment check-semantic-coverage-closure check-repository-knowledge-reconciliation
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_inventory_acceptance_evidence_index.py --index coordination/internal_work/blueprint/inventory_refresh/2026-07-30__blueprint__inventory_acceptance_evidence_index_v0_1.yaml --repo-root . --module forprint_system_blueprint --output reports/inventory_acceptance_evidence_index_validation_report.yaml

# Target: inventory-acceptance-evidence-status
# Purpose: Render inventory acceptance evidence status.
# Safety: READ-ONLY WITH REPORT/TMP OUTPUT — may refresh diagnostic/generated evidence, but does not change execution authority.
# Inputs: MODULE (optional/defaulted).
# Scope: PROJECT KNOWLEDGE — repository-knowledge/inventory surfaces.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: inventory-acceptance-evidence-status
inventory-acceptance-evidence-status:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_inventory_acceptance_evidence_index.py --index coordination/internal_work/blueprint/inventory_refresh/2026-07-30__blueprint__inventory_acceptance_evidence_index_v0_1.yaml --repo-root . --module "$(MODULE)" --output reports/inventory_acceptance_evidence_index_validation_report.yaml
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_inventory_acceptance_evidence_status.py --index coordination/internal_work/blueprint/inventory_refresh/2026-07-30__blueprint__inventory_acceptance_evidence_index_v0_1.yaml --report reports/inventory_acceptance_evidence_index_validation_report.yaml

# Target: check-inventory-acceptance-dry-run
# Purpose: Run the read-only inventory acceptance dry run with prerequisite evidence checks.
# Safety: READ-ONLY WITH REPORT/TMP OUTPUT — may refresh diagnostic/generated evidence, but does not change execution authority.
# Inputs: None.
# Scope: PROJECT KNOWLEDGE — repository-knowledge/inventory surfaces.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: check-inventory-acceptance-dry-run
check-inventory-acceptance-dry-run: check-inventory-acceptance-evidence-index check-semantic-coverage-closure check-repository-knowledge-reconciliation
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/run_inventory_acceptance_dry_run.py --index coordination/internal_work/blueprint/inventory_refresh/2026-07-30__blueprint__inventory_acceptance_evidence_index_v0_1.yaml --index-validation reports/inventory_acceptance_evidence_index_validation_report.yaml --rci coordination/repository_knowledge/inventory/2026-07-30__forprint_system_blueprint__repository_capability_inventory_v0_4.yaml --redm coordination/repository_knowledge/flows/2026-07-30__forprint_system_blueprint__repository_execution_dependency_map_v0_4.yaml --closure reports/semantic_coverage_closure_report.yaml --reconciliation reports/repository_knowledge_reconciliation_report.yaml --authority-policy coordination/repository_knowledge/artifact_authority_policy_v0_1.yaml --plan coordination/internal_work/blueprint/inventory_refresh/2026-07-29__blueprint__inventory_refresh_plan_v0_1.yaml --roadmap coordination/self_coordination/roadmap.yaml --queue coordination/self_coordination/prompt_queue/index.yaml --module forprint_system_blueprint --output reports/inventory_acceptance_dry_run_report.yaml

# Target: inventory-acceptance-dry-run-status
# Purpose: Render the current inventory acceptance dry-run status.
# Safety: READ-ONLY WITH REPORT/TMP OUTPUT — may refresh diagnostic/generated evidence, but does not change execution authority.
# Inputs: MODULE (optional/defaulted).
# Scope: PROJECT KNOWLEDGE — repository-knowledge/inventory surfaces.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: inventory-acceptance-dry-run-status
inventory-acceptance-dry-run-status:
	@mkdir -p reports
	@$(BLUEPRINT_PYTHON) scripts/coordination/run_inventory_acceptance_dry_run.py --index coordination/internal_work/blueprint/inventory_refresh/2026-07-30__blueprint__inventory_acceptance_evidence_index_v0_1.yaml --index-validation reports/inventory_acceptance_evidence_index_validation_report.yaml --rci coordination/repository_knowledge/inventory/2026-07-30__forprint_system_blueprint__repository_capability_inventory_v0_4.yaml --redm coordination/repository_knowledge/flows/2026-07-30__forprint_system_blueprint__repository_execution_dependency_map_v0_4.yaml --closure reports/semantic_coverage_closure_report.yaml --reconciliation reports/repository_knowledge_reconciliation_report.yaml --authority-policy coordination/repository_knowledge/artifact_authority_policy_v0_1.yaml --plan coordination/internal_work/blueprint/inventory_refresh/2026-07-29__blueprint__inventory_refresh_plan_v0_1.yaml --roadmap coordination/self_coordination/roadmap.yaml --queue coordination/self_coordination/prompt_queue/index.yaml --module "$(MODULE)" --output reports/inventory_acceptance_dry_run_report.yaml
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_inventory_acceptance_dry_run_status.py --report reports/inventory_acceptance_dry_run_report.yaml


COORDINATION_PULSE_FORMAT ?= text
PROMPT_CONTRACT_V0_4 ?= coordination/prompt_contracts/forprint_system_blueprint/blueprint_v0_4_immutable_prompt_contract_v0_1/blueprint_v0_4_immutable_prompt_contract_v0_1__contract_v0_1.yaml
COMPLETION_PACKET_V0_4 ?= coordination/templates/module_completion_packet_v0_4.example.yaml
COMPLETION_OUTBOX_V0_4 ?= coordination/templates/module_completion_outbox_v0_4.example.yaml
COORDINATION_SOURCE_REGISTRY_V0_4 ?= coordination/registry/coordination_source_registry_v0_1.yaml


# =============================================================================
# 12 v0.4 closed-loop coordination primitives
# =============================================================================
# Block scope: Focused v0.4 transaction, completion, and tracking-event primitives.

# Target: coordination-pulse
# Purpose: Render the current v0.4 coordination pulse in the selected output format.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: COORDINATION_PULSE_FORMAT (optional/defaulted).
# Scope: COORDINATION — focused coordination protocol surface.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: coordination-pulse
coordination-pulse:
	@$(BLUEPRINT_PYTHON) scripts/coordination/coordination_pulse.py --root . --output-format "$(COORDINATION_PULSE_FORMAT)"

# Target: prompt-contract-v0-4-validate
# Purpose: Validate a v0.4 immutable prompt contract.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: PROMPT_CONTRACT_V0_4 (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: prompt-contract-v0-4-validate
prompt-contract-v0-4-validate:
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_prompt_contract_v0_4.py --root . --contract "$(PROMPT_CONTRACT_V0_4)"

# Target: completion-packet-v0-4-validate
# Purpose: Validate a v0.4 completion packet in template-compatible mode.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: COMPLETION_PACKET_V0_4 (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: completion-packet-v0-4-validate
completion-packet-v0-4-validate:
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_completion_packet_v0_4.py --root . --packet "$(COMPLETION_PACKET_V0_4)" --template-mode

# Target: completion-outbox-v0-4-validate
# Purpose: Validate a v0.4 completion outbox artifact.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: COMPLETION_OUTBOX_V0_4 (optional/defaulted), COORDINATION_SOURCE_REGISTRY_V0_4 (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: completion-outbox-v0-4-validate
completion-outbox-v0-4-validate:
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_completion_outbox_v0_4.py "$(COMPLETION_OUTBOX_V0_4)" --root . --registry "$(COORDINATION_SOURCE_REGISTRY_V0_4)" --template

# Target: completion-discovery-intake-v0-4
# Purpose: Discover and ingest v0.4 completion evidence according to the coordination contract.
# Safety: BLUEPRINT COORDINATION MUTATION — may write only the governed v0.4 intake/discovery state defined by its script.
# Inputs: None.
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: completion-discovery-intake-v0-4
completion-discovery-intake-v0-4:
	@$(BLUEPRINT_PYTHON) scripts/coordination/completion_discovery_and_intake_v0_4.py --root .

REVIEW_TRANSACTION_REQUEST ?=
REVIEW_TRANSACTION_APPLY ?= 0
REVIEW_OPERATOR_CONFIRMATION ?=
REVIEW_TRANSACTION_FORMAT ?= text

# Target: review-roadmap-queue-transaction-v0-4
# Purpose: Show live transaction status or evaluate/apply a governed roadmap/queue transaction request.
# Safety: CONDITIONAL MUTATION — with no request renders live status; with a request evaluates it; mutation requires REVIEW_TRANSACTION_APPLY=1 plus explicit operator confirmation.
# Inputs: REVIEW_TRANSACTION_REQUEST (required), REVIEW_TRANSACTION_FORMAT (optional/defaulted), REVIEW_TRANSACTION_APPLY (optional/defaulted), REVIEW_OPERATOR_CONFIRMATION (required).
# Scope: COORDINATION — focused coordination protocol surface.
# Result: Preview/evaluation is reported; when explicit apply inputs authorize mutation, only the target's documented state is written.
.PHONY: review-roadmap-queue-transaction-v0-4
review-roadmap-queue-transaction-v0-4:
	@set -eu; \
	if [ -z "$(REVIEW_TRANSACTION_REQUEST)" ]; then \
		$(BLUEPRINT_PYTHON) scripts/coordination/review_roadmap_queue_transaction_v0_4.py \
			--root . --live-status --output-format "$(REVIEW_TRANSACTION_FORMAT)"; \
	else \
		set -- \
			--root . \
			--request "$(REVIEW_TRANSACTION_REQUEST)" \
			--output-format "$(REVIEW_TRANSACTION_FORMAT)"; \
		if [ "$(REVIEW_TRANSACTION_APPLY)" = "1" ]; then \
			test -n "$(REVIEW_OPERATOR_CONFIRMATION)" || { \
				echo "ERROR: REVIEW_OPERATOR_CONFIRMATION is required when REVIEW_TRANSACTION_APPLY=1"; \
				exit 2; \
			}; \
			set -- "$$@" --apply \
				--operator-confirmation "$(REVIEW_OPERATOR_CONFIRMATION)"; \
		elif [ "$(REVIEW_TRANSACTION_APPLY)" != "0" ]; then \
			echo "ERROR: REVIEW_TRANSACTION_APPLY must be 0 or 1"; \
			exit 2; \
		fi; \
		$(BLUEPRINT_PYTHON) scripts/coordination/review_roadmap_queue_transaction_v0_4.py "$$@"; \
	fi

ACCEPT_AND_ADVANCE_REQUEST ?=
ACCEPT_AND_ADVANCE_APPLY ?= 0
ACCEPT_AND_ADVANCE_CONFIRMATION ?=
ACCEPT_AND_ADVANCE_FORMAT ?= text

# Target: accept-and-advance
# Purpose: Evaluate or apply an explicit governed accept-and-advance request.
# Safety: CONDITIONAL MUTATION — evaluates by default; mutation requires ACCEPT_AND_ADVANCE_APPLY=1 plus explicit operator confirmation.
# Inputs: ACCEPT_AND_ADVANCE_REQUEST (required), ACCEPT_AND_ADVANCE_APPLY (optional/defaulted), ACCEPT_AND_ADVANCE_FORMAT (optional/defaulted), ACCEPT_AND_ADVANCE_CONFIRMATION (required).
# Scope: COORDINATION — focused coordination protocol surface.
# Result: Preview/evaluation is reported; when explicit apply inputs authorize mutation, only the target's documented state is written.
.PHONY: accept-and-advance
accept-and-advance:
	@set -eu; \
	if [ -z "$(ACCEPT_AND_ADVANCE_REQUEST)" ]; then \
		echo "ERROR: ACCEPT_AND_ADVANCE_REQUEST=tmp/<request>.yaml is required"; \
		exit 2; \
	fi; \
	case "$(ACCEPT_AND_ADVANCE_APPLY)" in \
		0|1) ;; \
		*) echo "ERROR: ACCEPT_AND_ADVANCE_APPLY must be 0 or 1"; exit 2 ;; \
	esac; \
	set -- --root . --request "$(ACCEPT_AND_ADVANCE_REQUEST)" --output-format "$(ACCEPT_AND_ADVANCE_FORMAT)"; \
	if [ "$(ACCEPT_AND_ADVANCE_APPLY)" = "1" ]; then \
		test -n "$(ACCEPT_AND_ADVANCE_CONFIRMATION)" || { \
			echo "ERROR: ACCEPT_AND_ADVANCE_CONFIRMATION is required when APPLY=1"; \
			exit 2; \
		}; \
		set -- "$$@" --apply --operator-confirmation "$(ACCEPT_AND_ADVANCE_CONFIRMATION)"; \
	fi; \
	$(BLUEPRINT_PYTHON) scripts/coordination/accept_and_advance_v0_1.py "$$@"

# Target: test-v0-4-1-h5
# Purpose: Run focused tests for the v0.4.1 H5 accept-and-advance flow.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: COORDINATION — focused coordination protocol surface.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: test-v0-4-1-h5
test-v0-4-1-h5:
	@$(BLUEPRINT_PYTHON) -m pytest -q tests/validation/test_v0_4_1_accept_and_advance.py

# Target: next-prompt-selection-activation-v0-4
# Purpose: Render live next-prompt selection/activation status for the v0.4 coordination flow.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: COORDINATION — focused coordination protocol surface.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: next-prompt-selection-activation-v0-4
next-prompt-selection-activation-v0-4:
	@$(BLUEPRINT_PYTHON) scripts/coordination/next_prompt_selection_activation_v0_4.py --root . --live-status


TRACKING_EVENTS_REFERENCE_BUNDLE ?= tmp/step27_tracking_events_reference_sources.txt
TRACKING_EVENTS_SOURCE_PROMPT ?= coordination/prompt_contracts/logistics_service/logistics_service_tracking_events_v0_1/source_prompt_snapshot.md
TRACKING_EVENTS_V0_3_CONTRACT ?= coordination/prompt_contracts/logistics_service/logistics_service_tracking_events_v0_1.yaml
PROMPT_CONTRACT_V0_4_STANDARD ?= coordination/standards/governance/module_prompt_contract_v0_4.yaml
PROMPT_CONTRACT_V0_4_EXAMPLE ?= coordination/templates/module_prompt_contract_v0_4.example.yaml
PROMPT_CONTRACT_V0_4_SELF_REFERENCE ?= coordination/prompt_contracts/forprint_system_blueprint/blueprint_v0_4_immutable_prompt_contract_v0_1/blueprint_v0_4_immutable_prompt_contract_v0_1__contract_v0_1.yaml

# Target: tracking-events-reference-v0-4-preflight
# Purpose: Build a temporary read-only-source bundle for Tracking Events v0.4 reference review.
# Safety: TMP-ONLY WRITE — reads governed sources and writes only the temporary reference review bundle.
# Inputs: PROMPT_CONTRACT_V0_4_STANDARD (optional/defaulted), PROMPT_CONTRACT_V0_4_EXAMPLE (optional/defaulted), PROMPT_CONTRACT_V0_4_SELF_REFERENCE (optional/defaulted), TRACKING_EVENTS_V0_3_CONTRACT (optional/defaulted), TRACKING_EVENTS_SOURCE_PROMPT (optional/defaulted), TRACKING_EVENTS_REFERENCE_BUNDLE (optional/defaulted).
# Scope: COORDINATION — focused coordination protocol surface.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: tracking-events-reference-v0-4-preflight
tracking-events-reference-v0-4-preflight:
	@set -eu; \
	paths="$(PROMPT_CONTRACT_V0_4_STANDARD) $(PROMPT_CONTRACT_V0_4_EXAMPLE) $(PROMPT_CONTRACT_V0_4_SELF_REFERENCE) $(TRACKING_EVENTS_V0_3_CONTRACT) $(TRACKING_EVENTS_SOURCE_PROMPT) tests/validation/test_v0_4_immutable_prompt_contract.py"; \
	for path in $$paths; do \
		test -f "$$path" || { echo "ERROR: missing required source: $$path"; exit 1; }; \
	done; \
	mkdir -p "$$(dirname "$(TRACKING_EVENTS_REFERENCE_BUNDLE)")"; \
	{ \
		echo "ForPrint STEP27 Tracking Events v0.4 reference source bundle"; \
		echo "mode: read-only-source / tmp-output"; \
		echo "HEAD: $$(git rev-parse HEAD)"; \
		echo "BRANCH: $$(git branch --show-current)"; \
		echo; \
		for path in $$paths; do \
			echo "===== FILE: $$path ====="; \
			echo "SHA256: $$(sha256sum "$$path" | awk '{print $$1}')"; \
			cat "$$path"; \
			echo; \
			echo "===== END FILE: $$path ====="; \
			echo; \
		done; \
	} > "$(TRACKING_EVENTS_REFERENCE_BUNDLE)"; \
	echo "BUNDLE: $(TRACKING_EVENTS_REFERENCE_BUNDLE)"; \
	echo "BUNDLE_SHA256: $$(sha256sum "$(TRACKING_EVENTS_REFERENCE_BUNDLE)" | awk '{print $$1}')"; \
	echo "module_repository_writes: false"; \
	echo "operator_decision_created: false"; \
	echo "global_v0_4_promotion_performed: false"; \
	echo "RESULT: TRACKING_EVENTS_V0_4_REFERENCE_PREFLIGHT_BUNDLE_READY"


TRACKING_EVENTS_V0_4_CONTRACT ?= coordination/prompt_contracts/logistics_service/logistics_service_tracking_events_v0_1/logistics_service_tracking_events_v0_1__contract_v0_4_reference_v0_2.yaml

# Target: tracking-events-reference-v0-4-build
# Purpose: Build the Blueprint-owned Tracking Events v0.4 reference contract and related artifacts.
# Safety: BLUEPRINT MUTATION — writes only Blueprint-owned immutable reference contract/snapshot/findings surfaces; no module writes or operator decision.
# Inputs: None.
# Scope: COORDINATION — focused coordination protocol surface.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: tracking-events-reference-v0-4-build
tracking-events-reference-v0-4-build:
	@$(BLUEPRINT_PYTHON) scripts/coordination/build_tracking_events_reference_v0_4.py --root .

# Target: tracking-events-reference-v0-4-validate
# Purpose: Validate the immutable Tracking Events v0.4 reference contract.
# Safety: READ-ONLY — validates the reference contract only; no Packet/Outbox creation, lifecycle decision, promotion, commit, or push.
# Inputs: TRACKING_EVENTS_V0_4_CONTRACT (optional/defaulted).
# Scope: COORDINATION — focused coordination protocol surface.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: tracking-events-reference-v0-4-validate
tracking-events-reference-v0-4-validate:
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_prompt_contract_v0_4.py --root . --contract "$(TRACKING_EVENTS_V0_4_CONTRACT)"


# Target: tracking-events-reference-v0-4-revise-after-pre-review
# Purpose: Record pre-review findings and rebuild the Tracking Events v0.4 reference candidate.
# Safety: BLUEPRINT MUTATION — records bounded pre-review findings and rebuilds the Blueprint-owned reference candidate only.
# Inputs: None.
# Scope: COORDINATION — focused coordination protocol surface.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: tracking-events-reference-v0-4-revise-after-pre-review
tracking-events-reference-v0-4-revise-after-pre-review:
	@$(BLUEPRINT_PYTHON) scripts/coordination/record_tracking_events_reference_v0_4_pre_review.py --root .
	@$(BLUEPRINT_PYTHON) scripts/coordination/build_tracking_events_reference_v0_4.py --root .


# Target: tracking-events-reference-v0-4-semantic-review-prep
# Purpose: Prepare the Tracking Events v0.4 semantic-review package.
# Safety: GENERATED REVIEW ARTIFACT WRITE — prepares semantic-review evidence only; no acceptance/promotion decision.
# Inputs: None.
# Scope: COORDINATION — focused coordination protocol surface.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: tracking-events-reference-v0-4-semantic-review-prep
tracking-events-reference-v0-4-semantic-review-prep:
	@$(BLUEPRINT_PYTHON) scripts/coordination/prepare_tracking_events_reference_v0_4_semantic_review.py --root .


TRACKING_EVENTS_SEMANTIC_DECISION ?=

# Target: tracking-events-reference-v0-4-semantic-decision
# Purpose: Record the explicit operator semantic-fidelity decision for Tracking Events v0.4.
# Safety: BLUEPRINT DECISION MUTATION — records only the explicit semantic-fidelity operator decision; does not accept completion or advance roadmap.
# Inputs: TRACKING_EVENTS_SEMANTIC_DECISION (required).
# Scope: COORDINATION — focused coordination protocol surface.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: tracking-events-reference-v0-4-semantic-decision
tracking-events-reference-v0-4-semantic-decision:
	@test -n "$(TRACKING_EVENTS_SEMANTIC_DECISION)" || { echo "ERROR: TRACKING_EVENTS_SEMANTIC_DECISION is required"; exit 1; }
	@$(BLUEPRINT_PYTHON) scripts/coordination/record_tracking_events_reference_v0_4_semantic_decision.py \
		--root . \
		--decision "$(TRACKING_EVENTS_SEMANTIC_DECISION)"


# ---------------------------------------------------------------------------
# H3 v0.4.1 module-owned prompt execution event observability
# ---------------------------------------------------------------------------
PROMPT_EXECUTION_EVENT_V0_1 ?= coordination/templates/module_prompt_execution_event_v0_1.example.yaml
PROMPT_EXECUTION_EVENT_MODULE_ROOT ?= .
PROMPT_EXECUTION_EVENT_REGISTRY ?= coordination/registry/coordination_source_registry_v0_1.yaml


# =============================================================================
# 13 Prompt execution observability / coordination health / preflight
# =============================================================================
# Block scope: Prompt execution events, coordination health, and execution readiness.

# Target: prompt-execution-event-v0-1-template-validate
# Purpose: Validate the prompt-execution event v0.1 template.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: PROMPT_EXECUTION_EVENT_REGISTRY (optional/defaulted), PROMPT_EXECUTION_EVENT_V0_1 (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: prompt-execution-event-v0-1-template-validate
prompt-execution-event-v0-1-template-validate:
	@$(BLUEPRINT_PYTHON) scripts/coordination/prompt_execution_events_v0_1.py validate --root . --registry "$(PROMPT_EXECUTION_EVENT_REGISTRY)" --event "$(PROMPT_EXECUTION_EVENT_V0_1)" --template

# Target: prompt-execution-event-v0-1-validate
# Purpose: Validate the supplied prompt-execution event against the registry.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: EVENT (required), PROMPT_EXECUTION_EVENT_REGISTRY (optional/defaulted), PROMPT_EXECUTION_EVENT_MODULE_ROOT (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: prompt-execution-event-v0-1-validate
prompt-execution-event-v0-1-validate:
	@if [ -z "$(EVENT)" ]; then echo "FAILED: provide EVENT=<module-relative event path>"; exit 2; fi
	@$(BLUEPRINT_PYTHON) scripts/coordination/prompt_execution_events_v0_1.py validate --root . --registry "$(PROMPT_EXECUTION_EVENT_REGISTRY)" --module-root "$(PROMPT_EXECUTION_EVENT_MODULE_ROOT)" --event "$(EVENT)"

# Target: prompt-execution-discovery-v0-1
# Purpose: Discover prompt-execution events, optionally scoped to one module.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: PROMPT_EXECUTION_EVENT_REGISTRY (optional/defaulted), MODULE (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: prompt-execution-discovery-v0-1
prompt-execution-discovery-v0-1:
	@$(BLUEPRINT_PYTHON) scripts/coordination/prompt_execution_events_v0_1.py discover --root . --registry "$(PROMPT_EXECUTION_EVENT_REGISTRY)" $(if $(MODULE),--module "$(MODULE)",)

# Target: prompt-execution-status
# Purpose: Render prompt-execution event status for the selected module.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: MODULE (required), PROMPT_EXECUTION_EVENT_REGISTRY (optional/defaulted).
# Scope: MODULE/QUEUE — selected module, prompt, packet, or queue record.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: prompt-execution-status
prompt-execution-status:
	@if [ -z "$(MODULE)" ]; then echo "FAILED: provide MODULE=<canonical module id>"; exit 2; fi
	@$(BLUEPRINT_PYTHON) scripts/coordination/prompt_execution_events_v0_1.py discover --root . --registry "$(PROMPT_EXECUTION_EVENT_REGISTRY)" --module "$(MODULE)"

# Target: test-v0-4-1-h3
# Purpose: Run focused tests for v0.4.1 H3 prompt-execution observability.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: PROMPT_EXECUTION_EVENT_V0_1 (optional/defaulted).
# Scope: COORDINATION — focused coordination protocol surface.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: test-v0-4-1-h3
test-v0-4-1-h3:
	@$(BLUEPRINT_PYTHON) scripts/coordination/prompt_execution_events_v0_1.py validate --root . --event "$(PROMPT_EXECUTION_EVENT_V0_1)" --template
	@$(BLUEPRINT_PYTHON) -m pytest -q tests/validation/test_v0_4_1_prompt_execution_events.py
	@$(BLUEPRINT_PYTHON) scripts/coordination/coordination_pulse.py --root . --output-format yaml >/dev/null

# Target: check-prompt-execution-observability
# Purpose: Validate prompt-execution observability contracts and evidence.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: check-prompt-execution-observability
check-prompt-execution-observability:
	@$(BLUEPRINT_PYTHON) scripts/coordination/coordination_pulse.py --root . --output-format yaml >/dev/null


# H4 v0.4.1 coordination freshness / prompt notification contract
# Target: test-v0-4-1-h4
# Purpose: Run focused tests for v0.4.1 H4 module coordination synchronization.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: COORDINATION — focused coordination protocol surface.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: test-v0-4-1-h4
test-v0-4-1-h4:
	@$(BLUEPRINT_PYTHON) -m pytest -q tests/validation/test_v0_4_1_module_coordination_sync.py

# H7 Logistics pilot coordination health (read-only)
COORDINATION_HEALTH_MODULE ?= logistics_service

# Target: coordination-health
# Purpose: Render coordination health for the selected module.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: COORDINATION_HEALTH_MODULE (optional/defaulted).
# Scope: COORDINATION — focused coordination protocol surface.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: coordination-health
coordination-health:
	.venv_blueprint/bin/python scripts/coordination/module_coordination_health_v0_1.py --module "$(COORDINATION_HEALTH_MODULE)"

# Target: coordination-release-status
# Purpose: Render current coordination release projection.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: COORDINATION — focused coordination protocol surface.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: coordination-release-status
coordination-release-status:
	.venv_blueprint/bin/python scripts/coordination/current_release_projection_v0_1.py --root .

# Target: legacy-compat-status
# Purpose: Render current legacy compatibility status.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: COORDINATION — focused coordination protocol surface.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: legacy-compat-status
legacy-compat-status:
	.venv_blueprint/bin/python scripts/coordination/legacy_compatibility_status_v0_1.py --root .

# ---------------------------------------------------------------------------
# B1 v0.4.1 execution baseline and drift control — P1 foundation
# ---------------------------------------------------------------------------
EXECUTION_PREFLIGHT_CONTRACT ?=
EXECUTION_PREFLIGHT_MODULE_ROOT ?=
EXECUTION_PREFLIGHT_PREVIOUS_REPORT ?=
EXECUTION_PREFLIGHT_FORMAT ?= text

# Target: execution-preflight-v0-1
# Purpose: Run the bounded execution preflight for an immutable prompt contract and module repository.
# Safety: READ-ONLY WITH OPTIONAL REPORT OUTPUT — evaluates execution readiness against immutable contract/module state; no worker launch or module mutation.
# Inputs: EXECUTION_PREFLIGHT_CONTRACT (required), EXECUTION_PREFLIGHT_MODULE_ROOT (required), EXECUTION_PREFLIGHT_FORMAT (optional/defaulted), EXECUTION_PREFLIGHT_PREVIOUS_REPORT (optional/defaulted).
# Scope: COORDINATION — focused coordination protocol surface.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: execution-preflight-v0-1
execution-preflight-v0-1:
	@if [ -z "$(EXECUTION_PREFLIGHT_CONTRACT)" ]; then echo "FAILED: provide EXECUTION_PREFLIGHT_CONTRACT=<immutable prompt contract path>"; exit 2; fi
	@if [ -z "$(EXECUTION_PREFLIGHT_MODULE_ROOT)" ]; then echo "FAILED: provide EXECUTION_PREFLIGHT_MODULE_ROOT=<module repository path>"; exit 2; fi
	@set -- \
		--root . \
		--contract "$(EXECUTION_PREFLIGHT_CONTRACT)" \
		--module-root "$(EXECUTION_PREFLIGHT_MODULE_ROOT)" \
		--output-format "$(EXECUTION_PREFLIGHT_FORMAT)"; \
	if [ -n "$(EXECUTION_PREFLIGHT_PREVIOUS_REPORT)" ]; then set -- "$$@" --previous-report "$(EXECUTION_PREFLIGHT_PREVIOUS_REPORT)"; fi; \
	$(BLUEPRINT_PYTHON) scripts/coordination/execution_preflight_v0_1.py "$$@"

# Target: test-v0-4-1-b1-p1
# Purpose: Run focused tests for v0.4.1 B1 P1 execution baseline.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: COORDINATION — focused coordination protocol surface.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: test-v0-4-1-b1-p1
test-v0-4-1-b1-p1:
	@$(BLUEPRINT_PYTHON) -m pytest -q tests/validation/test_v0_4_1_execution_baseline_and_drift_control.py tests/validation/test_v0_4_immutable_prompt_contract.py
	@$(BLUEPRINT_PYTHON) -m py_compile scripts/coordination/execution_preflight_v0_1.py scripts/coordination/validate_prompt_contract_v0_4.py

# Target: test-v0-4-1-b1-p2
# Purpose: Run focused tests for v0.4.1 B1 P2 execution drift control.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: PROMPT_EXECUTION_EVENT_V0_1 (optional/defaulted), COMPLETION_PACKET_V0_4 (optional/defaulted).
# Scope: COORDINATION — focused coordination protocol surface.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: test-v0-4-1-b1-p2
test-v0-4-1-b1-p2:
	@$(BLUEPRINT_PYTHON) -m pytest -q tests/validation/test_v0_4_1_prompt_execution_events.py tests/validation/test_v0_4_completion_packet.py tests/validation/test_v0_4_1_b1_p2_authoritative_binding.py
	@$(BLUEPRINT_PYTHON) -m py_compile scripts/coordination/prompt_execution_events_v0_1.py scripts/coordination/validate_completion_packet_v0_4.py
	@$(BLUEPRINT_PYTHON) scripts/coordination/prompt_execution_events_v0_1.py validate --root . --event "$(PROMPT_EXECUTION_EVENT_V0_1)" --template
	@$(BLUEPRINT_PYTHON) scripts/coordination/validate_completion_packet_v0_4.py --root . --packet "$(COMPLETION_PACKET_V0_4)" --template-mode

# portfolio-readiness-dashboard-v0-1-2026-09-01

# =============================================================================
# 14 Portfolio / canonical-state / surface governance
# =============================================================================
# Block scope: Portfolio readiness and current-state/freshness/surface governance.

# Target: portfolio-readiness-dashboard
# Purpose: Render the portfolio readiness dashboard.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: PORTFOLIO — configured multi-module/project view.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: portfolio-readiness-dashboard
portfolio-readiness-dashboard:
	python scripts/coordination/render_portfolio_readiness_dashboard_v0_1.py

# document-surface-normalization-v0-1-2026-09-01
# Target: surface-normalization-check
# Purpose: Validate document-surface normalization and cleanliness closure.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: surface-normalization-check
surface-normalization-check:
	.venv_blueprint/bin/python scripts/validation/validate_document_surface_registry_v0_1.py
	.venv_blueprint/bin/python scripts/validation/validate_cleanliness_normalization_closure_v0_1.py

# Target: human-intent-check
# Purpose: Validate human-intent surfaces and their consistency.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: human-intent-check
human-intent-check:
	.venv_blueprint/bin/python scripts/validation/validate_human_intent_surfaces_v0_1.py

# Target: root-roadmap-check
# Purpose: Validate root/module roadmap surfaces.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: root-roadmap-check
root-roadmap-check:
	.venv_blueprint/bin/python scripts/validation/validate_root_module_roadmap_surfaces_v0_1.py

# Target: roadmap-rebuild-seed-check
# Purpose: Validate portfolio roadmap rebuild seed surfaces.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: MODULE/ROADMAP — selected MODULE/ROADMAP or configured summary set.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: roadmap-rebuild-seed-check
roadmap-rebuild-seed-check:
	.venv_blueprint/bin/python scripts/validation/validate_portfolio_rebuild_seed_surfaces_v0_1.py

# Target: continuity-surface-check
# Purpose: Validate continuity surface contracts.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: continuity-surface-check
continuity-surface-check:
	.venv_blueprint/bin/python scripts/validation/validate_continuity_roadmap_detail_surfaces_v0_1.py

# Target: roadmap-detail-check
# Purpose: Validate roadmap-detail surfaces.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: MODULE/ROADMAP — selected MODULE/ROADMAP or configured summary set.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: roadmap-detail-check
roadmap-detail-check:
	.venv_blueprint/bin/python scripts/validation/validate_roadmap_detail_surfaces_v0_2.py

# Target: skip-inventory-check
# Purpose: Validate skip-inventory governance.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: skip-inventory-check
skip-inventory-check:
	.venv_blueprint/bin/python scripts/validation/validate_pytest_skip_inventory_v0_1.py

# Target: safe-mutation-check
# Purpose: Validate the safe mutation pipeline contract.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: safe-mutation-check
safe-mutation-check:
	.venv_blueprint/bin/python scripts/validation/validate_safe_mutation_pipeline_v0_1.py

# Target: asset-retirement-check
# Purpose: Validate asset-retirement governance.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: asset-retirement-check
asset-retirement-check:
	.venv_blueprint/bin/python scripts/validation/validate_asset_retirement_registry_v0_1.py

# Target: module-cleanliness-pack-check
# Purpose: Validate module cleanliness package behavior.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: module-cleanliness-pack-check
module-cleanliness-pack-check:
	.venv_blueprint/bin/python scripts/validation/validate_module_cleanliness_conformance_pack_v0_1.py

# Target: module-current-state-check
# Purpose: Validate module current-state evidence.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: module-current-state-check
module-current-state-check:
	.venv_blueprint/bin/python scripts/validation/validate_module_current_state_evidence_v0_1.py

# u132 canonical-state freshness/impact resolver
# Target: canonical-state-freshness-impact-check
# Purpose: Validate canonical-state freshness and impact resolution.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: canonical-state-freshness-impact-check
canonical-state-freshness-impact-check:
	@$(BLUEPRINT_PYTHON) scripts/validation/validate_blueprint_canonical_state_freshness_impact_v0_1.py

# Target: canonical-state-freshness-impact-status
# Purpose: Render canonical-state freshness/impact status.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: LOCAL/FOCUSED — only the selected status/artifact/query surface.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: canonical-state-freshness-impact-status
canonical-state-freshness-impact-status:
	@$(BLUEPRINT_PYTHON) scripts/coordination/render_blueprint_canonical_state_freshness_impact.py --repo-root . --format text

# u133 Module Memory and Logistics H10 preflight
# Target: module-memory-schema-check
# Purpose: Validate the Module Memory schema contract.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: module-memory-schema-check
module-memory-schema-check:
	@$(BLUEPRINT_PYTHON) scripts/validation/validate_module_memory_schema_v0_1.py

# Target: logistics-h10-bootstrap-preflight
# Purpose: Run the Logistics H10 bootstrap prompt preflight and emit YAML evidence.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: LOCAL/FOCUSED — target-specific repository surface.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: logistics-h10-bootstrap-preflight
logistics-h10-bootstrap-preflight:
	@$(BLUEPRINT_PYTHON) scripts/coordination/preflight_logistics_h10_bootstrap_prompt_v0_1.py --repo-root . --format yaml

# Generator / derivation foundation


# =============================================================================
# 15 Generator / dependency / execution progress
# =============================================================================
# Block scope: Derived generator inventory, dependency graph, and progress visibility.

# Target: generator-inventory
# Purpose: Build the generated inventory of Blueprint generator surfaces.
# Safety: GENERATED-ARTIFACT WRITE — writes only the documented generated/report/package surface; no release/commit/push authority.
# Inputs: None.
# Scope: DERIVATION/EXECUTION — generator, dependency, or progress-control surfaces.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: generator-inventory
generator-inventory:
	$(PYTHON) scripts/indexing/build_generator_inventory.py

# Target: generator-inventory-check
# Purpose: Validate the generator inventory against current generator surfaces.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: DERIVATION/EXECUTION — generator, dependency, or progress-control surfaces.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: generator-inventory-check
generator-inventory-check:
	$(PYTHON) scripts/indexing/build_generator_inventory.py --check

# Target: generator-contract-check
# Purpose: Validate generator contracts and registration.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: DERIVATION/EXECUTION — generator, dependency, or progress-control surfaces.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: generator-contract-check
generator-contract-check:
	$(PYTHON) scripts/indexing/validate_generator_derivation_registry.py

# Execution dependency contract / graph

# Target: execution-dependency-graph
# Purpose: Build the generated execution dependency graph.
# Safety: GENERATED-ARTIFACT WRITE — writes only the documented generated/report/package surface; no release/commit/push authority.
# Inputs: None.
# Scope: DERIVATION/EXECUTION — generator, dependency, or progress-control surfaces.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: execution-dependency-graph
execution-dependency-graph:
	$(PYTHON) scripts/indexing/build_execution_dependency_graph.py

# Target: execution-dependency-graph-check
# Purpose: Validate the generated execution dependency graph.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: DERIVATION/EXECUTION — generator, dependency, or progress-control surfaces.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: execution-dependency-graph-check
execution-dependency-graph-check:
	$(PYTHON) scripts/indexing/build_execution_dependency_graph.py --check

# Target: execution-dependency-check
# Purpose: Run the stable execution-dependency validation alias.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: DERIVATION/EXECUTION — generator, dependency, or progress-control surfaces.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: execution-dependency-check
execution-dependency-check: execution-dependency-graph-check
	$(PYTHON) scripts/validation/validate_execution_dependency_contract.py

# Target: execution-dependency-explain
# Purpose: Explain dependency relationships for the selected target.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: TARGET (optional/defaulted).
# Scope: DERIVATION/EXECUTION — generator, dependency, or progress-control surfaces.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: execution-dependency-explain
execution-dependency-explain:
	$(PYTHON) scripts/coordination/explain_execution_dependency.py --target "$(TARGET)"

# Execution progress visibility

FORPRINT_PROGRESS ?= always
FORPRINT_PROGRESS_HEARTBEAT_SECONDS ?= 15
FORPRINT_PROGRESS_CHILD_OUTPUT ?= failures

export FORPRINT_PROGRESS
export FORPRINT_PROGRESS_HEARTBEAT_SECONDS
export FORPRINT_PROGRESS_CHILD_OUTPUT

# Target: execution-progress-check
# Purpose: Validate execution-progress visibility and tests.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: DERIVATION/EXECUTION — generator, dependency, or progress-control surfaces.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: execution-progress-check
execution-progress-check:
	$(PYTHON) scripts/validation/validate_execution_progress_visibility_v0_1.py
	$(PYTHON) -m pytest -q tests/coordination/test_execution_progress_visibility_v0_1.py

# Target: execution-progress-demo
# Purpose: Run the execution-progress demo with live child output.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: DERIVATION/EXECUTION — generator, dependency, or progress-control surfaces.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: execution-progress-demo
execution-progress-demo:
	$(PYTHON) scripts/coordination/execution_progress.py --demo --progress-child-output live


# =============================================================================
# 16 Continuity / handoff / Work Front / execution profiles
# =============================================================================
# Block scope: Control-foundation lifecycle, handoff, work-front, profile, procedure, and Handoff v2 commands.

# Target: roadmap-sync
# Purpose: Synchronize generated roadmap execution projections from canonical lifecycle state.
# Safety: GENERATED-PROJECTION MUTATION — refreshes derived roadmap execution projections only; canonical lifecycle authority remains the continuity event store.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: roadmap-sync
roadmap-sync:
	$(PYTHON) scripts/coordination/roadmap_execution_reconciliation.py --root . sync

# Target: roadmap-sync-check
# Purpose: Validate roadmap execution reconciliation without mutating projections.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: roadmap-sync-check
roadmap-sync-check:
	$(PYTHON) scripts/coordination/roadmap_execution_reconciliation.py --root . check
	$(PYTHON) scripts/validation/validate_roadmap_execution_reconciliation_v0_1.py
	$(PYTHON) -m pytest -q tests/validation/test_roadmap_execution_reconciliation_v0_1.py

# Target: assistant-handoff-check
# Purpose: Validate the assistant handoff compiler and its prerequisite governance contracts.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: assistant-handoff-check
assistant-handoff-check:
	$(MAKE) roadmap-sync-check
	$(MAKE) project-constitution-check
	$(MAKE) work-front-contract-check
	$(PYTHON) scripts/coordination/blueprint_continuity_adapter_v0_1.py --root . --handoff-validate
	$(PYTHON) scripts/validation/validate_assistant_handoff_compiler_v0_1.py
	$(PYTHON) -m pytest -q tests/validation/test_assistant_handoff_compiler_v0_1.py

# Target: assistant-pack
# Purpose: Build the authoritative project-onboarding assistant handoff archive after governance gates.
# Safety: GENERATED-ARTIFACT WRITE — creates the governed PROJECT_ONBOARD assistant handoff archive after read-only gates; grants no execution/release authority.
# Inputs: FRONT (optional/defaulted).
# Scope: PROJECT_ONBOARD — whole-project onboarding context bounded by the handoff contract.
# Result: A bounded assistant/context package is generated and its path/validation state is reported.
.PHONY: assistant-pack
assistant-pack:
	$(MAKE) roadmap-sync-check
	$(MAKE) project-constitution-check
	$(MAKE) work-front-assistant-pack-gate FRONT="$(FRONT)"
	$(PYTHON) scripts/coordination/blueprint_continuity_adapter_v0_1.py --root . --handoff-write

# Target: continuity-lifecycle-check
# Purpose: Validate continuity lifecycle rules and roadmap gates.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: continuity-lifecycle-check
continuity-lifecycle-check:
	$(PYTHON) scripts/validation/validate_continuity_lifecycle_v0_1.py
	$(PYTHON) -m pytest -q tests/validation/test_continuity_lifecycle_v0_1.py tests/validation/test_continuity_lifecycle_roadmap_gate_v0_1.py

# Target: continuity-transfer-check
# Purpose: Validate module continuity-transfer behavior.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: continuity-transfer-check
continuity-transfer-check:
	$(PYTHON) scripts/validation/validate_module_continuity_transfer_v0_1.py
	$(PYTHON) -m pytest -q tests/validation/test_module_continuity_transfer_v0_1.py

# Target: continuity-lifecycle-status
# Purpose: Render current continuity lifecycle status.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: continuity-lifecycle-status
continuity-lifecycle-status:
	$(PYTHON) scripts/coordination/continuity_lifecycle.py --root . status

# Target: continuity-projections-refresh
# Purpose: Rebuild generated continuity projections from canonical lifecycle state.
# Safety: GENERATED-PROJECTION MUTATION — rebuilds derived continuity projections only; does not change canonical lifecycle authority.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: continuity-projections-refresh
continuity-projections-refresh:
	$(PYTHON) scripts/coordination/blueprint_continuity_adapter_v0_1.py --root . --refresh

# Target: continuity-projections-check
# Purpose: Validate continuity projections without applying a refresh.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: continuity-projections-check
continuity-projections-check:
	$(PYTHON) scripts/coordination/blueprint_continuity_adapter_v0_1.py --root . --check
	$(PYTHON) scripts/validation/validate_continuity_projections_v0_1.py
	$(PYTHON) -m pytest -q tests/validation/test_continuity_projections_v0_1.py tests/validation/test_continuity_projection_dependency_registration_v0_1.py

# Target: continuity-event-store-check
# Purpose: Validate the append-only continuity event store.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: continuity-event-store-check
continuity-event-store-check:
	$(PYTHON) scripts/validation/validate_continuity_event_store_v0_1.py

# Target: continuity-fingerprint
# Purpose: Print the current continuity source-state fingerprint.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: continuity-fingerprint
continuity-fingerprint:
	$(PYTHON) scripts/coordination/continuity.py fingerprint --root .

# Target: continuity-checkpoint
# Purpose: Append a governed continuity checkpoint from the supplied checkpoint specification.
# Safety: CANONICAL LIFECYCLE MUTATION — appends one governed checkpoint from an explicit SPEC; does not auto-activate later work.
# Inputs: SPEC (required).
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: The documented bounded mutation/artifact operation completes or fails closed with a non-zero exit code.
.PHONY: continuity-checkpoint
continuity-checkpoint:
	@test -n "$(SPEC)" || (echo "SPEC=<checkpoint-spec.yaml> is required" >&2; exit 2)
	$(PYTHON) scripts/coordination/continuity.py checkpoint --root . --spec "$(SPEC)"

# Target: continuity-contract-check
# Purpose: Validate continuity contract invariants.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: continuity-contract-check
continuity-contract-check:
	$(PYTHON) scripts/validation/validate_continuity_contract_v0_1.py
	$(PYTHON) -m pytest -q tests/validation/test_continuity_contract_v0_1.py

# Target: continuity-micro-roadmap-check
# Purpose: Validate the continuity assistant-handoff micro-roadmap.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: continuity-micro-roadmap-check
continuity-micro-roadmap-check:
	$(PYTHON) scripts/validation/validate_continuity_micro_roadmap_v0_1.py

# Target: project-constitution-check
# Purpose: Validate the Project Constitution contract.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: project-constitution-check
project-constitution-check:
	.venv_blueprint/bin/python scripts/validation/validate_project_constitution_v0_1.py
# Target: work-front-contract-check
# Purpose: Validate the Work Front contract and tests.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: TASK/WORK-FRONT — explicitly selected execution package/profile/front.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: work-front-contract-check
work-front-contract-check:
	$(PYTHON) scripts/validation/validate_work_front_contract_v0_1.py
	$(PYTHON) -m pytest -q tests/validation/test_work_front_contract_v0_1.py

# Target: work-front-check
# Purpose: Validate or evaluate the supplied Work Front using the selected ACTION.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: FRONT (required), ACTION (optional/defaulted).
# Scope: TASK/WORK-FRONT — explicitly selected execution package/profile/front.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: work-front-check
work-front-check:
	@test -n "$(FRONT)" || (echo "WORK_FRONT_CHECK=FAIL"; echo "ERROR=FRONT_REQUIRED"; exit 2)
	$(PYTHON) scripts/coordination/work_front_v0_1.py --root . --front "$(FRONT)" --action "$(if $(ACTION),$(ACTION),validate)"

# Target: work-front-assistant-pack-gate
# Purpose: Apply the Work Front gate for assistant-pack when FRONT is supplied; project-onboard compatibility remains no-front.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: FRONT (optional/defaulted).
# Scope: TASK/WORK-FRONT — explicitly selected execution package/profile/front.
# Result: The target completes its documented operation and returns non-zero on failure.
.PHONY: work-front-assistant-pack-gate
work-front-assistant-pack-gate:
	@if [ -n "$(FRONT)" ]; then \
		$(PYTHON) scripts/coordination/work_front_v0_1.py --root . --front "$(FRONT)" --action assistant-pack; \
	else \
		echo "WORK_FRONT_GATE=NOT_APPLICABLE_PROJECT_ONBOARD_COMPAT"; \
	fi

# Target: workfront-history-check
# Purpose: Validate Work Front history integrity.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: workfront-history-check
workfront-history-check:
	$(PYTHON) scripts/validation/validate_workfront_history_v0_1.py
	$(PYTHON) -m pytest -q tests/validation/test_workfront_history_v0_1.py

# Target: execution-attempt-ledger-check
# Purpose: Validate execution-attempt ledger integrity.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: RELATED — target contract plus its direct validation dependencies.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: execution-attempt-ledger-check
execution-attempt-ledger-check:
	$(PYTHON) scripts/validation/validate_execution_attempt_ledger_v0_1.py
	$(PYTHON) -m pytest -q tests/validation/test_execution_attempt_ledger_v0_1.py

# Target: cf05-history-ledger-check
# Purpose: Run the combined CF-05 history/ledger validation gate.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: cf05-history-ledger-check
cf05-history-ledger-check: workfront-history-check execution-attempt-ledger-check

# Target: execution-profile-registry-check
# Purpose: Validate the execution profile registry.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: TASK/WORK-FRONT — explicitly selected execution package/profile/front.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: execution-profile-registry-check
execution-profile-registry-check:
	$(PYTHON) scripts/validation/validate_execution_profile_registry_v0_1.py
	$(PYTHON) -m pytest -q tests/validation/test_execution_profile_registry_v0_1.py

# Target: execution-profile-list
# Purpose: List registered execution profiles.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: TASK/WORK-FRONT — explicitly selected execution package/profile/front.
# Result: Human-readable status/content is printed to stdout; command returns non-zero on invalid required input.
.PHONY: execution-profile-list
execution-profile-list:
	$(PYTHON) scripts/coordination/execution_profiles_v0_1.py --root . list

# CF-07 first bounded Procedure Graph / Run Manifest conformance surface.
# Target: governed-procedure-graph-check
# Purpose: Validate governed Procedure Graph and Run Manifest contracts.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: governed-procedure-graph-check
governed-procedure-graph-check:
	$(PYTHON) scripts/validation/validate_governed_procedure_graph_v0_1.py
	$(PYTHON) -m pytest -q tests/validation/test_governed_procedure_graph_v0_1.py

# assistant-handoff-v2-s1-v0-1:start
# Target: assistant-handoff-v2-contract-check
# Purpose: Validate Handoff Compiler v2 contract surfaces and tests.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: assistant-handoff-v2-contract-check
assistant-handoff-v2-contract-check:
	$(BLUEPRINT_PYTHON) scripts/validation/validate_assistant_handoff_v2_contract_v0_1.py --root .
	$(BLUEPRINT_PYTHON) -m pytest -q tests/validation/test_assistant_handoff_v2_contract_v0_1.py
# assistant-handoff-v2-s1-v0-1:end

# assistant-handoff-v2-s2-runtime-v0-1:start
# Target: assistant-handoff-v2-runtime-check
# Purpose: Validate Handoff Compiler v2 runtime behavior, including PROJECT_ONBOARD dry run.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: assistant-handoff-v2-runtime-check
assistant-handoff-v2-runtime-check:
	$(BLUEPRINT_PYTHON) scripts/validation/validate_assistant_handoff_v2_runtime_v0_1.py --root .
	$(BLUEPRINT_PYTHON) -m pytest -q tests/validation/test_assistant_handoff_v2_runtime_v0_1.py
	$(BLUEPRINT_PYTHON) scripts/coordination/assistant_handoff_v2_runtime_v0_1.py --root . --launch-mode PROJECT_ONBOARD --no-write

# Target: assistant-handoff-v2-project-onboard
# Purpose: Build/run a Handoff v2 PROJECT_ONBOARD package from current canonical state.
# Safety: GENERATED-ARTIFACT WRITE — creates PROJECT_ONBOARD Handoff v2 output from current canonical state; grants no worker-dispatch authority.
# Inputs: None.
# Scope: PROJECT_ONBOARD — whole-project onboarding context bounded by the handoff contract.
# Result: A bounded assistant/context package is generated and its path/validation state is reported.
.PHONY: assistant-handoff-v2-project-onboard
assistant-handoff-v2-project-onboard:
	$(BLUEPRINT_PYTHON) scripts/coordination/assistant_handoff_v2_runtime_v0_1.py --root . --launch-mode PROJECT_ONBOARD

# Target: assistant-handoff-v2-task-execution
# Purpose: Build/run a Handoff v2 TASK_EXECUTION package for an explicit Work Front, profile, prompt, module root, and procedure decision.
# Safety: GENERATED-ARTIFACT WRITE — creates a bounded TASK_EXECUTION handoff package from explicit Work Front/profile/procedure inputs; grants no execution authority by itself.
# Inputs: FRONT (required), EXECUTION_PROFILE (required), TASK_PROMPT_ID (required), TASK_MODULE_ROOT (required), MODULE (optional/defaulted), PROCEDURE_ID (optional/defaulted), PROCEDURE_NOT_REQUIRED_REASON (optional/defaulted).
# Scope: TASK/WORK-FRONT — explicitly selected execution package/profile/front.
# Result: A bounded assistant/context package is generated and its path/validation state is reported.
.PHONY: assistant-handoff-v2-task-execution
assistant-handoff-v2-task-execution:
	@test -n "$(FRONT)" || { echo "FAILED: FRONT is required"; exit 2; }
	@test -n "$(EXECUTION_PROFILE)" || { echo "FAILED: EXECUTION_PROFILE is required"; exit 2; }
	@test -n "$(TASK_PROMPT_ID)" || { echo "FAILED: TASK_PROMPT_ID is required"; exit 2; }
	@test -n "$(TASK_MODULE_ROOT)" || { echo "FAILED: TASK_MODULE_ROOT is required"; exit 2; }
	@set -- --root . --launch-mode TASK_EXECUTION --front "$(FRONT)" --profile-id "$(EXECUTION_PROFILE)" --prompt-id "$(TASK_PROMPT_ID)" --module-root "$(TASK_MODULE_ROOT)"; 	if [ -n "$(MODULE)" ]; then set -- "$$@" --module "$(MODULE)"; fi; 	if [ -n "$(PROCEDURE_ID)" ]; then set -- "$$@" --procedure-id "$(PROCEDURE_ID)"; elif [ -n "$(PROCEDURE_NOT_REQUIRED_REASON)" ]; then set -- "$$@" --procedure-not-required-reason "$(PROCEDURE_NOT_REQUIRED_REASON)"; else echo "FAILED: PROCEDURE_ID or PROCEDURE_NOT_REQUIRED_REASON is required"; exit 2; fi; 	$(BLUEPRINT_PYTHON) scripts/coordination/assistant_handoff_v2_runtime_v0_1.py "$$@"
# assistant-handoff-v2-s2-runtime-v0-1:end

# assistant-handoff-v2-s3-result-v0-1:start
# Target: assistant-handoff-v2-result-check
# Purpose: Validate Handoff v2 result-envelope handling and tests.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: assistant-handoff-v2-result-check
assistant-handoff-v2-result-check:
	$(BLUEPRINT_PYTHON) scripts/validation/validate_assistant_handoff_v2_result_v0_1.py --root .
	$(BLUEPRINT_PYTHON) -m pytest -q tests/validation/test_assistant_handoff_v2_result_v0_1.py
# assistant-handoff-v2-s3-result-v0-1:end

# assistant-handoff-v2-s4-freshness-resume-v0-1:start
# Target: assistant-handoff-v2-freshness-resume-check
# Purpose: Validate Handoff v2 freshness, stale-context refusal, and structured resume behavior.
# Safety: READ-ONLY — does not intentionally mutate canonical project state, Git refs, or external systems.
# Inputs: None.
# Scope: CONTROL FOUNDATION — Blueprint continuity/handoff/control contracts.
# Result: Validation exits 0 on success and non-zero on failure; any report/tmp output is diagnostic evidence only.
.PHONY: assistant-handoff-v2-freshness-resume-check
assistant-handoff-v2-freshness-resume-check:
	$(BLUEPRINT_PYTHON) scripts/validation/validate_assistant_handoff_v2_freshness_resume_v0_1.py --root .
	$(BLUEPRINT_PYTHON) -m pytest -q tests/validation/test_assistant_handoff_v2_freshness_resume_v0_1.py
# assistant-handoff-v2-s4-freshness-resume-v0-1:end
