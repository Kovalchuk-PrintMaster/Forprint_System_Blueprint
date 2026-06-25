# Module Global Context Policy

## Purpose

This policy defines what every ForPrint module should understand about the global system before making local implementation decisions.

A module is not a standalone application.

A module is a node in the ForPrint operational platform.

## Required global context

Each module should know:

```text
its owner responsibility;
what it must not own;
its upstream modules;
its downstream modules;
the commands it may emit;
 the commands it may accept;
the events it may emit;
the events it may consume;
the foreign references it may store;
its degraded mode behavior;
its reporting or status obligations.
```

## Module-local documentation

Mature modules should include local documentation that answers:

```text
Where does this module sit in the ForPrint ecosystem?
Which module owns the data this module reads?
Which module receives this module's output?
What happens when a dependency is unavailable?
What handoffs must be durable?
What should be reported to Blueprint?
```

## Prompt requirement

Blueprint outgoing prompts for mature modules should include a `Global ForPrint architecture context` section.

This section should remind the assistant that:

```text
the module is part of a larger ecosystem;
ownership boundaries must be respected;
foreign truth must not be silently copied or mutated;
cross-module handoffs must be durable when they affect business flow;
Gateway should be used for runtime integration when approved;
local drafts are not canonical truth;
degraded mode must be visible.
```

## Example module context

Calculator Engine should understand:

```text
Library provides semantic and catalog references.
Calculator produces calculation packages, quote drafts and order drafts.
Operational Registry owns canonical operational orders.
Accounting Registry owns invoices and payment truth.
Gateway will later route runtime handoffs.
CRM will show operator views and decisions.
```

Operational Registry should understand:

```text
it owns operational truth;
it may receive order creation commands;
it does not own accounting truth;
it should store payment references, not payment truth;
it should expose read models or projections for CRM and reporting.
```

Library should understand:

```text
it owns semantic and catalog meaning;
it does not own pricing, stock, orders or accounting;
it should provide stable references and alias rules;
downstream modules may use snapshots when Library is unavailable.
```

Telegram Bot should understand:

```text
it owns channel interaction shell and dialog state;
it does not own canonical clients or orders;
it should hand off request context through approved contracts;
it must not become CRM or Operational Registry.
```

## Degraded mode awareness

Modules should not assume all other modules are always available.

Module-local logic should be able to represent:

```text
dependency unavailable;
using snapshot;
pending handoff;
manual review required;
retry scheduled;
operation cannot complete until owner module is available.
```

## Reporting to Blueprint

When a module discovers that its local implementation conflicts with global architecture, it should report the conflict through coordination records or completion reports.

A module should not silently redesign global architecture from inside local code.

## Boundary

This policy defines context expectations for modules and prompts.

Detailed topology is defined in `architecture_topology_policy.md`.

Detailed storage ownership is defined in `data_ownership_and_storage_policy.md`.

Detailed handoff behavior is defined in `module_interaction_reliability_policy.md`.
