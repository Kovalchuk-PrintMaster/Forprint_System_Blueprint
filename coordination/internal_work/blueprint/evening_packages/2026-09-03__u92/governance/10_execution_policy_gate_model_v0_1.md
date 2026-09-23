# Execution Policy Gate Model v0.1

Status: PROPOSED

## Principle

AI intent/output is not authorization.

Before a significant side effect:

`AI/Module → structured tool request → Execution Policy Gate → IAM/resource policy → tool/service`

## Preferred tool shape

Prefer narrow capability tools:
- `print_document(document_id, printer_id)`
- `install_approved_package(package_id, target_id)`
- `restart_allowed_service(service_id)`
- `restore_workspace(profile_id, target_id)`

over:
- `run_shell(arbitrary_string)`

Arbitrary shell may remain in Development Plane where bounded by development permissions.

## Decision inputs

A policy decision may include:
- requester/service identity;
- user identity and selected business context;
- module;
- environment;
- requested capability;
- resource;
- action class;
- side-effect class;
- data sensitivity;
- approval state;
- correlation/root request IDs;
- current system health;
- change/release identity.

## Decision outcomes

- ALLOW
- DENY
- REQUIRE_OPERATOR_APPROVAL
- REQUIRE_OWNER_APPROVAL
- REQUIRE_MAINTENANCE_WINDOW
- ALLOW_TEST_ONLY

## Human approval packet

For high-impact action, operator receives:
- requested outcome;
- why it is requested;
- affected resources;
- data/external effects;
- risk class;
- rollback/recovery evidence;
- requesting module;
- artifact/release version;
- approve/reject.

Do not send raw shell commands without a human-readable explanation.

## Environment policy

DEVELOPMENT:
- broad module-local engineering actions allowed.

TEST:
- broad synthetic/adversarial actions allowed;
- live side effects denied by default.

PRODUCTION:
- least privilege;
- capability-shaped tools;
- destructive/high-impact actions governed.

## Implementation path

First revision may be simple YAML rules + deterministic Python policy evaluator.
A future mature policy engine may be adopted if complexity warrants it.
