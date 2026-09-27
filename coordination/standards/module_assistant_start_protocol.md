# Module Assistant Start Protocol

## Status

Active Blueprint standard / gradual adoption

## Purpose

Every module assistant must start work by refreshing its understanding of the current ForPrint architecture and module-specific instructions.

A ForPrint module is not a standalone application.

A module is a node in the ForPrint ecosystem and must respect global architecture, module ownership and active Blueprint guidance.

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
13. Blueprint standards visibility.
14. Relevant architecture standards packages.

## Global ForPrint architecture context

At startup, a module assistant should remember:

```text
ForPrint System Blueprint owns architecture and standards.
ForPrint Library owns semantic and catalog meaning.
Calculator Engine owns calculation outputs and drafts.
ForPrint Operations Control Registry owns operational truth.
ForPrint Accounting Registry Service owns accounting and 1C staging truth.
ForPrint Integration Gateway owns transport and handoff reliability.
CRM owns human-facing workflow views and coordination UI.
Channel modules own channel shells, not canonical business truth.
```

A module must not silently take ownership of another module's canonical data.

Required standards awareness

At startup, mature module assistants should be able to see:

coordination/standards/index.yaml
coordination/standards/README.md
coordination/standards/module_standards_awareness_protocol.md
coordination/standards/modular_topology_and_resilience/
coordination/standards/third_party_reuse/

The following packages are especially important for modules that touch runtime integration, data ownership, external tools, Gateway, databases, reporting, queues or cross-module handoff:

coordination/standards/modular_topology_and_resilience/
coordination/standards/third_party_reuse/
Primary current startup command

```text
make module-start
```

`module-start` is the canonical prompt-driven entrypoint. It performs the
freshness-gated startup workflow and must not mutate the Blueprint repository.

Compatibility/read-only component checks may still include:

```text
make governance-check
make blueprint-check
make module-policy-check
make coordination-check
make status-report
```

Older startup sequences are compatibility guidance only. They must not be
interpreted as requiring module-side Blueprint mutation.

If the module has make-first standards support, it should also support or gradually add:

make blueprint-standards-list
make blueprint-standards-check
make blueprint-standards-sync
Required behavior

If the module cannot perform one of these checks yet, it must clearly print:

DEFERRED

or:

MISSING_NEEDS_ALIGNMENT

It must not silently skip the check.

Prompt-driven work startup

If the module receives work through Blueprint outgoing prompts, the assistant must run:

make governance-check
make blueprint-prompts-list
make blueprint-prompt
git status --short

The assistant should then execute only the active prompt intended for its own module.

Long implementation prompts should not be manually copied into module chats when a Blueprint outgoing prompt is available.

Third-party tools at startup

If the task involves a new database, message broker, BI tool, auth provider, ERP/PIM/CRM integration, automation platform or external service, the assistant must classify it using:

coordination/standards/third_party_reuse/third_party_reuse_policy.md

A module assistant must not introduce a production third-party dependency as a hidden architecture decision.

Non-goals

The start protocol must not:

commit changes;
push changes;
run destructive migrations;
start production integrations;
overwrite module-specific coordination blocks;
silently redesign global architecture;
introduce third-party core dependencies without Blueprint approval.


## Current startup command

For prompt-driven work, use `make module-start`.

Do not run module-side `blueprint-pull`.

`module-start` freshness-checks Blueprint, synchronizes module-local snapshots,
renders status and prompt notification, and reads the next ready prompt.
Local validation remains network-independent.
