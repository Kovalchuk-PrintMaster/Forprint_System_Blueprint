# Calculator Engine Directive: Coordination Pull and Calculator Focus v1

## Directive ID

```text
2026-06-02__calculator_engine__directive__coordination-pull-and-calculator-focus-v1
```

## Target module

```text
calculator_engine
```

## Status

```text
active
```

## Source

```text
forprint_system_blueprint
```

## Purpose

Calculator Engine is the first test module for the new ForPrint coordination loop.

This directive has two goals:

```text
1. Apply the ForPrint Module Coordination Standard.
2. Continue Calculator development in the correct strategic direction.
```

## Required self-check behavior

Calculator Engine must not wait for the owner to manually announce every new Blueprint instruction.

After pulling ForPrint System Blueprint updates, the module assistant should check:

```text
coordination/directives/global/index.yaml
coordination/directives/modules/calculator_engine/index.yaml
```

If new active directives are found, the module assistant should:

```text
1. Read the referenced directive files.
2. Compare them with local module status.
3. Apply allowed coordination updates.
4. Record acknowledgement or questions in the module coordination files.
5. Reference directive_id in reports when the work responds to a directive.
```

In the first stage this process is manual, but the file structure must support future automation.

## Required coordination action

Apply the standard prompt from Blueprint:

```text
coordination/templates/module_coordination_prompt.md
```

The Calculator repository should maintain:

```text
coordination/status/current_status.yaml
coordination/status/current_status.md
coordination/status/next_questions_for_blueprint.md
coordination/prompts/index.yaml
coordination/reports/index.yaml
coordination/reports/completion/
coordination/reports/commits/
coordination/prompts/received/
```

The module should update these files after meaningful milestones and commits.

## Strategic Calculator direction

Calculator Engine is the primary formalization point for new order/calculation requests.

Calculator should move toward:

```text
CalculationOutputPackage
Quote / CommercialOffer
OrderDraft / OrderCreationDraft
price_breakdown
material_consumption_estimate
production_method_plan
operation_sequence
accounting line drafts
prepress requirements
validation warnings
manual/custom operation drafts
```

## Local catalog policy

Calculator may use local temporary catalog/projection data to harden calculation logic.

But Calculator must not become the canonical catalog owner.

Canonical product/service/material/operation definitions belong to ForPrint Library.

Calculator-local catalog structures are:

```text
projection
cache
fixture
sandbox data
development helper
```

not canonical truth.

## Boundaries

Calculator must not own:

```text
canonical client registry
canonical order registry
canonical product/material catalog
accounting truth
1C synchronization
warehouse stock truth
prepress lifecycle
runtime gateway routing
CRM workflow ownership
```

## Priority

```text
p0
```

## Expected report

After applying this directive, Calculator should provide a completion report with:

```text
report_id
responds_to_directive_id
module_id
files added/changed
coordination files status
check results
current Calculator phase
next recommended Calculator macro pack
open questions for Blueprint
commit hash
push status
```

Recommended report ID:

```text
2026-06-02__calculator_engine__report__coordination-pull-and-calculator-focus
```

## Expected next macro pack

After coordination is in place, the next strategic Calculator pack should be:

```text
Calculator Engine — CalculationOutputPackage / Quote / OrderDraft Foundation
```

It should remain internal/sandbox-safe and must not create real production integrations.
