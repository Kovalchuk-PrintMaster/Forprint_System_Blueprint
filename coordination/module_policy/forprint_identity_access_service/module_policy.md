# Module Policy — ForPrint Identity & Access Service

## Module ID

```text
forprint_identity_access_service
```

## Priority

```text
p1
```

## Development status

```text
confirmed_planned_not_active
```

## Strategic role

Shared cross-project identity, authentication, authorization, session and access-policy service.

## Main goals

- `Provide one registration/authentication/session foundation.`
- `Support role defaults plus per-user permission overrides.`
- `Support recovery, future MFA/passkeys and security audit.`
- `Provide one shared identity/authentication/authorization foundation across ForPrint web, internal and future mobile surfaces.`
- `Support role defaults plus explicit per-user permission additions or restrictions.`
- `Keep cross-client/cross-organization access deny-by-default unless explicitly scoped.`
- `Support session/recovery/security-audit foundations and later MFA/passkeys/SSO adoption.`

## Owns

- `account_identity`
- `authentication_factors`
- `session_and_device_state`
- `role_and_permission_policy`
- `per_user_permission_override`
- `account_recovery`
- `access_decision_audit`
- `shared_sso_boundary`
- `security_authentication_audit`

## Must not own

- `crm_relationship_truth`
- `accounting_truth`
- `operational_order_truth`
- `external_provider_credentials`
- `canonical_business_partner_relationship_truth`
- `business_domain_authority`

## Next focus

- `Build full charter/capability/dependency roadmap before implementation.`
- `Remain NOT ACTIVE until portfolio readiness gate is cleared.`
- `Define stable Account/Person linkage without using phone/email/Telegram as immutable primary keys.`
- `Define customer/staff realms, least-privilege policy and admin access-control surface.`
- `Keep implementation NOT ACTIVE until the portfolio readiness gate is cleared.`

## Adoption rule

This module policy is strategic guidance. It does not automatically authorize large refactors or broad rewrites. The module should compare this policy with its current implementation and report alignment, conflicts or questions to Blueprint.
