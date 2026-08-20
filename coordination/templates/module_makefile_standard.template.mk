# ForPrint Module Makefile Standard Template
#
# This file is an executable governance contract for module repositories.
# Copy it to a module repository and adapt only the variables and explicitly
# marked module-specific targets. Do not weaken target safety semantics.
#
# Command ownership:
#   - Module targets may read Blueprint files but must never mutate Blueprint.
#   - Module targets may execute only module-owned scripts.
#   - `prompt-prepare` and `prompt-release` are Blueprint-owned commands.
#     Module Makefiles must not implement, proxy, or invoke those mutations.
#   - An artifact under Blueprint `approved/` is storage, not execution authority.
#     A module may execute only a Prompt Queue v0.2 record whose
#     `module_execution.status` is `ready_for_module_pull`.
#   - Read-only targets must not write tracked/untracked repository files or
#     mutate Git state.
#   - Mutating targets must state their write scope explicitly.
#   - module-finish may mutate only the current module and never commit/push.
#   - module-publish may commit/push only the current branch and never merge.
#
# Make syntax:
#   - GNU Make with TAB-prefixed recipe lines.
#   - Do not use .RECIPEPREFIX.

.DEFAULT_GOAL := help
.DELETE_ON_ERROR:
export PYTHONDONTWRITEBYTECODE := 1
# =============================================================================
# 00 Environment / constants START
# =============================================================================

# Repository identity
MODULE_ID ?= forprint_module
MODULE_NAME ?= ForPrint Module
MODULE_ROOT ?= .
BLUEPRINT_ROOT ?= ../forprint_system_blueprint

# Tooling
PYTHON ?= .venv/bin/python
GIT ?= git

# Optional terminal colors.
# Set NO_COLOR=1 for plain output in CI, logs, or non-interactive terminals.
COLOR_RESET ?= \033[0m
COLOR_BOLD ?= \033[1m
COLOR_GREEN ?= \033[32m
COLOR_YELLOW ?= \033[33m
COLOR_BLUE ?= \033[34m
COLOR_CYAN ?= \033[36m
COLOR_RED ?= \033[31m

ifeq ($(strip $(NO_COLOR)),1)
COLOR_RESET :=
COLOR_BOLD :=
COLOR_GREEN :=
COLOR_YELLOW :=
COLOR_BLUE :=
COLOR_CYAN :=
COLOR_RED :=
endif

# Operator inputs
PACKET ?=
REMOTE ?= origin
BRANCH ?=
PUBLISH_MESSAGE ?=
STATUS ?= acknowledged
DOCUMENT ?=
SOURCE ?=
PRIORITY ?=
NOTES ?=
MODULE_COMMIT ?=
SCOPE ?= bootstrap
LIMIT ?= 40
MODULES ?=
ROADMAP ?=
BEFORE_CURRENT ?= 5
AFTER_CURRENT ?= 10
ROADMAP_SUMMARY_MODULES ?= $(MODULE_ID)

# Local module paths
REPORTS_DIR ?= reports
COORDINATION_DIR ?= coordination
CONFIG_DIR ?= config
DATA_DIR ?= data
LOGS_DIR ?= logs
STATE_DIR ?= state
TMP_DIR ?= tmp
REQUIREMENTS_APP ?= requirements/app.txt
REQUIREMENTS_DEV ?= requirements/dev.txt
PYPROJECT ?= pyproject.toml
ENV_EXAMPLE ?= .env.example
TOOLING_MANIFEST ?= coordination/tooling_manifest.yaml
DEVELOPMENT_ENVIRONMENT_DOC ?= coordination/development_environment.md
PROMPTS_DIR ?= $(COORDINATION_DIR)/prompts
LOCAL_PROMPTS_DIR ?= $(PROMPTS_DIR)/received
LOCAL_BLUEPRINT_SNAPSHOT_DIR ?= $(COORDINATION_DIR)/blueprint_snapshot
MODULE_DOCUMENT_AWARENESS_LEDGER ?= $(COORDINATION_DIR)/blueprint_awareness/document_review_ledger.yaml

# Blueprint read-only source paths
BLUEPRINT_PROMPTS_ROOT ?= $(BLUEPRINT_ROOT)/coordination/outgoing_prompts
BLUEPRINT_MODULE_PROMPTS_DIR ?= $(BLUEPRINT_PROMPTS_ROOT)/$(MODULE_ID)
BLUEPRINT_PROMPT_INDEX ?= $(BLUEPRINT_MODULE_PROMPTS_DIR)/index.yaml
ACTIVE_PROMPT_DIR ?= $(BLUEPRINT_MODULE_PROMPTS_DIR)/approved

# Module-owned workflow scripts
MODULE_SYNC_SCRIPT ?= scripts/coordination/module_sync.py
MODULE_STATUS_SCRIPT ?= scripts/coordination/module_status.py
MODULE_COORDINATION_VALIDATOR ?= scripts/coordination/validate_module_coordination.py
MODULE_PROMPT_CLI ?= scripts/coordination/module_prompt_cli.py
MODULE_DOCUMENT_CLI ?= scripts/coordination/module_document_cli.py
MODULE_ROADMAP_CLI ?= scripts/coordination/module_roadmap_cli.py
MODULE_CHECK_REPORT_SCRIPT ?= scripts/reporting/build_module_check_report.py
MODULE_PUBLISH_SCRIPT ?= scripts/coordination/module_publish.py
COMPLETION_PACKET_VALIDATE_SCRIPT ?= scripts/validate_completion_packet.py
COMPLETION_PACKET_CHECK_SCRIPT ?= scripts/check_completion_packet.py
COMPLETION_PACKET_PREVIEW_SCRIPT ?= scripts/preview_completion_packet.py
COMPLETION_PACKET_APPLY_SCRIPT ?= scripts/apply_completion_packet.py
COMPLETION_PACKET_IDEMPOTENCY_SCRIPT ?= scripts/check_completion_packet_idempotency.py
MODULE_WORKFLOW_CLI ?= scripts/coordination/modules/module_workflow_cli.py

# Source/test configuration
LINT_PATHS ?= app scripts tests
FORMAT_PATHS ?= app scripts tests
TEST_ARGS ?= -q -p no:cacheprovider

# Reusable fail-fast helpers. These helpers never hide missing implementation.
define require_file
@test -f "$(1)" || { echo "FAILED: missing required file: $(1)"; exit 2; }
endef

define require_module_script
@case "$(1)" in scripts/*) ;; *) echo "FAILED: module-owned script must be under scripts/: $(1)"; exit 2;; esac
@test -f "$(1)" || { echo "FAILED: missing required module-owned script: $(1)"; exit 2; }
endef

define require_dir
@test -d "$(1)" || { echo "FAILED: missing required directory: $(1)"; exit 2; }
endef

define require_value
@test -n "$($(1))" || { echo "FAILED: provide $(1)=..."; exit 2; }
endef

define require_packet
@test -n "$(PACKET)" || { printf '%b\n' "$(COLOR_RED)FAILED: PACKET is required.$(COLOR_RESET)"; exit 2; }
endef

define not_implemented
@echo "FAILED: target '$@' is not implemented for $(MODULE_ID)."; exit 2
endef

# =============================================================================
# 00 Environment / constants FINISH
# =============================================================================


# =============================================================================
# 01 Help / navigation START
# =============================================================================

# Purpose: List stable public commands and required operator inputs.
# Safety: Read-only; prints help only.
# Inputs: None.
# Result: Shows the canonical execution chain and explicit mutating commands.
.PHONY: help
help:
	@echo "$(MODULE_NAME) Make targets"
	@echo ""
	@echo "Canonical module workflow:"
	@echo "  make module-start"
	@echo "  make module-sync"
	@echo "  make module-status"
	@echo "  make module-validate"
	@echo "  make module-finish PACKET=<module-relative-packet>"
	@echo "  make module-publish PACKET=<packet> PUBLISH_MESSAGE='message' [REMOTE=origin] [BRANCH=current]"
	@echo ""
	@echo "Completion packet lifecycle:"
	@echo "  make completion-packet-validate PACKET=<packet>           # read-only"
	@echo "  make completion-packet-check PACKET=<packet>              # read-only"
	@echo "  make completion-packet-preview PACKET=<packet>            # read-only"
	@echo "  make completion-packet-idempotency-check PACKET=<packet>  # isolated sandbox"
	@echo "  make completion-packet-apply PACKET=<packet>              # module mutation"
	@echo ""
	@echo "Validation:"
	@echo "  make check"
	@echo "  make check-report"
	@echo "  make governance-check"
	@echo "  make git-status"
	@echo ""
	@echo "Blueprint source access:"
	@echo "  make coordination-sync-check   # explicit network read-only freshness gate"
	@echo "  make blueprint-check           # local filesystem/readability only"
	@echo ""
	@echo "Blueprint prompt consumption (read-only):"
	@echo "  make blueprint-prompts-list"
	@echo "  make prompt-notify"
	@echo "  make prompt-next"
	@echo "  make prompt-read-next"
	@echo "  Approved files are inventory only; readiness comes from Prompt Queue v0.2."
	@echo ""
	@echo "Blueprint-owned prompt mutations (intentionally unavailable here):"
	@echo "  prompt-prepare"
	@echo "  prompt-release"
	@echo ""
	@echo "Safety note: blueprint-pull is intentionally forbidden from module repositories."

# =============================================================================
# 01 Help / navigation FINISH
# =============================================================================


# =============================================================================
# 02 Operator entrypoints / Blueprint-first workflow START
# =============================================================================

# Purpose: Prepare the module for execution of the next approved prompt.
# Safety: Runs one explicit network-read freshness gate, then mutates only module-local snapshots; never writes Blueprint or Git refs.
# Inputs: Readable Blueprint root, network access for freshness, and module-owned sync/status/prompt CLIs.
# Result: Stale Blueprint blocks startup; otherwise local inputs sync, status/notification render, and the next prompt is read.
.PHONY: module-start
module-start:
	$(MAKE) coordination-sync-check
	$(MAKE) module-sync
	$(MAKE) module-status
	$(MAKE) prompt-notify
	$(MAKE) prompt-read-next

# Purpose: Run the complete module-owned synchronization workflow.
# Safety: Mutates only module-local snapshots through module-sync-apply; all follow-up checks are read-only.
# Inputs: MODULE_SYNC_SCRIPT, readable BLUEPRINT_ROOT, and module-owned awareness/coordination/status tools.
# Result: Blueprint inputs are synchronized locally, then awareness, coordination, and status checks pass.
.PHONY: module-sync
module-sync:
	$(MAKE) module-sync-apply
	$(MAKE) document-awareness
	$(MAKE) coordination-check
	$(MAKE) module-status

# Purpose: Apply approved Blueprint inputs to module-local snapshots.
# Safety: Internal module-only mutation; never executes Blueprint code, writes Blueprint, commits, pushes, or merges.
# Inputs: MODULE_SYNC_SCRIPT and readable BLUEPRINT_ROOT.
# Result: All supported Blueprint input scopes are synchronized deterministically into the module.
.PHONY: module-sync-apply
module-sync-apply:
	$(call require_module_script,$(MODULE_SYNC_SCRIPT))
	$(call require_dir,$(BLUEPRINT_ROOT))
	"$(PYTHON)" "$(MODULE_SYNC_SCRIPT)" --module-root "$(MODULE_ROOT)" --blueprint-root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --scope all

# Purpose: Render current module workflow, prompt, coordination, and Git status.
# Safety: Read-only; no report generation and no Git mutation.
# Inputs: MODULE_STATUS_SCRIPT.
# Result: Current state is printed to stdout.
.PHONY: module-status
module-status:
	$(call require_module_script,$(MODULE_STATUS_SCRIPT))
	"$(PYTHON)" "$(MODULE_STATUS_SCRIPT)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)"

# Purpose: Run the complete read-only module validation sequence.
# Safety: Read-only; excludes lint fixes, report cleanup, synchronization, commit, push, and merge.
# Inputs: Configured tools and module-owned governance validators.
# Result: All code, tests, governance, and packet-independent checks pass.
.PHONY: module-validate
module-validate:
	$(MAKE) check
	$(MAKE) governance-check

# Purpose: Finalize module-local completion records after read-only evidence checks.
# Safety: May mutate only the current module through completion-packet-apply; never commits, pushes, or merges.
# Inputs: PACKET and all completion packet scripts.
# Result: Packet validation/check/preview/idempotency pass, local apply completes, and final validation passes.
.PHONY: module-finish
module-finish:
	$(call require_packet)
	$(MAKE) module-validate
	$(MAKE) completion-packet-validate PACKET="$(PACKET)"
	$(MAKE) completion-packet-check PACKET="$(PACKET)"
	$(MAKE) completion-packet-preview PACKET="$(PACKET)"
	$(MAKE) completion-packet-idempotency-check PACKET="$(PACKET)"
	$(MAKE) completion-packet-apply PACKET="$(PACKET)"
	$(MAKE) module-validate

# Purpose: Commit and push a completed module packet on the current non-protected branch.
# Safety: Mutates only current module Git index/commit/remote branch; merge and protected-branch publication are forbidden.
# Inputs: PACKET, PUBLISH_MESSAGE, MODULE_PUBLISH_SCRIPT, REMOTE, optional BRANCH.
# Result: Allowlisted completion changes are committed and pushed without merge.
.PHONY: module-publish
module-publish:
	$(call require_packet)
	$(call require_value,PUBLISH_MESSAGE)
	$(call require_module_script,$(MODULE_PUBLISH_SCRIPT))
	@set -eu; set -- --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" --packet "$(PACKET)" --remote "$(REMOTE)" --message "$(PUBLISH_MESSAGE)" --require-clean-outside-packet --no-merge; if [ -n "$(BRANCH)" ]; then set -- "$$@" --branch "$(BRANCH)"; fi; "$(PYTHON)" "$(MODULE_PUBLISH_SCRIPT)" "$$@"

# =============================================================================
# 02 Operator entrypoints / Blueprint-first workflow FINISH
# =============================================================================


# =============================================================================
# 03 Blueprint repository synchronization START
# =============================================================================

MODULE_COORDINATION_SYNC_CHECK_SCRIPT ?= scripts/coordination_sync_check.py

# Purpose: Compatibility guard for removed legacy module-side Blueprint pull.
# Safety: Always fails; Blueprint updates are performed only in the Blueprint repository.
# Inputs: None.
# Result: Returns non-zero with the canonical H4 migration instruction.
.PHONY: blueprint-pull
blueprint-pull:
	@echo "FAILED: blueprint-pull is deprecated and forbidden; run coordination-sync-check, then update Blueprint only from the Blueprint repository if stale."; exit 2

# Purpose: Verify local Blueprint checkout freshness against its remote branch.
# Safety: Explicit network read only; no fetch, pull, ref update, Blueprint write, or module write.
# Inputs: BLUEPRINT_ROOT, MODULE_ID, MODULE_COORDINATION_SYNC_CHECK_SCRIPT.
# Result: Stale/unreachable Blueprint fails closed; prompt availability is reported.
.PHONY: coordination-sync-check
coordination-sync-check:
	$(call require_module_script,$(MODULE_COORDINATION_SYNC_CHECK_SCRIPT))
	"$(PYTHON)" "$(MODULE_COORDINATION_SYNC_CHECK_SCRIPT)" --blueprint-root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)"

# Purpose: Verify required Blueprint source paths are readable.
# Safety: Read-only filesystem checks; no Blueprint executable is invoked.
# Inputs: BLUEPRINT_ROOT and MODULE_ID.
# Result: Required source policy, standards, prompt queue, and approved prompt paths exist.
.PHONY: blueprint-check
blueprint-check:
	$(call require_dir,$(BLUEPRINT_ROOT))
	$(call require_dir,$(BLUEPRINT_ROOT)/coordination/global_policy)
	$(call require_dir,$(BLUEPRINT_ROOT)/coordination/standards)
	$(call require_file,$(BLUEPRINT_ROOT)/coordination/standards/index.yaml)
	$(call require_file,$(BLUEPRINT_ROOT)/coordination/module_policy/$(MODULE_ID)/module_policy.md)
	$(call require_file,$(BLUEPRINT_MODULE_PROMPTS_DIR)/index.yaml)

# Purpose: Synchronize Blueprint directives into module-local snapshots.
# Safety: Module-only mutation through MODULE_SYNC_SCRIPT.
# Inputs: MODULE_SYNC_SCRIPT and readable Blueprint source.
# Result: Directive snapshot is updated locally.
.PHONY: blueprint-sync-directives
blueprint-sync-directives:
	$(call require_module_script,$(MODULE_SYNC_SCRIPT))
	"$(PYTHON)" "$(MODULE_SYNC_SCRIPT)" --module-root "$(MODULE_ROOT)" --blueprint-root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --scope directives

# Purpose: Compatibility entrypoint for safe module-owned Blueprint input synchronization.
# Safety: Mutates only module-local snapshots; never pulls or writes Blueprint.
# Inputs: Same as module-sync.
# Result: Delegates to module-sync.
.PHONY: blueprint-sync
blueprint-sync:
	$(MAKE) module-sync

# =============================================================================
# 03 Blueprint repository synchronization FINISH
# =============================================================================


# =============================================================================
# 04 Blueprint instruction intake START
# =============================================================================

# Purpose: List Blueprint instruction source files.
# Safety: Read-only.
# Inputs: Readable Blueprint instruction intake directory.
# Result: Files are printed in stable order.
.PHONY: blueprint-instruction-list
blueprint-instruction-list:
	@find "$(BLUEPRINT_ROOT)/coordination/instruction_intake" -maxdepth 1 -type f | sort

# Purpose: Verify required Blueprint instruction files are readable.
# Safety: Read-only; no Blueprint executable.
# Inputs: BLUEPRINT_ROOT.
# Result: Required instruction files exist.
.PHONY: blueprint-instruction-check
blueprint-instruction-check:
	$(call require_file,$(BLUEPRINT_ROOT)/coordination/instruction_intake/assistant_reading_order.md)
	$(call require_file,$(BLUEPRINT_ROOT)/coordination/instruction_intake/instruction_sources.yaml)
	$(call require_file,$(BLUEPRINT_ROOT)/coordination/instruction_intake/module_profile_model.md)
	$(call require_file,$(BLUEPRINT_ROOT)/coordination/instruction_intake/default_profile_traits.yaml)

# Purpose: Synchronize instruction intake into module-local snapshots.
# Safety: Module-only mutation through MODULE_SYNC_SCRIPT.
# Inputs: MODULE_SYNC_SCRIPT.
# Result: Instruction snapshot is updated locally.
.PHONY: blueprint-instruction-sync
blueprint-instruction-sync:
	$(call require_module_script,$(MODULE_SYNC_SCRIPT))
	"$(PYTHON)" "$(MODULE_SYNC_SCRIPT)" --module-root "$(MODULE_ROOT)" --blueprint-root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --scope instructions

# Purpose: Run instruction list/check/sync in explicit order.
# Safety: Mutates only module-local snapshots in the final sync step.
# Inputs: Blueprint instruction source and MODULE_SYNC_SCRIPT.
# Result: Instruction workflow completes.
.PHONY: blueprint-instruction
blueprint-instruction:
	$(MAKE) blueprint-instruction-list
	$(MAKE) blueprint-instruction-check
	$(MAKE) blueprint-instruction-sync

# =============================================================================
# 04 Blueprint instruction intake FINISH
# =============================================================================


# =============================================================================
# 05 Blueprint standards and policies START
# =============================================================================

# Purpose: List Blueprint standards.
# Safety: Read-only.
# Inputs: Readable Blueprint standards directory.
# Result: Files are printed in stable order.
.PHONY: blueprint-standards-list
blueprint-standards-list:
	@find "$(BLUEPRINT_ROOT)/coordination/standards" -maxdepth 3 -type f | sort

# Purpose: Verify required Blueprint standards are readable.
# Safety: Read-only.
# Inputs: BLUEPRINT_ROOT.
# Result: Core standards and indexes exist.
.PHONY: blueprint-standards-check
blueprint-standards-check:
	$(call require_file,$(BLUEPRINT_ROOT)/coordination/standards/index.yaml)
	$(call require_dir,$(BLUEPRINT_ROOT)/coordination/standards/modular_topology_and_resilience)
	$(call require_dir,$(BLUEPRINT_ROOT)/coordination/standards/third_party_reuse)

# Purpose: Synchronize standards into module-local snapshots.
# Safety: Module-only mutation through MODULE_SYNC_SCRIPT.
# Inputs: MODULE_SYNC_SCRIPT.
# Result: Standards snapshot is updated locally.
.PHONY: blueprint-standards-sync
blueprint-standards-sync:
	$(call require_module_script,$(MODULE_SYNC_SCRIPT))
	"$(PYTHON)" "$(MODULE_SYNC_SCRIPT)" --module-root "$(MODULE_ROOT)" --blueprint-root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --scope standards

# Purpose: Run standards list/check/sync.
# Safety: Mutates only module-local snapshots in the final sync step.
# Inputs: Blueprint standards and MODULE_SYNC_SCRIPT.
# Result: Standards workflow completes.
.PHONY: blueprint-standards
blueprint-standards:
	$(MAKE) blueprint-standards-list
	$(MAKE) blueprint-standards-check
	$(MAKE) blueprint-standards-sync

# =============================================================================
# 05 Blueprint standards and policies FINISH
# =============================================================================


# =============================================================================
# 06 Blueprint outgoing prompts / prompt queue START
# =============================================================================

# Ownership boundary:
# - `prompt-prepare` and `prompt-release` are Blueprint-only mutations.
# - This module template intentionally does not define or proxy those targets.
# - Files in `approved/` are artifact inventory only.
# - Executable authority comes only from Prompt Queue v0.2 with
#   `module_execution.status: ready_for_module_pull`.
#
# Purpose: List the Blueprint queue source and approved artifact inventory.
# Safety: Read-only; listing an approved artifact does not authorize execution.
# Inputs: BLUEPRINT_PROMPT_INDEX and ACTIVE_PROMPT_DIR.
# Result: Queue index path and approved artifact inventory are printed.
.PHONY: blueprint-prompts-list
blueprint-prompts-list:
	$(call require_file,$(BLUEPRINT_PROMPT_INDEX))
	$(call require_dir,$(ACTIVE_PROMPT_DIR))
	@echo "Prompt Queue v0.2 source: $(BLUEPRINT_PROMPT_INDEX)"
	@echo "Approved artifact inventory (not execution readiness):"
	@find "$(ACTIVE_PROMPT_DIR)" -maxdepth 1 -type f -name "*.md" | sort
	@echo "Use prompt-next or prompt-read-next to resolve ready_for_module_pull work."

# Purpose: Verify the module has a readable queue index and approved storage.
# Safety: Read-only; does not select, prepare, release, or execute a prompt.
# Inputs: BLUEPRINT_PROMPT_INDEX and ACTIVE_PROMPT_DIR.
# Result: Queue source exists and at least one approved artifact is readable.
.PHONY: blueprint-prompts-check
blueprint-prompts-check:
	$(call require_file,$(BLUEPRINT_PROMPT_INDEX))
	$(call require_dir,$(ACTIVE_PROMPT_DIR))
	@test -n "$$(find "$(ACTIVE_PROMPT_DIR)" -maxdepth 1 -type f -name '*.md' -print -quit)" || { echo "FAILED: no approved prompt artifacts for $(MODULE_ID)."; exit 2; }

# Purpose: Synchronize approved prompts into module-local snapshots.
# Safety: Module-only mutation through MODULE_SYNC_SCRIPT.
# Inputs: MODULE_SYNC_SCRIPT.
# Result: Prompt snapshots are updated locally.
.PHONY: blueprint-prompts-sync
blueprint-prompts-sync:
	$(call require_module_script,$(MODULE_SYNC_SCRIPT))
	"$(PYTHON)" "$(MODULE_SYNC_SCRIPT)" --module-root "$(MODULE_ROOT)" --blueprint-root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --scope prompts

# Purpose: Run prompt inventory/check/sync and local queue validation.
# Safety: Mutates only module-local snapshots during sync; never prepares or
# releases Blueprint prompts.
# Inputs: Prompt source, MODULE_SYNC_SCRIPT, MODULE_PROMPT_CLI.
# Result: Local queue is synchronized and readiness is rendered explicitly.
.PHONY: blueprint-prompts
blueprint-prompts:
	$(MAKE) blueprint-prompts-list
	$(MAKE) blueprint-prompts-check
	$(MAKE) blueprint-prompts-sync
	$(MAKE) prompt-queue-validate
	$(MAKE) prompt-dashboard



# Purpose: Render current Blueprint prompt availability without claiming work.
# Safety: Local read-only; no network, queue mutation, or CLAIMED event.
# Inputs: BLUEPRINT_ROOT, MODULE_ID, MODULE_COORDINATION_SYNC_CHECK_SCRIPT.
# Result: READY_PROMPT, NO_READY_PROMPT, or MULTIPLE_READY_PROMPTS is reported explicitly.
.PHONY: prompt-notify
prompt-notify:
	$(call require_module_script,$(MODULE_COORDINATION_SYNC_CHECK_SCRIPT))
	"$(PYTHON)" "$(MODULE_COORDINATION_SYNC_CHECK_SCRIPT)" --blueprint-root "$(BLUEPRINT_ROOT)" --module "$(MODULE_ID)" --local-only

# Purpose: Read the current local synchronized prompt.
# Safety: Read-only; module-owned executable only.
# Inputs: MODULE_PROMPT_CLI
# Result: Requested information is printed.
.PHONY: prompt-read
prompt-read:
	$(call require_module_script,$(MODULE_PROMPT_CLI))
	"$(PYTHON)" "$(MODULE_PROMPT_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" read-current

# Purpose: Validate the local synchronized prompt queue.
# Safety: Read-only; module-owned executable only.
# Inputs: MODULE_PROMPT_CLI
# Result: Requested information is printed.
.PHONY: prompt-queue-validate
prompt-queue-validate:
	$(call require_module_script,$(MODULE_PROMPT_CLI))
	"$(PYTHON)" "$(MODULE_PROMPT_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" validate

# Purpose: Render local prompt queue status.
# Safety: Read-only; module-owned executable only.
# Inputs: MODULE_PROMPT_CLI
# Result: Requested information is printed.
.PHONY: prompt-dashboard
prompt-dashboard:
	$(call require_module_script,$(MODULE_PROMPT_CLI))
	"$(PYTHON)" "$(MODULE_PROMPT_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" dashboard

# Purpose: Resolve the next local synchronized ready prompt.
# Safety: Read-only; module-owned executable only; selects only
# `module_execution.status: ready_for_module_pull`.
# Inputs: MODULE_PROMPT_CLI.
# Result: The next executable prompt is printed, or no-ready-prompt is reported.
.PHONY: prompt-next
prompt-next:
	$(call require_module_script,$(MODULE_PROMPT_CLI))
	"$(PYTHON)" "$(MODULE_PROMPT_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" next

# Purpose: Read the next local synchronized ready prompt.
# Safety: Read-only; module-owned executable only; never reads planning-only
# drafts as executable work.
# Inputs: MODULE_PROMPT_CLI.
# Result: The ready prompt selected from Prompt Queue v0.2 is printed.
.PHONY: prompt-read-next
prompt-read-next:
	$(call require_module_script,$(MODULE_PROMPT_CLI))
	"$(PYTHON)" "$(MODULE_PROMPT_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" read-next

# =============================================================================
# 06 Blueprint outgoing prompts / prompt queue FINISH
# =============================================================================


# =============================================================================
# 07 Blueprint document awareness START
# =============================================================================

# Purpose: Validate and print document manifest without writes.
# Safety: Read-only; module-owned executable only.
# Inputs: MODULE_DOCUMENT_CLI
# Result: Requested information is printed.
.PHONY: document-manifest
document-manifest:
	$(call require_module_script,$(MODULE_DOCUMENT_CLI))
	"$(PYTHON)" "$(MODULE_DOCUMENT_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" manifest --no-write

# Purpose: Write module-local document manifest.
# Safety: Mutates module-local generated manifest only.
# Inputs: MODULE_DOCUMENT_CLI
# Result: Module-local manifest is written.
.PHONY: document-manifest-write
document-manifest-write:
	$(call require_module_script,$(MODULE_DOCUMENT_CLI))
	"$(PYTHON)" "$(MODULE_DOCUMENT_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" manifest --write

# Purpose: Render module-local Blueprint document awareness.
# Safety: Read-only; module-owned executable only.
# Inputs: MODULE_DOCUMENT_CLI
# Result: Requested information is printed.
.PHONY: document-awareness
document-awareness:
	$(call require_module_script,$(MODULE_DOCUMENT_CLI))
	"$(PYTHON)" "$(MODULE_DOCUMENT_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" awareness --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --limit "$(LIMIT)"

# Purpose: Build context bundle without writing.
# Safety: Read-only; module-owned executable only.
# Inputs: MODULE_DOCUMENT_CLI
# Result: Requested information is printed.
.PHONY: context-bundle
context-bundle:
	$(call require_module_script,$(MODULE_DOCUMENT_CLI))
	"$(PYTHON)" "$(MODULE_DOCUMENT_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" context-bundle --scope "$(SCOPE)" --limit "$(LIMIT)" --no-write

# Purpose: Write a module-local context bundle.
# Safety: Mutates module-local generated context bundle only.
# Inputs: MODULE_DOCUMENT_CLI
# Result: Module-local bundle is written.
.PHONY: context-bundle-write
context-bundle-write:
	$(call require_module_script,$(MODULE_DOCUMENT_CLI))
	"$(PYTHON)" "$(MODULE_DOCUMENT_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" context-bundle --scope "$(SCOPE)" --limit "$(LIMIT)" --write

# Purpose: Print a context bundle to stdout.
# Safety: Read-only; module-owned executable only.
# Inputs: MODULE_DOCUMENT_CLI
# Result: Requested information is printed.
.PHONY: context-bundle-print
context-bundle-print:
	$(call require_module_script,$(MODULE_DOCUMENT_CLI))
	"$(PYTHON)" "$(MODULE_DOCUMENT_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" context-bundle --scope "$(SCOPE)" --limit "$(LIMIT)" --print

# Purpose: Preview document ledger changes.
# Safety: Read-only; module-owned executable only.
# Inputs: At least one of DOCUMENT, SOURCE, PRIORITY and MODULE_DOCUMENT_CLI.
# Result: Ledger change plan is printed.
.PHONY: document-ledger-preview
document-ledger-preview:
	$(call require_module_script,$(MODULE_DOCUMENT_CLI))
	@set -eu; if [ -z "$(DOCUMENT)$(SOURCE)$(PRIORITY)" ]; then echo "FAILED: provide DOCUMENT=..., SOURCE=..., or PRIORITY=..."; exit 2; fi; set -- --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" ledger --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --status "$(STATUS)" --no-write; if [ -n "$(DOCUMENT)" ]; then set -- "$$@" --document "$(DOCUMENT)"; fi; if [ -n "$(SOURCE)" ]; then set -- "$$@" --source "$(SOURCE)"; fi; if [ -n "$(PRIORITY)" ]; then set -- "$$@" --priority "$(PRIORITY)"; fi; if [ -n "$(NOTES)" ]; then set -- "$$@" --notes "$(NOTES)"; fi; if [ -n "$(MODULE_COMMIT)" ]; then set -- "$$@" --module-commit "$(MODULE_COMMIT)"; fi; "$(PYTHON)" "$(MODULE_DOCUMENT_CLI)" "$$@"

# Purpose: Apply document ledger changes.
# Safety: Mutates only the module-local ledger.
# Inputs: At least one of DOCUMENT, SOURCE, PRIORITY and MODULE_DOCUMENT_CLI.
# Result: Selected ledger entries are updated.
.PHONY: document-ledger-update
document-ledger-update:
	$(call require_module_script,$(MODULE_DOCUMENT_CLI))
	@set -eu; if [ -z "$(DOCUMENT)$(SOURCE)$(PRIORITY)" ]; then echo "FAILED: provide DOCUMENT=..., SOURCE=..., or PRIORITY=..."; exit 2; fi; set -- --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" ledger --ledger "$(MODULE_DOCUMENT_AWARENESS_LEDGER)" --status "$(STATUS)" --write; if [ -n "$(DOCUMENT)" ]; then set -- "$$@" --document "$(DOCUMENT)"; fi; if [ -n "$(SOURCE)" ]; then set -- "$$@" --source "$(SOURCE)"; fi; if [ -n "$(PRIORITY)" ]; then set -- "$$@" --priority "$(PRIORITY)"; fi; if [ -n "$(NOTES)" ]; then set -- "$$@" --notes "$(NOTES)"; fi; if [ -n "$(MODULE_COMMIT)" ]; then set -- "$$@" --module-commit "$(MODULE_COMMIT)"; fi; "$(PYTHON)" "$(MODULE_DOCUMENT_CLI)" "$$@"

# =============================================================================
# 07 Blueprint document awareness FINISH
# =============================================================================


# =============================================================================
# 08 Module coordination metadata START
# =============================================================================

# Purpose: Validate the module-local synchronized roadmap.
# Safety: Read-only; module-owned executable only.
# Inputs: MODULE_ROADMAP_CLI
# Result: Requested information is printed.
.PHONY: roadmap-validate
roadmap-validate:
	$(call require_module_script,$(MODULE_ROADMAP_CLI))
	"$(PYTHON)" "$(MODULE_ROADMAP_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" validate

# Purpose: Dashboard the module-local synchronized roadmap.
# Safety: Read-only; module-owned executable only.
# Inputs: MODULE_ROADMAP_CLI
# Result: Requested information is printed.
.PHONY: roadmap-dashboard
roadmap-dashboard:
	$(call require_module_script,$(MODULE_ROADMAP_CLI))
	"$(PYTHON)" "$(MODULE_ROADMAP_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" dashboard --before-current "$(BEFORE_CURRENT)" --after-current "$(AFTER_CURRENT)"

# Purpose: Summary the module-local synchronized roadmap.
# Safety: Read-only; module-owned executable only.
# Inputs: MODULE_ROADMAP_CLI
# Result: Requested information is printed.
.PHONY: roadmap-summary
roadmap-summary:
	$(call require_module_script,$(MODULE_ROADMAP_CLI))
	"$(PYTHON)" "$(MODULE_ROADMAP_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" summary --modules "$(ROADMAP_SUMMARY_MODULES)"


# Purpose: Validate module-owned coordination metadata.
# Safety: Read-only; module-owned validator only.
# Inputs: MODULE_COORDINATION_VALIDATOR.
# Result: Coordination metadata passes.
.PHONY: coordination-check
coordination-check:
	$(call require_module_script,$(MODULE_COORDINATION_VALIDATOR))
	"$(PYTHON)" "$(MODULE_COORDINATION_VALIDATOR)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)"

# Purpose: Apply explicitly supported module-local coordination repairs.
# Safety: Mutates only module coordination files; never Blueprint or Git refs.
# Inputs: MODULE_COORDINATION_VALIDATOR with fix support.
# Result: Supported repairs are applied or command fails.
.PHONY: coordination-fix
coordination-fix:
	$(call require_module_script,$(MODULE_COORDINATION_VALIDATOR))
	"$(PYTHON)" "$(MODULE_COORDINATION_VALIDATOR)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" --fix

# =============================================================================
# 08 Module coordination metadata FINISH
# =============================================================================


# =============================================================================
# 09 Module governance / policy checks START
# =============================================================================

# Purpose: Verify Blueprint module policy is readable.
# Safety: Read-only filesystem check.
# Inputs: BLUEPRINT_ROOT and MODULE_ID.
# Result: Module policy exists.
.PHONY: module-policy-check
module-policy-check:
	$(call require_file,$(BLUEPRINT_ROOT)/coordination/module_policy/$(MODULE_ID)/module_policy.md)

# Purpose: Run the complete read-only governance sequence.
# Safety: Read-only; never synchronizes, pulls, fixes, writes reports, or executes Blueprint code.
# Inputs: Module-owned validators and readable Blueprint source.
# Result: Governance checks pass.
.PHONY: governance-check
governance-check:
	$(MAKE) blueprint-check
	$(MAKE) blueprint-instruction-check
	$(MAKE) blueprint-standards-check
	$(MAKE) blueprint-prompts-check
	$(MAKE) prompt-queue-validate
	$(MAKE) document-manifest
	$(MAKE) module-policy-check
	$(MAKE) coordination-check
	$(MAKE) status-report

# =============================================================================
# 09 Module governance / policy checks FINISH
# =============================================================================


# =============================================================================
# 10 Module install / bootstrap START
# =============================================================================

# Purpose: Install module development dependencies.
# Safety: Mutates only the local Python environment.
# Inputs: REQUIREMENTS_DEV or PYPROJECT.
# Result: Development dependencies are installed.
.PHONY: install
install:
	@set -eu; if [ -f "$(REQUIREMENTS_DEV)" ]; then "$(PYTHON)" -m pip install --upgrade pip; "$(PYTHON)" -m pip install -r "$(REQUIREMENTS_DEV)"; elif [ -f "$(PYPROJECT)" ]; then "$(PYTHON)" -m pip install --upgrade pip; "$(PYTHON)" -m pip install -e ".[dev]"; else echo "FAILED: neither $(REQUIREMENTS_DEV) nor $(PYPROJECT) exists."; exit 2; fi

# Purpose: Run module-specific first-time bootstrap.
# Safety: Mutating; must be implemented explicitly per module.
# Inputs: Module-specific implementation.
# Result: Fails until implemented.
.PHONY: bootstrap
bootstrap:
	$(call not_implemented)

# =============================================================================
# 10 Module install / bootstrap FINISH
# =============================================================================


# =============================================================================
# 11 Module environment / local configuration START
# =============================================================================

# Purpose: Verify required local executable and repository identity.
# Safety: Read-only.
# Inputs: PYTHON, MODULE_ID, MODULE_ROOT.
# Result: Required environment is usable.
.PHONY: env-check
env-check:
	@test -n "$(MODULE_ID)" || { echo "FAILED: MODULE_ID is empty."; exit 2; }
	@test -d "$(MODULE_ROOT)" || { echo "FAILED: MODULE_ROOT does not exist: $(MODULE_ROOT)"; exit 2; }
	@command -v "$(PYTHON)" >/dev/null 2>&1 || test -x "$(PYTHON)" || { echo "FAILED: Python executable is unavailable: $(PYTHON)"; exit 2; }
	@"$(PYTHON)" --version

# Purpose: Verify mandatory Python validation tools.
# Safety: Read-only.
# Inputs: PYTHON.
# Result: ruff, pytest, and PyYAML are available.
.PHONY: tooling-check
tooling-check:
	@"$(PYTHON)" -m ruff --version >/dev/null
	@"$(PYTHON)" -m pytest --version >/dev/null
	@"$(PYTHON)" -c "import yaml"

# Purpose: Verify required project configuration entrypoints.
# Safety: Read-only.
# Inputs: PYPROJECT or REQUIREMENTS_DEV.
# Result: At least one supported dependency definition exists.
.PHONY: config-check
config-check:
	@test -f "$(PYPROJECT)" || test -f "$(REQUIREMENTS_DEV)" || { echo "FAILED: missing $(PYPROJECT) and $(REQUIREMENTS_DEV)."; exit 2; }

# Purpose: Reject tracked secret-like environment files.
# Safety: Read-only Git queries only.
# Inputs: Git worktree.
# Result: No forbidden secret-like files are tracked.
.PHONY: secrets-check
secrets-check:
	@$(GIT) rev-parse --is-inside-work-tree >/dev/null
	@if $(GIT) ls-files | grep -E '(^|/)(\.env|\.env\.local|\.env\.prod|secrets/.*\.env)$$' >/dev/null; then echo "FAILED: tracked secret-like env file detected."; $(GIT) ls-files | grep -E '(^|/)(\.env|\.env\.local|\.env\.prod|secrets/.*\.env)$$'; exit 2; fi

# =============================================================================
# 11 Module environment / local configuration FINISH
# =============================================================================


# =============================================================================
# 12 Runtime control / process lifecycle START
# =============================================================================

# Purpose: Module-specific implementation hook for run.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: run
run:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for start.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: start
start:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for stop.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: stop
stop:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for reload.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: reload
reload:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for status.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: status
status:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for logs.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: logs
logs:
	$(call not_implemented)

# Purpose: Restart the implemented local runtime.
# Safety: Delegates to explicit stop/start; inherits their safety.
# Inputs: Implemented stop and start targets.
# Result: Runtime restarts.
.PHONY: restart
restart:
	$(MAKE) stop
	$(MAKE) start

# =============================================================================
# 12 Runtime control / process lifecycle FINISH
# =============================================================================


# =============================================================================
# 13 Infrastructure / local services START
# =============================================================================

# Purpose: Module-specific implementation hook for services-up.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: services-up
services-up:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for services-down.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: services-down
services-down:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for services-status.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: services-status
services-status:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for workers-start.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: workers-start
workers-start:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for workers-stop.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: workers-stop
workers-stop:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for monitors-start.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: monitors-start
monitors-start:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for monitors-stop.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: monitors-stop
monitors-stop:
	$(call not_implemented)

# Purpose: Restart local services.
# Safety: Delegates to explicit down/up.
# Inputs: Implemented service targets.
# Result: Services restart.
.PHONY: services-restart
services-restart:
	$(MAKE) services-down
	$(MAKE) services-up

# Purpose: Compatibility alias for services-up.
# Safety: Same as services-up.
# Inputs: Implemented services-up.
# Result: Delegates.
.PHONY: services-start
services-start:
	$(MAKE) services-up

# Purpose: Compatibility alias for services-down.
# Safety: Same as services-down.
# Inputs: Implemented services-down.
# Result: Delegates.
.PHONY: services-stop
services-stop:
	$(MAKE) services-down

# Purpose: Restart workers.
# Safety: Delegates to explicit stop/start.
# Inputs: Implemented worker targets.
# Result: Workers restart.
.PHONY: workers-restart
workers-restart:
	$(MAKE) workers-stop
	$(MAKE) workers-start

# Purpose: Restart monitors.
# Safety: Delegates to explicit stop/start.
# Inputs: Implemented monitor targets.
# Result: Monitors restart.
.PHONY: monitors-restart
monitors-restart:
	$(MAKE) monitors-stop
	$(MAKE) monitors-start

# =============================================================================
# 13 Infrastructure / local services FINISH
# =============================================================================


# =============================================================================
# 14 Database / storage / migrations START
# =============================================================================

# Purpose: Module-specific implementation hook for db-check.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: db-check
db-check:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for db-migrate.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: db-migrate
db-migrate:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for db-downgrade.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: db-downgrade
db-downgrade:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for db-seed.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: db-seed
db-seed:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for db-reset.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: db-reset
db-reset:
	$(call not_implemented)

# Purpose: Compatibility alias for db-migrate.
# Safety: Same as db-migrate.
# Inputs: Implemented db-migrate.
# Result: Delegates.
.PHONY: migrate
migrate:
	$(MAKE) db-migrate

# Purpose: Upgrade local database state.
# Safety: Delegates to explicit db-migrate.
# Inputs: Implemented db-migrate.
# Result: Database is upgraded.
.PHONY: db-upgrade
db-upgrade:
	$(MAKE) db-migrate

# =============================================================================
# 14 Database / storage / migrations FINISH
# =============================================================================


# =============================================================================
# 15 Data import / export / fixtures START
# =============================================================================

# Purpose: Module-specific implementation hook for fixtures-check.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: fixtures-check
fixtures-check:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for fixtures-load.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: fixtures-load
fixtures-load:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for import-preview.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: import-preview
import-preview:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for export-preview.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: export-preview
export-preview:
	$(call not_implemented)

# Purpose: Compatibility alias for fixtures-load.
# Safety: Same as fixtures-load.
# Inputs: Implemented fixtures-load.
# Result: Delegates.
.PHONY: data-fixtures
data-fixtures:
	$(MAKE) fixtures-load

# =============================================================================
# 15 Data import / export / fixtures FINISH
# =============================================================================


# =============================================================================
# 16 External adapters / sandbox integrations START
# =============================================================================

# Purpose: Module-specific implementation hook for adapters-check.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: adapters-check
adapters-check:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for sandbox-check.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: sandbox-check
sandbox-check:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for sandbox-sync.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: sandbox-sync
sandbox-sync:
	$(call not_implemented)

# Purpose: Run adapter smoke checks through sandbox-check.
# Safety: Read-only when sandbox-check is correctly implemented.
# Inputs: Implemented sandbox-check.
# Result: Delegates.
.PHONY: adapters-smoke
adapters-smoke:
	$(MAKE) sandbox-check

# Purpose: Compatibility alias for sandbox-check.
# Safety: Same as sandbox-check.
# Inputs: Implemented sandbox-check.
# Result: Delegates.
.PHONY: adapters-sandbox-check
adapters-sandbox-check:
	$(MAKE) sandbox-check

# =============================================================================
# 16 External adapters / sandbox integrations FINISH
# =============================================================================


# =============================================================================
# 17 Local previews / operator workflows START
# =============================================================================

# Purpose: Module-specific implementation hook for preview.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: preview
preview:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for smoke.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: smoke
smoke:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for operator-demo.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: operator-demo
operator-demo:
	$(call not_implemented)

# =============================================================================
# 17 Local previews / operator workflows FINISH
# =============================================================================


# =============================================================================
# 18 Observability / diagnostics / logs START
# =============================================================================

# Purpose: Module-specific implementation hook for diagnostics.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: diagnostics
diagnostics:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for health.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: health
health:
	$(call not_implemented)

# Purpose: Module-specific implementation hook for inspect.
# Safety: Fails closed until explicitly implemented in the module.
# Inputs: Module-specific implementation.
# Result: Returns non-zero while unimplemented.
.PHONY: inspect
inspect:
	$(call not_implemented)

# =============================================================================
# 18 Observability / diagnostics / logs FINISH
# =============================================================================


# =============================================================================
# 19 Syntax / formatting / lint START
# =============================================================================

# Purpose: Run Ruff without modifying files.
# Safety: Read-only.
# Inputs: LINT_PATHS.
# Result: Lint passes.
.PHONY: lint
lint:
	"$(PYTHON)" -m ruff check $(LINT_PATHS)

# Purpose: Apply Ruff-safe automatic fixes.
# Safety: Mutates source files only.
# Inputs: LINT_PATHS.
# Result: Fixable lint findings are corrected.
.PHONY: lint-fix
lint-fix:
	"$(PYTHON)" -m ruff check $(LINT_PATHS) --fix

# Purpose: Format configured source paths.
# Safety: Mutates source files only.
# Inputs: FORMAT_PATHS.
# Result: Source formatting is applied.
.PHONY: format
format:
	"$(PYTHON)" -m ruff format $(FORMAT_PATHS)

# Purpose: Check formatting without changes.
# Safety: Read-only.
# Inputs: FORMAT_PATHS.
# Result: Formatting is compliant.
.PHONY: format-check
format-check:
	"$(PYTHON)" -m ruff format --check $(FORMAT_PATHS)

# =============================================================================
# 19 Syntax / formatting / lint FINISH
# =============================================================================


# =============================================================================
# 20 Tests START
# =============================================================================

# Purpose: Run the module test suite.
# Safety: Read-only except test-framework temporary files outside governed outputs.
# Inputs: TEST_ARGS.
# Result: Tests pass.
.PHONY: test
test:
	"$(PYTHON)" -m pytest $(TEST_ARGS)

# Purpose: Run unit tests.
# Safety: Read-only.
# Inputs: Module-specific pytest markers or default suite.
# Result: Delegates to test.
.PHONY: test-unit
test-unit:
	$(MAKE) test

# Purpose: Run contract tests.
# Safety: Read-only.
# Inputs: Module-specific implementation.
# Result: Fails until implemented.
.PHONY: test-contract
test-contract:
	$(call not_implemented)

# Purpose: Run integration tests.
# Safety: Read-only and must use non-production resources.
# Inputs: Module-specific implementation.
# Result: Fails until implemented.
.PHONY: test-integration
test-integration:
	$(call not_implemented)

# =============================================================================
# 20 Tests FINISH
# =============================================================================


# =============================================================================
# 21 Validation / check reports START
# =============================================================================

# Purpose: Run the standard read-only code validation sequence.
# Safety: Read-only; notably excludes lint-fix, format, synchronization, report generation, cleanup, commit, and push.
# Inputs: Configured tools and tests.
# Result: Validation passes.
.PHONY: check
check:
	$(MAKE) env-check
	$(MAKE) tooling-check
	$(MAKE) config-check
	$(MAKE) secrets-check
	$(MAKE) format-check
	$(MAKE) lint
	$(MAKE) test

# Purpose: Run validation and explicitly write module-local reports.
# Safety: Mutates only generated report files through MODULE_CHECK_REPORT_SCRIPT.
# Inputs: MODULE_CHECK_REPORT_SCRIPT.
# Result: Validation passes and reports are written.
.PHONY: check-report
check-report:
	$(MAKE) module-validate
	$(call require_module_script,$(MODULE_CHECK_REPORT_SCRIPT))
	"$(PYTHON)" "$(MODULE_CHECK_REPORT_SCRIPT)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" --output-dir "$(REPORTS_DIR)"

# =============================================================================
# 21 Validation / check reports FINISH
# =============================================================================


# =============================================================================
# 22 Status reports / generated reports / cleanup START
# =============================================================================

# Purpose: Run validation and write extended module-local diagnostics.
# Safety: Mutates only generated report files through MODULE_CHECK_REPORT_SCRIPT.
# Inputs: MODULE_CHECK_REPORT_SCRIPT.
# Result: Extended reports are written.
.PHONY: check-report-full
check-report-full:
	$(MAKE) module-validate
	$(call require_module_script,$(MODULE_CHECK_REPORT_SCRIPT))
	"$(PYTHON)" "$(MODULE_CHECK_REPORT_SCRIPT)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" --output-dir "$(REPORTS_DIR)" --full

# Purpose: Print current module status without writing reports.
# Safety: Read-only.
# Inputs: MODULE_STATUS_SCRIPT.
# Result: Status is printed.
.PHONY: status-report
status-report:
	$(MAKE) module-status

# Purpose: Remove only known generated module report artifacts.
# Safety: Explicit module-local mutation; never uses git restore/reset/clean.
# Inputs: REPORTS_DIR.
# Result: Known generated reports are removed.
.PHONY: report-clean
report-clean:
	@rm -f -- "$(REPORTS_DIR)/$(MODULE_ID)_check_report.json" "$(REPORTS_DIR)/$(MODULE_ID)_check_report.md"

# =============================================================================
# 22 Status reports / generated reports / cleanup FINISH
# =============================================================================


# =============================================================================
# 23 Completion packet / prompt finalization START
# =============================================================================

# Purpose: Validate packet schema and required fields.
# Safety: Read-only.
# Inputs: PACKET and COMPLETION_PACKET_VALIDATE_SCRIPT.
# Result: Packet schema is valid.
.PHONY: completion-packet-validate
completion-packet-validate:
	$(call require_packet)
	$(call require_module_script,$(COMPLETION_PACKET_VALIDATE_SCRIPT))
	"$(PYTHON)" "$(COMPLETION_PACKET_VALIDATE_SCRIPT)" "$(PACKET)"

# Purpose: Verify packet evidence, lineage, boundaries, and consistency.
# Safety: Read-only; apply invocation is forbidden.
# Inputs: PACKET and COMPLETION_PACKET_CHECK_SCRIPT.
# Result: Evidence check passes.
.PHONY: completion-packet-check
completion-packet-check:
	$(call require_packet)
	$(MAKE) completion-packet-validate PACKET="$(PACKET)"
	$(call require_module_script,$(COMPLETION_PACKET_CHECK_SCRIPT))
	"$(PYTHON)" "$(COMPLETION_PACKET_CHECK_SCRIPT)" "$(PACKET)"

# Purpose: Preview module-local changes produced by packet apply.
# Safety: Read-only; no module files are modified.
# Inputs: PACKET and COMPLETION_PACKET_PREVIEW_SCRIPT.
# Result: Deterministic change plan is printed.
.PHONY: completion-packet-preview
completion-packet-preview:
	$(call require_packet)
	$(call require_module_script,$(COMPLETION_PACKET_PREVIEW_SCRIPT))
	"$(PYTHON)" "$(COMPLETION_PACKET_PREVIEW_SCRIPT)" "$(PACKET)"

# Purpose: Apply the packet twice in an isolated sandbox and compare results.
# Safety: Read-only for the live worktree; writes are restricted to TMP_DIR sandbox.
# Inputs: PACKET and COMPLETION_PACKET_IDEMPOTENCY_SCRIPT.
# Result: Sandbox idempotency check passes.
.PHONY: completion-packet-idempotency-check
completion-packet-idempotency-check:
	$(call require_packet)
	$(call require_module_script,$(COMPLETION_PACKET_IDEMPOTENCY_SCRIPT))
	@mkdir -p "$(TMP_DIR)"
	"$(PYTHON)" "$(COMPLETION_PACKET_IDEMPOTENCY_SCRIPT)" "$(PACKET)" --module-root "$(MODULE_ROOT)" --sandbox-root "$(TMP_DIR)/completion_packet_idempotency"

# Purpose: Apply packet updates to module-local coordination records.
# Safety: Mutates only current module files; no commit, push, merge, or Blueprint writes.
# Inputs: PACKET and COMPLETION_PACKET_APPLY_SCRIPT.
# Result: Module-local completion records are updated idempotently.
.PHONY: completion-packet-apply
completion-packet-apply:
	$(call require_packet)
	$(call require_module_script,$(COMPLETION_PACKET_APPLY_SCRIPT))
	"$(PYTHON)" "$(COMPLETION_PACKET_APPLY_SCRIPT)" "$(PACKET)"

# =============================================================================
# 23 Completion packet / prompt finalization FINISH
# =============================================================================


# =============================================================================
# 24 Git / release / commit helpers START
# =============================================================================

# Purpose: Show current branch, HEAD, and changed files.
# Safety: Read-only Git queries.
# Inputs: Git worktree.
# Result: Git state is printed.
.PHONY: git-status
git-status:
	@$(GIT) branch --show-current
	@$(GIT) log -1 --oneline
	@$(GIT) status --short

# Purpose: Run read-only validation and diff checks before a manual commit.
# Safety: Read-only; does not stage or commit.
# Inputs: Valid module worktree.
# Result: Validation and diff checks pass.
.PHONY: pre-commit
pre-commit:
	$(MAKE) module-validate
	@$(GIT) diff --check
	@$(GIT) status --short

# Purpose: Run module-specific release readiness checks.
# Safety: Read-only; fails closed until implemented.
# Inputs: Module-specific implementation.
# Result: Fails until implemented.
.PHONY: release-check
release-check:
	$(call not_implemented)

# =============================================================================
# 24 Git / release / commit helpers FINISH
# =============================================================================


# =============================================================================
# 25 Optional module workflow / self-knowledge START
# =============================================================================

# Purpose: Run module-owned workflow command: list.
# Safety: Module-owned executable only; mutability is defined by the subcommand contract.
# Inputs: MODULE_WORKFLOW_CLI.
# Result: list completes.
.PHONY: module-workflow-list
module-workflow-list:
	$(call require_module_script,$(MODULE_WORKFLOW_CLI))
	"$(PYTHON)" "$(MODULE_WORKFLOW_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" list

# Purpose: Run module-owned workflow command: check.
# Safety: Module-owned executable only; mutability is defined by the subcommand contract.
# Inputs: MODULE_WORKFLOW_CLI.
# Result: check completes.
.PHONY: module-workflow-check
module-workflow-check:
	$(call require_module_script,$(MODULE_WORKFLOW_CLI))
	"$(PYTHON)" "$(MODULE_WORKFLOW_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" check

# Purpose: Run module-owned workflow command: self-audit.
# Safety: Module-owned executable only; mutability is defined by the subcommand contract.
# Inputs: MODULE_WORKFLOW_CLI.
# Result: self-audit completes.
.PHONY: module-self-audit
module-self-audit:
	$(call require_module_script,$(MODULE_WORKFLOW_CLI))
	"$(PYTHON)" "$(MODULE_WORKFLOW_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" self-audit

# Purpose: Run module-owned workflow command: self-audit-resume.
# Safety: Module-owned executable only; mutability is defined by the subcommand contract.
# Inputs: MODULE_WORKFLOW_CLI.
# Result: self-audit-resume completes.
.PHONY: module-self-audit-resume
module-self-audit-resume:
	$(call require_module_script,$(MODULE_WORKFLOW_CLI))
	"$(PYTHON)" "$(MODULE_WORKFLOW_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" self-audit-resume

# Purpose: Run module-owned workflow command: self-status.
# Safety: Module-owned executable only; mutability is defined by the subcommand contract.
# Inputs: MODULE_WORKFLOW_CLI.
# Result: self-status completes.
.PHONY: module-self-status
module-self-status:
	$(call require_module_script,$(MODULE_WORKFLOW_CLI))
	"$(PYTHON)" "$(MODULE_WORKFLOW_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" self-status

# Purpose: Run module-owned workflow command: self-report-full.
# Safety: Module-owned executable only; mutability is defined by the subcommand contract.
# Inputs: MODULE_WORKFLOW_CLI.
# Result: self-report-full completes.
.PHONY: module-self-report-full
module-self-report-full:
	$(call require_module_script,$(MODULE_WORKFLOW_CLI))
	"$(PYTHON)" "$(MODULE_WORKFLOW_CLI)" --module-root "$(MODULE_ROOT)" --module "$(MODULE_ID)" self-report-full

# =============================================================================
# 25 Optional module workflow / self-knowledge FINISH
# =============================================================================


# =============================================================================
# 90 Module-specific helpers START
# =============================================================================

# Add module-specific targets below this line.
# Every target must document Purpose, Safety, Inputs, and Result.

# =============================================================================
# 90 Module-specific helpers FINISH
# =============================================================================
