# ForPrint Visual Status Tokens Policy

## Status

Target standard / gradual adoption v0.1

## Purpose

This document defines shared visual status tokens for ForPrint command-line dashboards, generated reports and future lightweight operator interfaces.

The goal is to keep prompt queues, coordination awareness dashboards, roadmap dashboards, check reports and future UI outputs visually consistent.

A module should not invent unrelated colors for the same semantic status.

## Scope

This policy applies to:

- terminal dashboards;
- generated Markdown reports;
- generated JSON/YAML metadata where visual hints are useful;
- future simple web or local operator interfaces;
- module roadmap dashboards;
- prompt queue dashboards;
- coordination document awareness dashboards.

This policy does not require every module to implement colors immediately.

Color must be cosmetic only.

All dashboards must remain readable when `NO_COLOR=1` is used.

## Core rule

Visual styling must be driven by semantic tokens, not by ad-hoc hardcoded colors.

Allowed:

```text
status_token: success
status_token: warning
status_token: critical
status_token: in_progress
```

Avoid:

hardcoded_red_for_this_table_only
special_green_for_prompt_queue_only
Token categories

ForPrint visual tokens are grouped by purpose.

Recommended categories:

status
priority
review_state
execution_state
freshness
dependency_state
risk

A dashboard may use only the categories it needs.

Status tokens

Recommended status tokens:

success
ok
info
planned
new
changed
in_progress
warning
critical
blocked
failed
deferred
not_applicable
unknown

Recommended terminal meanings:

success        completed, accepted, applied
ok             no action needed
info           informational
planned        known but not started
new            newly discovered item
changed        existing item changed since last review
in_progress    active work or active review
warning        needs attention, not blocking yet
critical       high urgency or must review before work
blocked        cannot proceed until resolved
failed         validation failed
deferred       intentionally delayed
not_applicable not relevant for this module/context
unknown        missing or unresolved state
Priority tokens

Recommended priority tokens:

critical
high
normal
low
reference

Recommended meanings:

critical  must be reviewed or handled before relevant work continues
high      should be reviewed before the next substantial step
normal    should be handled during normal development flow
low       cleanup or gradual alignment
reference read only when relevant
Review state tokens

Recommended review state tokens:

unseen
acknowledged
in_progress
applied
accepted
deferred
not_applicable
superseded
returned_for_fix

Recommended meanings:

unseen           module has not reviewed this item/hash yet
acknowledged     module has read and accepted awareness of the item
in_progress      module is actively aligning to the item
applied          module has implemented the required change
accepted         Blueprint or reviewer accepted the result
deferred         intentionally delayed with reason
not_applicable   not relevant for the module
superseded       replaced by a newer item
returned_for_fix review found issues that need correction
Execution state tokens

Recommended execution state tokens:

ready
not_started
active
completed
paused
blocked
cancelled

Recommended meanings:

ready        ready to be picked up
not_started  known but not started
active       currently being worked on
completed    completed by module
paused       intentionally paused
blocked      cannot proceed
cancelled    no longer planned
Freshness tokens

Recommended freshness tokens:

current
new
changed
stale
missing
unknown

Recommended meanings:

current  local ledger/hash matches current source
new      source exists but local ledger does not know it
changed  source hash differs from local ledger
stale    local record exists but source was superseded
missing  referenced source is missing
unknown  freshness could not be determined
Terminal color guidance

Recommended terminal color mapping:

success / ok / applied / accepted     green
info / reference                      cyan
planned / not_started                 gray or default
new / changed                         yellow
in_progress / active                  blue
warning / deferred                    yellow
critical / blocked / failed           red
not_applicable / superseded           gray
unknown                               magenta or default warning color

Exact ANSI color codes may differ by implementation.

The semantic token is more important than the raw color.

Markdown report guidance

Markdown reports should include semantic status text even when colors are unavailable.

Allowed:

Status: critical
Priority: high
Review state: unseen

Avoid relying only on visual color without text.

Future UI guidance

Future HTML/CSS interfaces should map these same semantic tokens to CSS classes.

Recommended CSS class pattern:

fp-token-success
fp-token-warning
fp-token-critical
fp-priority-high
fp-review-unseen
fp-execution-active

This document defines the semantic tokens.

Concrete CSS implementation may be defined later in a separate interface stylesheet policy.

Template source

The machine-readable starter template is:

coordination/templates/visual_status_tokens_v0_1.template.yaml

Modules may copy or reference this template when implementing dashboards.

Compatibility rule

Existing dashboards may keep their current colors during gradual adoption.

New dashboards should use these tokens from the start.

When an existing dashboard is refactored, it should move from ad-hoc colors to semantic tokens.
