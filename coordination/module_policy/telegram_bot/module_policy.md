# Module Policy — Telegram Bot

## Module ID

```text
telegram_bot
```

## Priority

```text
p0
```

## Development status

```text
active_development
```

## Strategic role

Current main customer channel adapter for Telegram communication.

## Main goals

- `Collect customer request information.`
- `Keep channel-specific UI separate from business logic.`
- `Hand off structured request/calculation context to Calculator.`
- `Avoid becoming CRM or internal DB owner.`

## Owns

- `telegram_channel_adapter`
- `telegram_dialog_flow`
- `telegram_message_ui`
- `telegram_user_interaction_shell`

## Must not own

- `canonical_client_registry`
- `canonical_order_registry`
- `calculator_logic`
- `accounting_truth`
- `operational_db`
- `catalog_truth`

## Next focus

- `Keep order-intake/customer-request flow moving.`
- `Prepare channel-agnostic request handoff to Calculator.`
- `Plan gradual move away from Supabase toward internal DB/Operational Registry.`

## Adoption rule

This module policy is strategic guidance. It does not automatically authorize large refactors or broad rewrites. The module should compare this policy with its current implementation and report alignment, conflicts or questions to Blueprint.
