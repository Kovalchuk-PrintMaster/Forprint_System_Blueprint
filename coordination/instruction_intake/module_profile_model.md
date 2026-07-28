# Module Profile Model

Status: active model v0.1

ForPrint modules should not be classified using one rigid type.

A module profile is a small set of composable traits.

## Core dimensions

- maturity
- business_criticality
- complexity
- automation_level
- standards_strictness
- prompt_priority
- cleanup_priority
- feedback_required

## Example: core active module

```yaml
module_id: forprint_operational_registry
profile:
  maturity: active_development
  business_criticality: core
  complexity: high
  automation_level: medium
  standards_strictness: growing
  prompt_priority: high
  cleanup_priority: medium
  feedback_required: true
```

## Example: lightweight helper

```yaml
module_id: product_research_helper
profile:
  maturity: helper
  business_criticality: low
  complexity: low
  automation_level: light
  standards_strictness: advisory_only
  prompt_priority: high
  cleanup_priority: low
  feedback_required: false
```

## Rule

Profiles guide task packaging and priority.

Profiles do not override global policy, active directives or module ownership boundaries.
