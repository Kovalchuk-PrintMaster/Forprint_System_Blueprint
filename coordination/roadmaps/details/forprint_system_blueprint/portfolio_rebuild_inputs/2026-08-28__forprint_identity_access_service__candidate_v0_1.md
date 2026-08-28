# ForPrint Identity & Access Service — candidate v0.1

Provisional id: `forprint_identity_access_service`

Status: `AGREED_WITH_OWNER_DIRECTION / NEW_MODULE_CANDIDATE / NOT_ACTIVE`

## Purpose
Provide one cross-project identity/authentication/authorization capability for Website, Mobile App,
CRM, Operations Assistant, Telegram-related account flows and internal staff tools.

Do not rebuild login, recovery, MFA, sessions and access policy separately in every interface.

## Terminology
Canonical documentation should distinguish:
- identity = who the subject is;
- authentication = how identity is proven;
- authorization = what the subject may read/do.

## Current business identification convention
A simple individual customer is commonly identified by the primary phone number and a display name
similar to `TelegramName_<phone>`. Preserve this as migration/alias evidence. Do not use phone as the
future immutable database primary key.

## Candidate model
- stable internal Person/Account ID;
- verified contact points: phone, Telegram, email and future channels;
- sessions/tokens/devices;
- recovery;
- MFA/passkeys where justified;
- roles/permissions;
- customer and staff policy profiles;
- access-change audit.

## Person / Counterparty structure
An organization can have many contact persons. Contacts may have roles such as primary contact,
ordering, accounting or delivery.

Official organization name and EDRPOU are strong lookup/disambiguation fields, but the internal
record should still have a stable ID.

## HIGH-RISK cross-account rule — AGREED_WITH_OWNER
If one person/contact appears under two or more **different Client/Counterparty IDs**, do not infer
cross-account access.

Default:
`cross_client_data_access = DENY`

Any exception needs explicit approval and scoped permissions:
- client ID;
- role;
- read/write;
- data classes (orders, finance, chat history, contact/personal data, etc.);
- audit evidence.

One person representing several organizations must never automatically mean access to everything in all of them.

## Open questions
- final module name;
- customer vs employee realms;
- exact recovery policy;
- verification strength by channel;
- delegation/legal representative model;
- least-privilege inside one Client ID;
- privacy/retention;
- CRM linkage without credential ownership.
