# Identity / Counterparty / CRM security boundary v0.1

Status: `AGREED_WITH_OWNER + PROVISIONAL_BOUNDARY`

- Identity & Access owns identity proof, factors, sessions and access decisions.
- CRM owns business relationship/profile views, roles in the commercial relationship and relationship analytics.
- Accounting owns financial truth.
- Telegram/Website/Mobile are channels, not identity truth owners.
- Phone is a strong current lookup/business identifier, not the future immutable DB primary key.
- Multiple contacts may represent one client.
- One contact appearing under multiple different Client IDs is a security exception, not an automatic merge.
- Cross-Client-ID reads/writes are deny-by-default until explicitly approved and scoped.
