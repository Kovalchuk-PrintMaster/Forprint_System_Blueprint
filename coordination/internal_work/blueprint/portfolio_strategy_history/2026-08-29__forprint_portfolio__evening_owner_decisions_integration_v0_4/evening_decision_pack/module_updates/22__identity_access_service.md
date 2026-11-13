# ForPrint Identity & Access Service — clarification

This is the centralized auth module discussed during Website review.

Purpose:
- authentication;
- authorization;
- accounts;
- password/hash/credential handling;
- sessions/tokens;
- MFA/WebAuthn where appropriate;
- roles/permissions;
- shared identity across Website, Mobile App, Calculator, Operations Assistant and future clients.

Why it exists:
avoid duplicated credentials, inconsistent permissions and separate account lifecycle logic in each interface.

Boundary:
Identity proves who the user is and what they may access.
It is not CRM, order history, accounting or business-profile storage.

Expanded review:
provider/self-host options, customer vs employee security, client IDs, cross-client authorization, recovery, audit trail and deny-by-default behavior.
