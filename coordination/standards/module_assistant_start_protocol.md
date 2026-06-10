# Module Assistant Start Protocol

## Status

Active Blueprint standard / gradual adoption

## Purpose

Every module assistant must start work by refreshing its understanding of the current ForPrint architecture and module-specific instructions.

## Required start checklist

Before changing code, the assistant must check:

1. Git branch.
2. Git working tree status.
3. Blueprint repository freshness.
4. Global Blueprint policy.
5. Module policy.
6. Active global directives.
7. Active module directives.
8. Coordination status.
9. Prompts index.
10. Reports index.
11. Next questions for Blueprint.
12. Latest check-report.

## Preferred command

```bash
make governance-check
Fallback command sequence
make blueprint-pull
make blueprint-check
make blueprint-sync-directives
make module-policy-check
make coordination-check
make status-report
Required behavior

If the module cannot perform one of these checks yet, it must clearly print:

DEFERRED

or:

MISSING_NEEDS_ALIGNMENT

It must not silently skip the check.

Non-goals

The start protocol must not:

commit changes;
push changes;
run destructive migrations;
start production integrations;
overwrite module-specific coordination blocks.

---

## Prompt-driven work startup

If the module receives work through Blueprint outgoing prompts, the assistant must run:

```bash
make governance-check
make blueprint-prompts-list
make blueprint-prompt
git status --short

The assistant should then execute only the active prompt intended for its own module.

Long implementation prompts should not be manually copied into module chats when a Blueprint outgoing prompt is available.

